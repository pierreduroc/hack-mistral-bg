"""
Step 4 — Full Workflow Integration
Orchestrates Steps 1-3 into a single pipeline optimised for a local GPU
(RTX 4070 Ti 16 GB, Mistral 7B via Ollama).

Usage:
    from src.workflow import executer_workflow
    resultat = executer_workflow("regles_jeu.pdf")
    print(resultat)
"""

import os
from src.extractor import extraire_texte_pdf
from src.analyzer import construire_llm, extraire_et_structurer, analyser_mecaniques
from src.generator import generer_variantes


def executer_workflow(
    chemin_pdf: str,
    temperature_extraction: float = 0.2,  # More deterministic for factual extraction
    temperature_creation: float = 0.7,    # More creative for variant generation
    num_gpu: int = 1,                      # Offload all layers to RTX 4070 Ti
) -> dict:
    """Run the full pipeline on a PDF of board game rules.

    Pipeline:
        PDF  →  raw text  →  structured rules  →  mechanics analysis  →  3 variants

    Args:
        chemin_pdf:              Path to the rules PDF.
        temperature_extraction:  LLM temperature for extraction/analysis steps.
        temperature_creation:    LLM temperature for variant generation step.
        num_gpu:                 GPU layers (1 = full offload, maximises RTX VRAM).

    Returns:
        dict with keys:
            - texte_brut         : raw extracted text
            - regles_structurees : Markdown structured rules (Step 1 output)
            - analyse            : Markdown mechanics analysis (Step 2 output)
            - variantes          : Markdown with 3 variants (Step 3 output)
            - sortie_complete    : Full combined Markdown document
    """

    print("[1/4] Extraction du texte PDF...")
    texte_brut = extraire_texte_pdf(chemin_pdf)
    if not texte_brut:
        raise ValueError(f"Impossible d'extraire du texte depuis : {chemin_pdf}")

    # Two LLM instances with different temperatures
    llm_factuel = construire_llm(temperature=temperature_extraction, num_gpu=num_gpu)
    llm_creatif = construire_llm(temperature=temperature_creation, num_gpu=num_gpu)

    print("[2/4] Structuration des règles avec Mistral...")
    regles_structurees = extraire_et_structurer(texte_brut, llm_factuel)

    print("[3/4] Analyse des mécaniques...")
    analyse = analyser_mecaniques(regles_structurees, llm_factuel)

    print("[4/4] Génération des variantes créatives...")
    variantes = generer_variantes(analyse, llm_creatif)

    sortie_complete = _assembler_sortie(regles_structurees, analyse, variantes)

    return {
        "texte_brut": texte_brut,
        "regles_structurees": regles_structurees,
        "analyse": analyse,
        "variantes": variantes,
        "sortie_complete": sortie_complete,
    }


def _assembler_sortie(regles: str, analyse: str, variantes: str) -> str:
    """Concatenate all sections into a single Markdown document."""
    return f"{regles}\n\n---\n\n{analyse}\n\n---\n\n## Variantes créatives\n\n{variantes}\n"


def sauvegarder_markdown(contenu: str, chemin_sortie: str) -> None:
    """Save the final Markdown to a local file.

    Args:
        contenu:       Full Markdown string to write.
        chemin_sortie: Destination file path (e.g. outputs/mon_jeu.md).
    """
    os.makedirs(os.path.dirname(chemin_sortie) or ".", exist_ok=True)
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        f.write(contenu)
    print(f"[OK] Fichier sauvegardé : {chemin_sortie}")
