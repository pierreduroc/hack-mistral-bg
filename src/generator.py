"""
Step 3 — Creative Variant Generation
Produces 3 distinct game variants from the mechanics analysis.
Each variant preserves the original game spirit while adding
replayability or simplifying the experience.
"""

from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


PROMPT_VARIANTES = PromptTemplate(
    input_variables=["analyse"],
    template="""
Tu es un game designer créatif. À partir de l'analyse des mécaniques ci-dessous,
génère exactement 3 variantes créatives en Markdown **uniquement** (pas d'introduction).

Contraintes pour chaque variante :
- Conserver l'esprit du jeu original.
- Ajouter de la rejouabilité OU simplifier l'expérience.
- Être testable sans matériel supplémentaire si possible.

Format attendu pour chaque variante :
### Variante N : <Titre court>
**Description** : <2-3 phrases décrivant la variante>
**Impact** : <Effet sur la durée, la tension ou la complexité>
**Règles modifiées** :
- Ancienne règle : <texte original>
- **Nouvelle règle** : <**texte modifié en gras**>

Analyse des mécaniques :
{analyse}
""",
)


def generer_variantes(analyse: str, llm: Ollama) -> str:
    """Generate 3 creative game variants from the mechanics analysis.

    Args:
        analyse: Markdown mechanics analysis from Step 2.
        llm:     Configured Ollama LLM instance.

    Returns:
        Three game variants in Markdown.
    """
    chain = LLMChain(llm=llm, prompt=PROMPT_VARIANTES)
    return chain.run(analyse=analyse).strip()
