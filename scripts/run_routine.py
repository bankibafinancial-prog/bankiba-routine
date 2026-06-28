"""
Bankiba Technology — Routine quotidienne d'actualités financières CEMAC.

Ce script orchestre Claude (API Anthropic) avec des outils de recherche web
(Tavily) et de récupération de page (requests) pour produire chaque jour
le fichier cemac_finance_news.json.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import anthropic
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]
MODEL = "claude-sonnet-4-6"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "cemac_finance_news.json")

DEFAULT_IMAGE = (
    "https://plus.unsplash.com/premium_photo-1691223733678-095fee90a0a7"
    "?fm=jpg&q=60&w=3000&auto=format&fit=crop&ixlib=rb-4.1.0"
    "&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8YXJ0aWNsZXxlbnwwfHwwfHx8MA%3D%3D"
)

WAT = timezone(timedelta(hours=1))  # West Africa Time (UTC+1)
NOW = datetime.now(WAT)
TODAY = NOW.strftime("%Y-%m-%d")
MONTH_YEAR = NOW.strftime("%B %Y")

# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Recherche d'actualités récentes sur le web. Retourne une liste d'articles "
            "avec titre, URL, extrait et date de publication."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Requête de recherche en français ou en anglais.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_fetch",
        "description": (
            "Récupère le contenu HTML d'une page web pour en extraire l'image og:image "
            "ou twitter:image. Retourne l'URL absolue de l'image ou null si non trouvée."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL absolue de la page à récupérer.",
                }
            },
            "required": ["url"],
        },
    },
]

# ---------------------------------------------------------------------------
# Implémentation des outils
# ---------------------------------------------------------------------------

def web_search(query: str) -> str:
    """Appelle l'API Tavily et retourne les résultats formatés."""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced",
                "include_answer": False,
                "max_results": 6,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return "Aucun résultat trouvé."
        lines = []
        for r in results:
            lines.append(
                f"- Titre: {r.get('title', '')}\n"
                f"  URL: {r.get('url', '')}\n"
                f"  Date: {r.get('published_date', 'inconnue')}\n"
                f"  Extrait: {r.get('content', '')[:400]}"
            )
        return "\n\n".join(lines)
    except Exception as exc:
        return f"Erreur de recherche: {exc}"


def web_fetch(url: str) -> str:
    """Récupère og:image ou twitter:image depuis une page web."""
    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BankibaBot/1.0)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for prop in ("og:image", "twitter:image"):
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                img = tag["content"].strip()
                if img.startswith("http"):
                    return img
        # Première image de contenu significative
        for img in soup.find_all("img", src=True):
            src = img["src"].strip()
            if src.startswith("http") and any(src.lower().endswith(e) for e in (".jpg", ".jpeg", ".png", ".webp")):
                if not any(skip in src.lower() for skip in ("logo", "icon", "pixel", "banner", "ad")):
                    return src
        return "null"
    except Exception:
        return "null"


def dispatch_tool(name: str, inputs: dict) -> str:
    if name == "web_search":
        return web_search(inputs["query"])
    if name == "web_fetch":
        return web_fetch(inputs["url"])
    return f"Outil inconnu: {name}"


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""Tu es l'assistant de la routine quotidienne Bankiba Technology.
Tu produis un flux d'actualités financières en FRANÇAIS pour la zone CEMAC et l'Afrique élargie.
La date du jour est {TODAY}. Réponds uniquement en français.
Ne fabrique jamais de chiffres, dates ou URLs que tu n'as pas trouvés via les outils.
"""

USER_PROMPT = f"""Exécute la routine complète en 3 étapes et termine par le JSON final.

IMAGE PAR DÉFAUT (si aucune image valide extraite) :
{DEFAULT_IMAGE}

ÉTAPE 1 — RECHERCHE
Lance les requêtes WebSearch suivantes (tu peux les lancer l'une après l'autre) :
1. "CEMAC actualité financière {MONTH_YEAR}"
2. "BVMAC bourse actualité {NOW.year}"
3. "BEAC COBAC COSUMAF réglementation {NOW.year}"
4. "Cameroun Gabon Congo Tchad dette obligataire {NOW.year}"
5. "Afrique centrale fintech investissement {NOW.year}"
6. "Nigeria Afrique Ouest finance actualité {MONTH_YEAR}"

Sélectionne 8 à 12 articles pertinents et récents (24-48h préférés), sans doublons,
de sources fiables : Agence Ecofin, Sika Finance, Investir au Cameroun, Financial Afrik,
Ecomatin, Jeune Afrique, Bloomberg, Reuters, allAfrica, L'Economie, Businessday, etc.

ÉTAPE 2 — EXTRACTION D'IMAGE
Pour chaque article retenu, utilise web_fetch sur son URL pour extraire og:image ou twitter:image.
Si la récupération échoue ou ne retourne pas d'image valide, utilise l'IMAGE PAR DÉFAUT.
Le champ image_url n'est JAMAIS null.

ÉTAPE 3 — JSON FINAL
Produis uniquement un bloc JSON valide (pas de texte avant ni après le JSON)
respectant exactement ce schéma :
{{
  "version_schema": "1.0",
  "application": "Bankiba Technology",
  "flux": "actualites_finance_cemac",
  "langue": "fr",
  "zone_couverte": "CEMAC + Afrique centrale et de l'Ouest elargie",
  "date_edition": "{TODAY}",
  "genere_le": "{NOW.strftime('%Y-%m-%dT%H:%M:%S+01:00')}",
  "nombre_articles": <nombre exact d'articles dans le tableau>,
  "categories": ["liste des catégories effectivement utilisées"],
  "articles": [
    {{
      "id": "slug-unique-minuscules-tirets",
      "titre": "Titre en français",
      "categorie": "Dette souveraine | Dette privee | Bourse | FCP / Fonds d'investissement | Fintech | Reglementation | Banque | Macroeconomie",
      "pays": "Pays concerné, ou CEMAC, ou Regional",
      "resume": "2-3 phrases factuelles en français",
      "source": "Nom du média",
      "url": "URL source",
      "date_publication": "YYYY-MM-DD ou null si incertaine",
      "image_url": "URL absolue — jamais null"
    }}
  ]
}}

Vérifie que nombre_articles correspond au nombre d'éléments du tableau
et qu'aucun image_url n'est null avant de répondre.
"""

# ---------------------------------------------------------------------------
# Boucle agentique
# ---------------------------------------------------------------------------

def run_agent() -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": USER_PROMPT}]
    max_iterations = 30

    print(f"[Bankiba] Démarrage de la routine — {TODAY}", flush=True)

    for iteration in range(max_iterations):
        print(f"[Bankiba] Itération {iteration + 1}...", flush=True)
        response = client.messages.create(
            model=MODEL,
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Ajoute la réponse de l'assistant à l'historique
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extraire le JSON du dernier bloc texte
            for block in reversed(response.content):
                if hasattr(block, "text"):
                    text = block.text.strip()
                    # Cherche un bloc ```json ... ``` ou un objet JSON direct
                    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
                    if match:
                        return json.loads(match.group(1))
                    # JSON direct (commence par {)
                    start = text.find("{")
                    if start != -1:
                        return json.loads(text[start:])
            raise ValueError("Aucun JSON trouvé dans la réponse finale.")

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[Bankiba]   outil: {block.name}({list(block.input.values())[0][:80]})", flush=True)
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"stop_reason inattendu: {response.stop_reason}")

    raise RuntimeError("Nombre maximum d'itérations atteint.")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    data = run_agent()

    # Validation minimale
    assert "articles" in data, "Clé 'articles' manquante"
    assert data.get("nombre_articles") == len(data["articles"]), (
        f"nombre_articles ({data.get('nombre_articles')}) "
        f"!= len(articles) ({len(data['articles'])})"
    )
    for art in data["articles"]:
        assert art.get("image_url"), f"image_url null pour {art.get('id')}"

    output = os.path.abspath(OUTPUT_FILE)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    n = len(data["articles"])
    default_count = sum(1 for a in data["articles"] if DEFAULT_IMAGE in a["image_url"])
    extracted = n - default_count
    cats = ", ".join(data.get("categories", []))
    print(f"[Bankiba] ✓ {n} articles publiés | catégories: {cats}", flush=True)
    print(f"[Bankiba] ✓ Images: {extracted} extraites, {default_count} par défaut", flush=True)
    print(f"[Bankiba] ✓ Fichier écrit: {output}", flush=True)


if __name__ == "__main__":
    main()
