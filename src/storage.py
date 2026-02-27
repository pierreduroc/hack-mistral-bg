"""
Step 5 — Storage Integration
Handles Minio object storage and Git/DVC versioning for generated outputs.
"""

import os
import subprocess
from minio import Minio
from minio.error import S3Error


# ---------------------------------------------------------------------------
# Minio helpers
# ---------------------------------------------------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = "jeux-regles"


def _get_client() -> Minio:
    """Create an authenticated Minio client (no TLS for local setups)."""
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )


def _assurer_bucket(client: Minio, bucket: str) -> None:
    """Create the bucket if it does not exist yet."""
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"[Minio] Bucket '{bucket}' créé.")


def publier_sur_minio(chemin_local: str, nom_objet: str, bucket: str = MINIO_BUCKET) -> None:
    """Upload a local file to Minio.

    Args:
        chemin_local: Path to the local Markdown file.
        nom_objet:    Object name within the bucket (e.g. "variantes/mon_jeu.md").
        bucket:       Target Minio bucket (default: jeux-regles).
    """
    client = _get_client()
    _assurer_bucket(client, bucket)
    try:
        client.fput_object(bucket, nom_objet, chemin_local)
        print(f"[Minio] Fichier publié : {bucket}/{nom_objet}")
    except S3Error as e:
        print(f"[Minio] Erreur lors du téléversement : {e}")


def telecharger_depuis_minio(nom_objet: str, chemin_local: str, bucket: str = MINIO_BUCKET) -> None:
    """Download an object from Minio to a local file.

    Args:
        nom_objet:    Object name within the bucket.
        chemin_local: Destination path on disk.
        bucket:       Source Minio bucket.
    """
    client = _get_client()
    try:
        client.fget_object(bucket, nom_objet, chemin_local)
        print(f"[Minio] Téléchargé : {bucket}/{nom_objet} → {chemin_local}")
    except S3Error as e:
        print(f"[Minio] Erreur lors du téléchargement : {e}")


# ---------------------------------------------------------------------------
# Git + DVC helpers
# ---------------------------------------------------------------------------

def commiter_markdown(chemin_md: str, message: str = None) -> None:
    """Stage and commit a Markdown file in the local Git repository.

    Args:
        chemin_md: Path to the Markdown file to commit.
        message:   Commit message (auto-generated if None).
    """
    nom_fichier = os.path.basename(chemin_md)
    if message is None:
        message = f"feat: add generated variants for {nom_fichier}"

    subprocess.run(["git", "add", chemin_md], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    print(f"[Git] Commit effectué : {message}")


def versionner_pdf_dvc(chemin_pdf: str) -> None:
    """Track a PDF with DVC so large binaries stay out of Git history.

    Args:
        chemin_pdf: Path to the PDF rules file to track.
    """
    subprocess.run(["dvc", "add", chemin_pdf], check=True)
    # DVC creates a .dvc sidecar file — commit it to Git
    subprocess.run(["git", "add", chemin_pdf + ".dvc", ".dvcignore"], check=True)
    subprocess.run(["git", "commit", "-m", f"chore: track {os.path.basename(chemin_pdf)} with DVC"], check=True)
    print(f"[DVC] Fichier versionné : {chemin_pdf}")
