import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
MODEL_NAME = "llama-3.3-70b-versatile"
MODEL_TEMPERATURE = 0.2

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
    response = client.responses.create(
        model=MODEL_NAME,
        instructions=instructions,
        input=content,
        temperature=MODEL_TEMPERATURE,
    )
    return response.output_text.strip()


def extract_facts(client: OpenAI, source_text: str) -> str:
    prompt = load_prompt("facts_extraction.txt")
    return run_generation(client, prompt, source_text)


def generate_content(client: OpenAI, prompt_filename: str, facts_text: str) -> dict:
    prompt = load_prompt(prompt_filename)
    draft = run_generation(client, prompt, facts_text)
    review_prompt = load_prompt("compliance_review.txt")
    reviewed_text = run_generation(
        client,
        review_prompt,
        f"FACTOS:\n{facts_text}\n\nRASCUNHO:\n{draft}",
    )
    return {
        "prompt": prompt,
        "text": reviewed_text,
    }


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
                            client, "blog_post.txt", st.session_state.facts
                        ),
                        "linkedin": generate_content(
                            client, "linkedin_post.txt", st.session_state.facts
                        ),
                        "newsletter": generate_content(
                            client, "newsletter_section.txt", st.session_state.facts
                        ),
                    }

                st.success("Conteudos gerados com sucesso.")

            except Exception as error:
                st.error(f"Ocorreu um erro ao gerar os conteudos: {error}")

st.divider()

blog_tab, linkedin_tab, newsletter_tab = st.tabs(
    ["Blog Post", "LinkedIn Post", "Newsletter Section"]
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
        with st.expander("Prompt carregado"):
            st.code(st.session_state.results["linkedin"]["prompt"], language="text")
    else:
        st.info("O resultado do post de LinkedIn sera mostrado aqui.")

with newsletter_tab:
    st.subheader("Newsletter Section")
    if "newsletter" in st.session_state.results:
        st.text_area(
            "Resultado",
            value=st.session_state.results["newsletter"]["text"],
            height=220,
        )
        with st.expander("Prompt carregado"):
            st.code(st.session_state.results["newsletter"]["prompt"], language="text")
    else:
        st.info("O resultado da newsletter sera mostrado aqui.")
