Contexte :
Tu es un assistant expert en orchestration de LLM pour la co-création de jeux de société. Tu vas m'aider à concevoir un workflow local pour :

Extraire les règles d'un jeu de société à partir d'un PDF.
Analyser ces règles pour en comprendre les mécaniques clés.
Générer 3 variantes créatives (nouveaux scénarios, règles alternatives, ou extensions).
Structurer la sortie en Markdown pour une intégration facile dans une base de données (Minio) ou un système de versioning (Git).
Contraintes techniques :

Le workflow s'exécutera sur un PC Gaming (32 Go RAM, RTX 4070 Ti 16 Go).
On utilisera des outils locaux : Ollama (pour Mistral 7B), Python (avec PyPDF2, langchain), et Minio (stockage).
Le code doit être modulaire, optimisé pour le GPU, et intégrable dans une interface Streamlit ou un script CLI.

Étapes à suivre (pour le LLM) :
1. Extraction des règles depuis un PDF

Entrée : Un fichier PDF (ex : regles_jeu.pdf) contenant les règles d'un jeu de société.
Sortie : Un texte structuré en Markdown avec :

Titre du jeu
Objectif du jeu (1 phrase)
Mécaniques principales (liste à puces)
Règles spéciales (si existantes)
Exemple de tour de jeu (si décrit)

Code Python suggéré pour l'extraction :
python
Copier

import PyPDF2

def extraire_texte_pdf(chemin_pdf):
    texte = ""
    with open(chemin_pdf, "rb") as fichier:
        lecteur = PyPDF2.PdfReader(fichier)
        for page in lecteur.pages:
            texte += page.extract_text()
    return texte

# Exemple d'appel :
texte_regles = extraire_texte_pdf("regles_jeu.pdf")

Ta tâche :

Analyser le texte extrait (texte_regles) et résumer les éléments ci-dessus en Markdown.
Ignorer les sections non pertinentes (ex : crédits, illustrations).

2. Analyse des mécaniques

Entrée : Le texte structuré de l'étape 1.
Sortie :

Une liste des mécaniques clés (ex : "draft de cartes", "placement d'ouvriers", "enchères").
Une évaluation de la complexité (1 à 5, où 1 = simple, 5 = expert).
Points forts/faibles (ex : "Règles claires mais tour trop long").

Format attendu :
markdown
Copier

### Analyse des mécaniques
- **Mécaniques** : [liste]
- **Complexité** : X/5
- **Points à améliorer** : [liste]


3. Génération de 3 variantes créatives

Entrée : L'analyse de l'étape 2.
Sortie : 3 propositions de variantes, chacune avec :

Titre (ex : "Mode coopératif")
Description (2-3 phrases)
Impact sur le gameplay (ex : "Réduit la durée de 30%")
Règles modifiées (en Markdown, avec les changements en gras).

Exemple de format :
markdown
Copier

### Variante 1 : [Titre]
**Description** : [texte]
**Impact** : [texte]
**Règles modifiées** :
- Ancienne règle : [texte]
- **Nouvelle règle** : [texte en gras]

Contraintes créatives :

Les variantes doivent :

Conserver l'esprit du jeu original.
Ajouter de la rejouabilité ou simplifier l'expérience.
Être testables sans matériel supplémentaire (si possible).


4. Intégration dans un workflow local

Fournis un exemple de code Python utilisant langchain et Ollama pour automatiser ce processus.
Optimise pour le GPU : Utilise vLLM ou Ollama avec les paramètres suivants :
python
Copier

from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Configuration pour Mistral 7B (local)
llm = Ollama(model="mistral", temperature=0.7, num_gpu=1)  # Utilise 1 GPU

# Prompt pour l'analyse
prompt_analyse = PromptTemplate(
    input_variables=["regles"],
    template="""
    Analyse les règles suivantes et structure-les en Markdown comme demandé :
    {regles}
    """
)

chain_analyse = LLMChain(llm=llm, prompt=prompt_analyse)

# Exécution
resultat = chain_analyse.run(regles=texte_regles)
print(resultat)



5. Sortie finale

Fournis un exemple complet de sortie Markdown pour un jeu fictif (ex : "Les Aventuriers du Rail").
Ajoute des commentaires dans le code pour expliquer chaque étape.

Exemple de sortie attendue (pour validation)
markdown
Copier

# Règles extraites : Les Aventuriers du Rail
**Objectif** : Relier des villes par des routes ferroviaires en collectant des cartes wagon.

## Mécaniques principales
- Draft de cartes wagon.
- Placement de routes (3-6 wagons).
- Objectifs secrets (missions).

## Variante 1 : Mode "Course contre la montre"
**Description** : Les joueurs ont 20 tours pour compléter leurs missions, sinon la partie se termine.
**Impact** : Augmente la tension et réduit la durée à 45 min.
**Règles modifiées** :
- Ancienne règle : "La partie se termine quand un joueur a 2 missions ou moins."
- **Nouvelle règle** : "La partie se termine après 20 tours, quel que soit l'état des missions."

## Variante 2 : [Titre]
...


Notes supplémentaires pour l'orchestration locale


Stockage :

Sauvegarde les sorties dans Minio (bucket jeux-regles) au format jeu_[nom].md.
Utilise boto3 pour interagir avec Minio :
python
Copier

from minio import Minio
client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
client.fput_object("jeux-regles", "variantes/aventuriers_du_rail.md", "sortie.md")




Versioning :

Commite les fichiers Markdown dans un dépôt Git local avec DVC pour les PDF :
bash
Copier

git add variantes/aventuriers_du_rail.md
dvc add regles_jeu.pdf




Interface utilisateur :

Pour Streamlit, utilise ce template :
python
Copier

import streamlit as st
st.title("Générateur de variantes de jeux")
uploaded_file = st.file_uploader("Upload un PDF")
if uploaded_file:
    texte = extraire_texte_pdf(uploaded_file)
    resultat = chain_analyse.run(regles=texte)
    st.markdown(resultat)




Critères de qualité

Précision : Les règles extraites doivent être fidèles au PDF.
Créativité : Les variantes doivent être originelles mais jouables.
Optimisation : Le code doit tourner en <30 secondes sur ta config (utilise num_gpu=1 et la quantification si nécessaire).
