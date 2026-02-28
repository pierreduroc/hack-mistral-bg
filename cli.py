"""
Step 6 — CLI Script
Usage:
    # Full pipeline on a single PDF
    python cli.py <chemin_pdf> [--output outputs/mon_jeu.md] [--minio] [--dvc]

    # Extract raw text only from all PDFs in bg_rules/
    python cli.py --extract-only
    python cli.py --extract-only --bg-rules-dir path/to/pdfs --output-rules-dir path/to/output
"""

import argparse
import os
import sys

from src.extractor import extraire_texte_pdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère des variantes de règles de jeu de société à partir d'un PDF."
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        help="Chemin vers le fichier PDF des règles (non requis avec --extract-only)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Chemin de sortie du fichier Markdown (défaut : outputs/<nom_jeu>.md)",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        dest="extract_only",
        help="Extraire uniquement le texte brut de tous les PDFs dans --bg-rules-dir vers --output-rules-dir",
    )
    parser.add_argument(
        "--bg-rules-dir",
        default="bg_rules",
        dest="bg_rules_dir",
        help="Dossier source contenant les PDFs (défaut : bg_rules/)",
    )
    parser.add_argument(
        "--output-rules-dir",
        default="output_rules",
        dest="output_rules_dir",
        help="Dossier de sortie pour le texte extrait (défaut : output_rules/)",
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


def batch_extract(bg_rules_dir: str, output_rules_dir: str) -> None:
    """Extract raw text from all PDFs in bg_rules_dir and save as .txt in output_rules_dir."""
    if not os.path.isdir(bg_rules_dir):
        print(f"[Erreur] Dossier introuvable : {bg_rules_dir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_rules_dir, exist_ok=True)

    pdfs = [f for f in os.listdir(bg_rules_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"[Info] Aucun PDF trouvé dans {bg_rules_dir}")
        return

    print(f"[Extraction] {len(pdfs)} PDF(s) trouvé(s) dans {bg_rules_dir}")
    ok, errors = 0, []

    for filename in sorted(pdfs):
        pdf_path = os.path.join(bg_rules_dir, filename)
        nom = os.path.splitext(filename)[0]
        output_path = os.path.join(output_rules_dir, f"{nom}.txt")

        print(f"  → {filename} ...", end=" ", flush=True)
        try:
            texte = extraire_texte_pdf(pdf_path)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(texte)
            print("OK")
            ok += 1
        except Exception as e:
            print(f"ERREUR ({e})")
            errors.append(filename)

    print(f"\n=== Extraction terminée : {ok}/{len(pdfs)} réussie(s) ===")
    print(f"Sorties : {output_rules_dir}/")
    if errors:
        print(f"[Erreurs] {', '.join(errors)}", file=sys.stderr)


def main() -> None:
    args = parse_args()

    if args.extract_only:
        batch_extract(args.bg_rules_dir, args.output_rules_dir)
        return

    from src.workflow import executer_workflow, sauvegarder_markdown
    from src.storage import publier_sur_minio, commiter_markdown, versionner_pdf_dvc

    if not args.pdf:
        print("[Erreur] Fournissez un fichier PDF ou utilisez --extract-only.", file=sys.stderr)
        sys.exit(1)

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
