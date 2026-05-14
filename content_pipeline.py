import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from validation import newsletter_needs_repair


load_dotenv()

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
DATA_DIR = BASE_DIR / "data"

MODEL_NAME = "llama-3.3-70b-versatile"
AUDIO_TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"
MODEL_TEMPERATURE = 0.2
MODEL_MAX_TOKENS = 900

AUDIO_FILE_TYPES = [
    "flac",
    "mp3",
    "mp4",
    "mpeg",
    "mpga",
    "m4a",
    "ogg",
    "wav",
    "webm",
]

OUTPUT_TITLES = {
    "blog": "Blog Post",
    "linkedin": "LinkedIn Post",
    "tweet_thread": "Tweet Thread",
    "newsletter": "Newsletter Section",
}

FORMAT_PROMPTS = {
    "blog": "blog_post.txt",
    "linkedin": "linkedin_post.txt",
    "tweet_thread": "tweet_thread.txt",
    "newsletter": "newsletter_section.txt",
}

NEWSLETTER_REPAIR_INSTRUCTIONS = """
Recebes FACTOS e um RASCUNHO de uma secao de newsletter.

Objetivo:
Reescrever o RASCUNHO para cumprir rigorosamente o formato de newsletter.

Regras obrigatorias:
- Usa apenas informacao presente nos FACTOS.
- Nao tentes incluir todos os FACTOS.
- Mantem apenas a ideia central e os factos essenciais.
- Devolve um titulo curto na primeira linha.
- Depois do titulo, devolve um unico paragrafo.
- O paragrafo deve ter 1 frase; usa 2 frases apenas se for indispensavel.
- O paragrafo deve ter no maximo 60 palavras.
- Nao uses Markdown, asteriscos, negrito, listas ou marcadores.
- Nao acrescentes conclusoes, garantias, motivacoes ou interpretacoes.

Output:
Devolve apenas a newsletter final.
""".strip()

STRICT_FACTUAL_REPAIR_INSTRUCTIONS = """
Recebes FORMATO, FACTOS e TEXTO.

Objetivo:
Reescrever o TEXTO final para que cada frase fique diretamente suportada pelos FACTOS.

Regras obrigatorias:
- Os FACTOS sao a fonte completa. Nao uses conhecimento geral, contexto provavel ou inferencias.
- Remove qualquer frase que nao possa ser ligada diretamente a um ou mais FACTOS.
- Nao acrescentes sentimentos, agradecimentos, motivacoes, objetivos, beneficios, impactos, oportunidades, conclusoes ou planos futuros.
- Nao digas que algo "oferece", "permite", "facilita", "mostra", "sugere", "representa", "pode" ou "tem potencial" se isso nao estiver nos FACTOS.
- Se os FACTOS dizem que alguem "disse que ajudou", mantem essa atribuicao. Nao transformes isso numa afirmacao geral de que algo ajuda.
- Preserva o formato indicado em FORMATO.
- Se FORMATO for blog, devolve um blog post curto, com titulo simples e secoes apenas se houver factos suficientes.
- Se FORMATO for linkedin, devolve 2 a 4 paragrafos curtos, sem titulo.
- Se FORMATO for tweet_thread, devolve 3 a 6 linhas numeradas no formato 1/n, 2/n, etc., cada uma com no maximo 280 caracteres.
- Se FORMATO for newsletter, devolve um titulo curto e um unico paragrafo com no maximo 60 palavras.
- Nao uses Markdown, listas, asteriscos, negrito, hashtags, emojis ou perguntas finais.

Output:
Devolve apenas o texto final corrigido.
""".strip()


def create_client(api_key: str | None = None) -> OpenAI:
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("A variavel GROQ_API_KEY nao foi encontrada no ficheiro .env.")

    return OpenAI(
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
    )


def load_prompt(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {filename}")
    return prompt_path.read_text(encoding="utf-8")


def get_example_files() -> list[Path]:
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.glob("*.txt"))


def format_example_name(example_path: Path) -> str:
    return example_path.stem.replace("_", " ").capitalize()


def decode_text_file(file_content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return file_content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_content.decode("utf-8", errors="replace")


def transcribe_audio_bytes(client: OpenAI, filename: str, file_content: bytes) -> str:
    transcription = client.audio.transcriptions.create(
        file=(filename, file_content),
        model=AUDIO_TRANSCRIPTION_MODEL,
        response_format="text",
        language="pt",
        temperature=0,
    )

    if isinstance(transcription, str):
        return transcription.strip()
    return getattr(transcription, "text", str(transcription)).strip()


def run_generation(client: OpenAI, instructions: str, content: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": content},
        ],
        temperature=MODEL_TEMPERATURE,
        max_completion_tokens=MODEL_MAX_TOKENS,
    )
    return (response.choices[0].message.content or "").strip()


def extract_facts(client: OpenAI, source_text: str) -> str:
    prompt = load_prompt("facts_extraction.txt")
    return run_generation(client, prompt, source_text)


def generate_content(
    client: OpenAI, prompt_filename: str, facts_text: str, format_key: str
) -> dict:
    prompt = load_prompt(prompt_filename)
    draft = run_generation(client, prompt, facts_text)
    review_prompt = load_prompt("compliance_review.txt")
    reviewed_text = run_generation(
        client,
        review_prompt,
        f"FORMATO:\n{format_key}\n\nFACTOS:\n{facts_text}\n\nRASCUNHO:\n{draft}",
    )
    reviewed_text = run_generation(
        client,
        STRICT_FACTUAL_REPAIR_INSTRUCTIONS,
        f"FORMATO:\n{format_key}\n\nFACTOS:\n{facts_text}\n\nTEXTO:\n{reviewed_text}",
    )

    if format_key == "newsletter" and newsletter_needs_repair(reviewed_text):
        reviewed_text = run_generation(
            client,
            NEWSLETTER_REPAIR_INSTRUCTIONS,
            f"FACTOS:\n{facts_text}\n\nRASCUNHO:\n{reviewed_text}",
        )

    return {
        "prompt": prompt,
        "text": reviewed_text,
    }


def run_content_pipeline(client: OpenAI, source_text: str) -> dict:
    facts = extract_facts(client, source_text)
    results = {
        format_key: generate_content(client, prompt_filename, facts, format_key)
        for format_key, prompt_filename in FORMAT_PROMPTS.items()
    }

    return {
        "facts": facts,
        "results": results,
    }


def build_markdown_export(
    source_description: str, source_text: str, facts: str, results: dict
) -> str:
    sections = [
        "# Content Pipeline Agent - outputs",
        "",
        f"Fonte: {source_description or 'nao indicada'}",
        "",
        "## Texto fonte",
        "",
        source_text or "",
        "",
        "## Factos extraidos",
        "",
        facts or "",
        "",
    ]

    for key, title in OUTPUT_TITLES.items():
        if key not in results:
            continue
        sections.extend(
            [
                f"## {title}",
                "",
                results[key]["text"],
                "",
            ]
        )

    return "\n".join(sections).strip() + "\n"
