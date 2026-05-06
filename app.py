import os
import re
from collections import Counter
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
MODEL_NAME = "llama-3.3-70b-versatile"
MODEL_TEMPERATURE = 0.2
MODEL_MAX_TOKENS = 900
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
COMMON_WORDS = {
    "a",
    "o",
    "as",
    "os",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "em",
    "e",
    "ou",
    "que",
    "para",
    "por",
    "com",
    "um",
    "uma",
    "no",
    "na",
    "nos",
    "nas",
}
FORBIDDEN_PT_BR_TERMS = {
    "equipe",
    "esporte",
    "midia",
    "mídia",
    "seção",
    "time",
    "usuario",
    "usuário",
    "voce",
    "você",
}
UNSUPPORTED_CLAIM_TERMS = {
    "assegura",
    "asseguram",
    "assegurar",
    "comprova",
    "comprovam",
    "comprovar",
    "garante",
    "garantem",
    "garantir",
}

if "results" not in st.session_state:
    st.session_state.results = {}
if "facts" not in st.session_state:
    st.session_state.facts = ""


def load_prompt(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {filename}")
    return prompt_path.read_text(encoding="utf-8")


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


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def count_sentences(text: str) -> int:
    sentences = re.split(r"[.!?]+(?:\s|$)", text.strip())
    return len([sentence for sentence in sentences if sentence.strip()])


def count_paragraphs(text: str) -> int:
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return len([paragraph for paragraph in paragraphs if paragraph.strip()])


def find_repeated_phrases(text: str, phrase_size: int = 5) -> list[str]:
    words = re.findall(r"\b\w+\b", text.lower(), flags=re.UNICODE)
    phrases = Counter(
        tuple(words[index : index + phrase_size])
        for index in range(len(words) - phrase_size + 1)
    )

    repeated_phrases = []
    for phrase, count in phrases.most_common():
        if count < 2:
            continue
        if all(word in COMMON_WORDS for word in phrase):
            continue
        repeated_phrases.append(f"{' '.join(phrase)} ({count}x)")

    return repeated_phrases[:3]


def find_terms(text: str, terms: set[str]) -> list[str]:
    normalized_text = text.lower()
    found_terms = []

    for term in sorted(terms):
        pattern = rf"\b{re.escape(term.lower())}\b"
        if re.search(pattern, normalized_text, flags=re.UNICODE):
            found_terms.append(term)

    return found_terms


def has_markdown_markers(text: str) -> bool:
    return bool(re.search(r"(\*\*|__|^#{1,6}\s|^\s*[-*]\s+)", text, re.MULTILINE))


def get_newsletter_body(text: str) -> str:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) <= 1:
        return text
    return "\n".join(lines[1:])


def get_text_for_repetition_check(format_key: str, text: str) -> str:
    if format_key in {"blog", "newsletter"}:
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        if len(lines) > 1:
            return "\n".join(lines[1:])
    return text


def get_tweet_lines(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def has_thread_numbering(lines: list[str]) -> bool:
    if not lines:
        return False
    return all(re.match(r"^\d+/\d+\s+\S", line) for line in lines)


def build_validation_checks(format_key: str, text: str) -> dict:
    metric_text = get_newsletter_body(text) if format_key == "newsletter" else text
    word_count = count_words(metric_text)
    sentence_count = count_sentences(metric_text)
    paragraph_count = count_paragraphs(metric_text)
    repeated_phrases = find_repeated_phrases(
        get_text_for_repetition_check(format_key, text)
    )
    pt_br_terms = find_terms(text, FORBIDDEN_PT_BR_TERMS)
    unsupported_claim_terms = find_terms(text, UNSUPPORTED_CLAIM_TERMS)
    tweet_lines = get_tweet_lines(text) if format_key == "tweet_thread" else []
    long_tweets = [
        f"{index + 1} ({len(line)} caracteres)"
        for index, line in enumerate(tweet_lines)
        if len(line) > 280
    ]

    checks = [
        {
            "ok": not repeated_phrases,
            "message": (
                "Sem repeticoes obvias de frases."
                if not repeated_phrases
                else f"Possiveis repeticoes: {', '.join(repeated_phrases)}."
            ),
        },
        {
            "ok": not has_markdown_markers(text),
            "message": "Sem marcadores Markdown visiveis."
            if not has_markdown_markers(text)
            else "Foram encontrados marcadores Markdown visiveis no texto.",
        },
        {
            "ok": not pt_br_terms,
            "message": "Sem termos comuns de portugues do Brasil."
            if not pt_br_terms
            else f"Possiveis termos de portugues do Brasil: {', '.join(pt_br_terms)}.",
        },
        {
            "ok": not unsupported_claim_terms,
            "message": "Sem verbos fortes de garantia ou comprovacao."
            if not unsupported_claim_terms
            else f"Confirma se estes termos estao suportados pelos factos: {', '.join(unsupported_claim_terms)}.",
        },
    ]

    if format_key == "blog":
        checks.append(
            {
                "ok": word_count <= 700,
                "message": "Blog dentro de um tamanho medio."
                if word_count <= 700
                else "Blog possivelmente demasiado longo para o objetivo.",
            }
        )
    elif format_key == "linkedin":
        checks.extend(
            [
                {
                    "ok": 2 <= paragraph_count <= 4,
                    "message": "LinkedIn com 2 a 4 paragrafos."
                    if 2 <= paragraph_count <= 4
                    else "LinkedIn fora do intervalo recomendado de 2 a 4 paragrafos.",
                },
                {
                    "ok": word_count <= 180,
                    "message": "LinkedIn curto."
                    if word_count <= 180
                    else "LinkedIn possivelmente demasiado longo.",
                },
            ]
        )
    elif format_key == "tweet_thread":
        checks.extend(
            [
                {
                    "ok": 3 <= len(tweet_lines) <= 6,
                    "message": "Thread com 3 a 6 tweets."
                    if 3 <= len(tweet_lines) <= 6
                    else "Thread fora do intervalo recomendado de 3 a 6 tweets.",
                },
                {
                    "ok": not long_tweets,
                    "message": "Todos os tweets respeitam o limite de 280 caracteres."
                    if not long_tweets
                    else f"Tweets acima de 280 caracteres: {', '.join(long_tweets)}.",
                },
                {
                    "ok": has_thread_numbering(tweet_lines),
                    "message": "Thread numerada no formato 1/n."
                    if has_thread_numbering(tweet_lines)
                    else "Thread deve estar numerada no formato 1/n, 2/n, etc.",
                },
                {
                    "ok": word_count <= 220,
                    "message": "Thread curta e adequada ao formato."
                    if word_count <= 220
                    else "Thread possivelmente demasiado longa.",
                },
            ]
        )
    elif format_key == "newsletter":
        checks.extend(
            [
                {
                    "ok": word_count <= 60,
                    "message": "Newsletter com no maximo 60 palavras no corpo."
                    if word_count <= 60
                    else "Newsletter ultrapassa o limite recomendado de 60 palavras no corpo.",
                },
                {
                    "ok": sentence_count <= 2,
                    "message": "Newsletter com no maximo 2 frases."
                    if sentence_count <= 2
                    else "Newsletter ultrapassa o limite recomendado de 2 frases.",
                },
                {
                    "ok": paragraph_count == 1,
                    "message": "Newsletter com um unico paragrafo."
                    if paragraph_count == 1
                    else "Newsletter deve ficar num unico paragrafo.",
                },
            ]
        )

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "checks": checks,
    }


def newsletter_needs_repair(text: str) -> bool:
    newsletter_body = get_newsletter_body(text)
    return (
        count_words(newsletter_body) > 60
        or count_sentences(newsletter_body) > 2
        or count_paragraphs(newsletter_body) != 1
        or has_markdown_markers(text)
    )


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
st.write("Prototipo inicial do projeto de AO/SSD")
st.caption("Um input unico gera multiplos formatos adaptados a diferentes plataformas.")

texto = st.text_area("Fonte de conteudo", height=250)

if st.button("Gerar conteudos"):
    if not texto.strip():
        st.warning("Insere algum texto primeiro.")
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
