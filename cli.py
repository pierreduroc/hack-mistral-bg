"""
Step 6 — CLI Script
Usage:
    python cli.py <chemin_pdf> [--output outputs/mon_jeu.md] [--minio] [--dvc]
"""

import argparse
import os
import sys

from src.workflow import executer_workflow, sauvegarder_markdown
from src.storage import publier_sur_minio, commiter_markdown, versionner_pdf_dvc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère des variantes de règles de jeu de société à partir d'un PDF."
    )
    parser.add_argument("pdf", help="Chemin vers le fichier PDF des règles")
    parser.add_argument(
        "--output",
        default=None,
        help="Chemin de sortie du fichier Markdown (défaut : outputs/<nom_jeu>.md)",
    )
    parser.add_argument(
        "--minio",
        action="store_true",
        help="Publier le résultat sur Minio après génération",
    )
    parser.add_argument(
        "--dvc",
        action="store_true",
        help="Versionner le PDF avec DVC et commiter le Markdown dans Git",
    )
    parser.add_argument(
        "--temperature-extraction",
        type=float,
        default=0.2,
        dest="temperature_extraction",
        help="Température LLM pour l'extraction (défaut : 0.2)",
    )
    parser.add_argument(
        "--temperature-creation",
        type=float,
        default=0.7,
        dest="temperature_creation",
        help="Température LLM pour la génération (défaut : 0.7)",
    )
    parser.add_argument(
        "--num-gpu",
        type=int,
        default=1,
        dest="num_gpu",
        help="Nombre de couches déportées sur GPU (défaut : 1)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not os.path.isfile(args.pdf):
        print(f"[Erreur] Fichier introuvable : {args.pdf}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    nom_jeu = os.path.splitext(os.path.basename(args.pdf))[0].replace(" ", "_").lower()
    chemin_sortie = args.output or os.path.join("outputs", f"{nom_jeu}.md")

    # Run pipeline
    resultats = executer_workflow(
        args.pdf,
        temperature_extraction=args.temperature_extraction,
        temperature_creation=args.temperature_creation,
        num_gpu=args.num_gpu,
    )

    # Save to disk
    sauvegarder_markdown(resultats["sortie_complete"], chemin_sortie)

    # Optional: DVC versioning
    if args.dvc:
        print("[DVC] Versionnage du PDF...")
        versionner_pdf_dvc(args.pdf)
        print("[Git] Commit du Markdown...")
        commiter_markdown(chemin_sortie)

    # Optional: Minio upload
    if args.minio:
        print("[Minio] Envoi vers le bucket jeux-regles...")
        publier_sur_minio(chemin_sortie, f"variantes/{os.path.basename(chemin_sortie)}")

    print("\n=== Pipeline terminé avec succès ===")
    print(f"Sortie : {chemin_sortie}")


if __name__ == "__main__":
    main()
