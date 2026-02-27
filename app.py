"""
Step 6 — Streamlit Interface
Run: streamlit run app.py
"""

import os
import tempfile
import streamlit as st

from src.extractor import extraire_texte_pdf
from src.analyzer import construire_llm, extraire_et_structurer, analyser_mecaniques
from src.generator import generer_variantes
from src.workflow import _assembler_sortie, sauvegarder_markdown
from src.storage import publier_sur_minio

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Générateur de variantes de jeux",
    page_icon="🎲",
    layout="wide",
)

st.title("Générateur de variantes de jeux de société")
st.caption("Powered by Mistral 7B (Ollama) — 100 % local")

# ---------------------------------------------------------------------------
# Sidebar: LLM settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuration LLM")
    temperature_extraction = st.slider(
        "Température extraction (factuel)", 0.0, 1.0, 0.2, 0.05
    )
    temperature_creation = st.slider(
        "Température génération (créatif)", 0.0, 1.0, 0.7, 0.05
    )
    num_gpu = st.number_input("Couches GPU (num_gpu)", min_value=0, max_value=1, value=1)
    publier_minio = st.checkbox("Publier sur Minio après génération", value=False)

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("Importe un PDF de règles", type=["pdf"])

if uploaded_file:
    st.info(f"Fichier reçu : **{uploaded_file.name}** ({uploaded_file.size} octets)")

    if st.button("Lancer le pipeline", type="primary"):
        nom_jeu = os.path.splitext(uploaded_file.name)[0].replace(" ", "_").lower()

        # Step 1 — Extract
        with st.spinner("Extraction du texte PDF..."):
            texte_brut = extraire_texte_pdf(uploaded_file)

        if not texte_brut:
            st.error("Impossible d'extraire du texte depuis ce PDF.")
            st.stop()

        # Build LLM instances
        llm_factuel = construire_llm(temperature=temperature_extraction, num_gpu=int(num_gpu))
        llm_creatif = construire_llm(temperature=temperature_creation, num_gpu=int(num_gpu))

        # Step 2 — Structure + Analyse
        with st.spinner("Structuration des règles avec Mistral..."):
            regles_structurees = extraire_et_structurer(texte_brut, llm_factuel)

        with st.spinner("Analyse des mécaniques..."):
            analyse = analyser_mecaniques(regles_structurees, llm_factuel)

        # Step 3 — Generate variants
        with st.spinner("Génération des variantes créatives..."):
            variantes = generer_variantes(analyse, llm_creatif)

        # Assemble full document
        sortie_complete = _assembler_sortie(regles_structurees, analyse, variantes)

        # Display in tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Règles structurées", "Analyse", "Variantes", "Document complet"]
        )
        with tab1:
            st.markdown(regles_structurees)
        with tab2:
            st.markdown(analyse)
        with tab3:
            st.markdown(variantes)
        with tab4:
            st.markdown(sortie_complete)

        # Download button
        st.download_button(
            label="Télécharger le Markdown",
            data=sortie_complete.encode("utf-8"),
            file_name=f"variantes_{nom_jeu}.md",
            mime="text/markdown",
        )

        # Optional Minio upload
        if publier_minio:
            with tempfile.NamedTemporaryFile(
                suffix=".md", delete=False, mode="w", encoding="utf-8"
            ) as tmp:
                tmp.write(sortie_complete)
                chemin_tmp = tmp.name
            with st.spinner("Envoi vers Minio..."):
                publier_sur_minio(chemin_tmp, f"variantes/{nom_jeu}.md")
            os.unlink(chemin_tmp)
            st.success("Fichier publié sur Minio.")
