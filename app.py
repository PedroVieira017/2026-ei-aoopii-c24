import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from validation import build_validation_checks, newsletter_needs_repair


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
if "results" not in st.session_state:
    st.session_state.results = {}
if "facts" not in st.session_state:
    st.session_state.facts = ""
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "source_description" not in st.session_state:
    st.session_state.source_description = ""


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


def transcribe_audio(client: OpenAI, uploaded_file) -> str:
    transcription = client.audio.transcriptions.create(
        file=(uploaded_file.name, uploaded_file.getvalue()),
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


def build_markdown_export() -> str:
    results = st.session_state.results
    sections = [
        "# Content Pipeline Agent - outputs",
        "",
        f"Fonte: {st.session_state.source_description or 'nao indicada'}",
        "",
        "## Texto fonte",
        "",
        st.session_state.source_text or "",
        "",
        "## Factos extraidos",
        "",
        st.session_state.facts or "",
        "",
    ]

    output_titles = {
        "blog": "Blog Post",
        "linkedin": "LinkedIn Post",
        "tweet_thread": "Tweet Thread",
        "newsletter": "Newsletter Section",
    }

    for key, title in output_titles.items():
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


def render_validation(format_key: str, text: str) -> None:
    validation = build_validation_checks(format_key, text)

    with st.expander("Validacao rapida", expanded=True):
        word_col, sentence_col, paragraph_col = st.columns(3)
        word_col.metric("Palavras", validation["word_count"])
        sentence_col.metric("Frases", validation["sentence_count"])
        paragraph_col.metric("Paragrafos", validation["paragraph_count"])

        for check in validation["checks"]:
            if check["ok"]:
                st.success(check["message"])
            else:
                st.warning(check["message"])


st.set_page_config(page_title="Content Pipeline Agent", layout="wide")

st.title("Content Pipeline Agent")
st.write("Prototipo do trabalho pratico")
st.caption("Um input unico gera multiplos formatos adaptados a diferentes plataformas.")

st.subheader("Fonte de conteudo")
input_mode = st.radio(
    "Modo de entrada",
    [
        "Escrever manualmente",
        "Escolher exemplo",
        "Carregar ficheiro de texto",
        "Carregar audio",
    ],
    horizontal=True,
)

texto = ""
source_description = ""
uploaded_audio = None

if input_mode == "Escrever manualmente":
    texto = st.text_area("Fonte de conteudo", height=250, key="manual_source")
    source_description = "texto escrito manualmente"
elif input_mode == "Escolher exemplo":
    example_files = get_example_files()

    if not example_files:
        st.warning("Nao foram encontrados exemplos em data/*.txt.")
    else:
        selected_example = st.selectbox(
            "Exemplo disponivel",
            example_files,
            format_func=format_example_name,
        )
        texto = selected_example.read_text(encoding="utf-8")
        source_description = f"exemplo: {selected_example.name}"
        texto = st.text_area(
            "Fonte de conteudo",
            value=texto,
            height=250,
            key=f"example_source_{selected_example.name}",
        )
elif input_mode == "Carregar ficheiro de texto":
    uploaded_file = st.file_uploader(
        "Carregar fonte de conteudo",
        type=["txt", "md"],
        help="Carrega uma entrevista, artigo, nota de investigacao ou transcricao em texto.",
    )

    if uploaded_file is None:
        st.info("Carrega um ficheiro .txt ou .md para gerar os conteudos.")
    else:
        texto = decode_text_file(uploaded_file.getvalue())
        source_description = f"ficheiro: {uploaded_file.name}"
        texto = st.text_area(
            "Fonte de conteudo",
            value=texto,
            height=250,
            key=f"uploaded_source_{uploaded_file.name}",
        )
elif input_mode == "Carregar audio":
    uploaded_audio = st.file_uploader(
        "Carregar voice memo",
        type=AUDIO_FILE_TYPES,
        help="Carrega um ficheiro de audio para transcricao antes da pipeline.",
    )

    if uploaded_audio is None:
        st.info("Carrega um ficheiro de audio para transcrever e gerar os conteudos.")
    else:
        source_description = f"audio: {uploaded_audio.name}"
        st.caption("O audio sera transcrito quando carregares em Gerar conteudos.")

if st.button("Gerar conteudos"):
    if not texto.strip() and uploaded_audio is None:
        st.warning("Insere texto ou carrega uma fonte primeiro.")
    else:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            st.error("A variavel GROQ_API_KEY nao foi encontrada no ficheiro .env.")
        else:
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.groq.com/openai/v1",
                )

                with st.spinner("A gerar conteudos..."):
                    if uploaded_audio is not None:
                        texto = transcribe_audio(client, uploaded_audio)
                        if not texto.strip():
                            raise ValueError("A transcricao do audio ficou vazia.")

                    st.session_state.source_text = texto
                    st.session_state.source_description = source_description
                    st.session_state.facts = extract_facts(client, texto)
                    st.session_state.results = {
                        "blog": generate_content(
                            client,
                            "blog_post.txt",
                            st.session_state.facts,
                            "blog",
                        ),
                        "linkedin": generate_content(
                            client,
                            "linkedin_post.txt",
                            st.session_state.facts,
                            "linkedin",
                        ),
                        "tweet_thread": generate_content(
                            client,
                            "tweet_thread.txt",
                            st.session_state.facts,
                            "tweet_thread",
                        ),
                        "newsletter": generate_content(
                            client,
                            "newsletter_section.txt",
                            st.session_state.facts,
                            "newsletter",
                        ),
                    }

                st.success("Conteudos gerados com sucesso.")
                if st.session_state.source_description:
                    st.caption(f"Fonte usada: {st.session_state.source_description}.")
                if uploaded_audio is not None:
                    with st.expander("Transcricao usada"):
                        st.text_area(
                            "Texto transcrito",
                            value=st.session_state.source_text,
                            height=180,
                        )

            except Exception as error:
                st.error(f"Ocorreu um erro ao gerar os conteudos: {error}")

st.divider()

blog_tab, linkedin_tab, tweet_thread_tab, newsletter_tab = st.tabs(
    ["Blog Post", "LinkedIn Post", "Tweet Thread", "Newsletter Section"]
)

with blog_tab:
    st.subheader("Blog Post")
    if "blog" in st.session_state.results:
        if st.session_state.facts:
            with st.expander("Factos extraidos"):
                st.code(st.session_state.facts, language="text")
        st.text_area(
            "Resultado",
            value=st.session_state.results["blog"]["text"],
            height=320,
        )
        render_validation("blog", st.session_state.results["blog"]["text"])
        with st.expander("Prompt carregado"):
            st.code(st.session_state.results["blog"]["prompt"], language="text")
    else:
        st.info("O resultado do blog post sera mostrado aqui.")

with linkedin_tab:
    st.subheader("LinkedIn Post")
    if "linkedin" in st.session_state.results:
        st.text_area(
            "Resultado",
            value=st.session_state.results["linkedin"]["text"],
            height=260,
        )
        render_validation("linkedin", st.session_state.results["linkedin"]["text"])
        with st.expander("Prompt carregado"):
            st.code(st.session_state.results["linkedin"]["prompt"], language="text")
    else:
        st.info("O resultado do post de LinkedIn sera mostrado aqui.")

with tweet_thread_tab:
    st.subheader("Tweet Thread")
    if "tweet_thread" in st.session_state.results:
        st.text_area(
            "Resultado",
            value=st.session_state.results["tweet_thread"]["text"],
            height=260,
        )
        render_validation(
            "tweet_thread", st.session_state.results["tweet_thread"]["text"]
        )
        with st.expander("Prompt carregado"):
            st.code(
                st.session_state.results["tweet_thread"]["prompt"], language="text"
            )
    else:
        st.info("O resultado da tweet thread sera mostrado aqui.")

with newsletter_tab:
    st.subheader("Newsletter Section")
    if "newsletter" in st.session_state.results:
        st.text_area(
            "Resultado",
            value=st.session_state.results["newsletter"]["text"],
            height=220,
        )
        render_validation("newsletter", st.session_state.results["newsletter"]["text"])
        with st.expander("Prompt carregado"):
            st.code(st.session_state.results["newsletter"]["prompt"], language="text")
    else:
        st.info("O resultado da newsletter sera mostrado aqui.")

if st.session_state.results:
    st.divider()
    st.subheader("Exportacao")

    if st.session_state.source_text:
        with st.expander("Fonte final usada"):
            st.text_area(
                "Texto fonte",
                value=st.session_state.source_text,
                height=180,
            )

    export_col, clear_col = st.columns([1, 1])
    export_col.download_button(
        "Descarregar outputs em Markdown",
        data=build_markdown_export(),
        file_name="content_pipeline_outputs.md",
        mime="text/markdown",
    )

    if clear_col.button("Limpar resultados"):
        st.session_state.results = {}
        st.session_state.facts = ""
        st.session_state.source_text = ""
        st.session_state.source_description = ""
        st.rerun()
