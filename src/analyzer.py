"""
Step 2 — Rules Analysis
Uses Mistral 7B (via Ollama) to structure the raw PDF text into Markdown
and evaluate the game mechanics.
"""

from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


def construire_llm(temperature: float = 0.3, num_gpu: int = 1) -> Ollama:
    """Instantiate Mistral 7B via Ollama with GPU acceleration.

    Args:
        temperature: Sampling temperature (lower = more factual).
        num_gpu:     Number of GPU layers to offload to VRAM.
    """
    return Ollama(
        model="mistral",
        temperature=temperature,
        num_gpu=num_gpu,
    )


# ---------------------------------------------------------------------------
# Prompt: extraction + structuring
# ---------------------------------------------------------------------------
PROMPT_EXTRACTION = PromptTemplate(
    input_variables=["regles"],
    template="""
Tu es un expert en jeux de société. À partir du texte brut suivant extrait d'un PDF de règles,
produis un résumé structuré en Markdown **uniquement** (pas d'introduction, pas de commentaire).

Format attendu :
# Règles extraites : <Titre du jeu>
**Objectif** : <Une phrase résumant le but du jeu>

## Mécaniques principales
- <mécanique 1>
- <mécanique 2>
...

## Règles spéciales
- <règle spéciale 1 si applicable>
...

## Exemple de tour de jeu
<Description d'un tour type si mentionné dans le texte>

Texte brut des règles :
{regles}
""",
)

# ---------------------------------------------------------------------------
# Prompt: mechanics analysis
# ---------------------------------------------------------------------------
PROMPT_ANALYSE = PromptTemplate(
    input_variables=["regles_structured"],
    template="""
À partir des règles structurées ci-dessous, produis une analyse en Markdown **uniquement**.

Format attendu :
### Analyse des mécaniques
- **Mécaniques** : <liste séparée par des virgules>
- **Complexité** : <chiffre entre 1 et 5>/5 (1=simple, 5=expert)
- **Points forts** : <liste à puces>
- **Points à améliorer** : <liste à puces>

Règles structurées :
{regles_structured}
""",
)


def extraire_et_structurer(texte_brut: str, llm: Ollama) -> str:
    """Run the extraction prompt: raw text → structured Markdown rules.

    Args:
        texte_brut: Raw text extracted from the PDF.
        llm:        Configured Ollama LLM instance.

    Returns:
        Structured rules in Markdown.
    """
    chain = LLMChain(llm=llm, prompt=PROMPT_EXTRACTION)
    return chain.run(regles=texte_brut).strip()


def analyser_mecaniques(regles_structured: str, llm: Ollama) -> str:
    """Run the analysis prompt: structured rules → mechanics analysis.

    Args:
        regles_structured: Markdown output from extraire_et_structurer.
        llm:               Configured Ollama LLM instance.

    Returns:
        Mechanics analysis in Markdown.
    """
    chain = LLMChain(llm=llm, prompt=PROMPT_ANALYSE)
    return chain.run(regles_structured=regles_structured).strip()
