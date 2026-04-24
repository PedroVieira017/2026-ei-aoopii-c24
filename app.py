import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"

if "results" not in st.session_state:
    st.session_state.results = {}


def load_prompt(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {filename}")
    return prompt_path.read_text(encoding="utf-8")


def generate_content(client: OpenAI, prompt_filename: str, source_text: str) -> dict:
    prompt = load_prompt(prompt_filename)

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=prompt,
        input=source_text,
    )

    return {
        "prompt": prompt,
        "text": response.output_text.strip(),
    }


st.set_page_config(page_title="Content Pipeline Agent", layout="wide")

st.title("Content Pipeline Agent")
st.write("Protótipo inicial do projeto de AO/SSD")
st.caption("Um input único gera múltiplos formatos adaptados a diferentes plataformas.")

texto = st.text_area("Fonte de conteúdo", height=250)

if st.button("Gerar conteúdos"):
    if not texto.strip():
        st.warning("Insere algum texto primeiro.")
    else:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            st.error("A variável OPENAI_API_KEY não foi encontrada no ficheiro .env.")
        else:
            try:
                client = OpenAI(api_key=api_key)

                with st.spinner("A gerar conteúdos..."):
                    st.session_state.results = {
                        "blog": generate_content(client, "blog_post.txt", texto),
                        "linkedin": generate_content(client, "linkedin_post.txt", texto),
                        "newsletter": generate_content(
                            client, "newsletter_section.txt", texto
                        ),
                    }

                st.success("Conteúdos gerados com sucesso.")

            except Exception as error:
                st.error(f"Ocorreu um erro ao gerar os conteúdos: {error}")

st.divider()

blog_tab, linkedin_tab, newsletter_tab = st.tabs(
    ["Blog Post", "LinkedIn Post", "Newsletter Section"]
)

with blog_tab:
    st.subheader("Blog Post")
    if "blog" in st.session_state.results:
        st.text_area(
            "Resultado",
            value=st.session_state.results["blog"]["text"],
            height=320,
        )
        with st.expander("Prompt carregado"):
            st.code(st.session_state.results["blog"]["prompt"], language="text")
    else:
        st.info("O resultado do blog post será mostrado aqui.")

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
        st.info("O resultado do post de LinkedIn será mostrado aqui.")

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
        st.info("O resultado da newsletter será mostrado aqui.")
