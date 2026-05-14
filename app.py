import streamlit as st

from content_pipeline import (
    AUDIO_FILE_TYPES,
    build_markdown_export as build_pipeline_markdown_export,
    create_client,
    decode_text_file,
    extract_facts,
    format_example_name,
    generate_content,
    get_example_files,
    transcribe_audio_bytes,
)
from validation import build_validation_checks


if "results" not in st.session_state:
    st.session_state.results = {}
if "facts" not in st.session_state:
    st.session_state.facts = ""
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "source_description" not in st.session_state:
    st.session_state.source_description = ""


def build_markdown_export() -> str:
    return build_pipeline_markdown_export(
        st.session_state.source_description,
        st.session_state.source_text,
        st.session_state.facts,
        st.session_state.results,
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
        try:
            client = create_client()

            with st.spinner("A gerar conteudos..."):
                if uploaded_audio is not None:
                    texto = transcribe_audio_bytes(
                        client,
                        uploaded_audio.name,
                        uploaded_audio.getvalue(),
                    )
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
