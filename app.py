import streamlit as st

st.set_page_config(page_title="Content Pipeline Agent", layout="wide")

st.title("Content Pipeline Agent")
st.write("Protótipo inicial do projeto de AO/SSD")

texto = st.text_area("Fonte de conteúdo", height=250)

if st.button("Gerar conteúdos"):
    if texto.strip():
        st.success("Entrada recebida. A lógica de geração será ligada no próximo passo.")
    else:
        st.warning("Insere algum texto primeiro.")
