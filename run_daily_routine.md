# Bankiba Daily News Routine — Instructions pour Claude Code

## Objectif
Chaque jour, produire et publier `cemac_finance_news.json` sur la branche `main`
du dépôt `bankibafinancial-prog/bankiba-routine`.

## Prompt à exécuter (copier-coller dans Claude Code)

```
Tu gères une routine quotidienne pour l'application mobile Bankiba Technology
(société de vente d'actions et d'investissement sur les FCP - fonds communs
de placement). Chaque jour, tu dois produire et publier sur Google Drive un
flux d'actualités financières en FRANÇAIS, sous la forme d'un UNIQUE fichier
nommé exactement "cemac_finance_news.json" (jamais de copie, jamais de
versionnage type "(1)" ou "-copie").

IMAGE PAR DÉFAUT (à utiliser quand aucune image fiable n'est extraite) :
https://plus.unsplash.com/premium_photo-1691223733678-095fee90a0a7?fm=jpg&q=60&w=3000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8YXJ0aWNsZXxlbnwwfHwwfHx8MA%3D%3D

ÉTAPE 1 — RECHERCHE
Utilise WebSearch (français ET anglais) pour couvrir les actualités
financières récentes (24-48h, sinon les plus récentes disponibles) sur :
- La zone CEMAC (Cameroun, Gabon, Congo, Tchad, RCA, Guinée Équatoriale) :
  dette souveraine, BVMAC (bourse régionale), FCP et fonds d'investissement,
  banques, réglementation (COBAC, COSUMAF, BEAC, ANIF), macroéconomie.
- L'Afrique centrale/de l'Ouest élargie : actualités financières régionales
  à fort impact hors CEMAC (Nigeria, fintechs panafricaines comme
  Flutterwave, groupes comme Dangote, levées de fonds majeures, IPO, M&A).
Requêtes suggérées : "CEMAC actualité financière", "BVMAC bourse actualité",
"FCP fonds commun de placement CEMAC", "COSUMAF COBAC BEAC réglementation",
"Cameroun Gabon Congo Tchad dette obligataire", "Afrique centrale fintech
investissement", "Nigeria Afrique de l'Ouest finance actualité".
Sélectionne 8 à 12 articles pertinents et récents, de sources économiques
fiables (Agence Ecofin, Sika Finance, Investir au Cameroun, Financial Afrik,
Ecomatin, Jeune Afrique, Bloomberg, Reuters, allAfrica, Businessday,
Semafor, L'Economie, etc.). Pas de doublons. N'invente jamais un chiffre ou
une date que tu n'as pas trouvé.

ÉTAPE 2 — EXTRACTION DE L'IMAGE DE CHAQUE ARTICLE
Pour CHAQUE article retenu, récupère la page source (WebFetch) et essaie
d'en extraire une image représentative (og:image > twitter:image > première
image significative). L'URL doit être absolue et pointer vers un fichier
image direct. Si la récupération échoue (403, timeout, paywall, aucune
balise image), utilise l'IMAGE PAR DÉFAUT. Ne laisse jamais image_url à null.

ÉTAPE 3 — STRUCTURATION JSON
Produis un JSON valide respectant exactement ce schéma :
{
  "version_schema": "1.0",
  "application": "Bankiba Technology",
  "flux": "actualites_finance_cemac",
  "langue": "fr",
  "zone_couverte": "CEMAC + Afrique centrale et de l'Ouest elargie",
  "date_edition": "YYYY-MM-DD",
  "genere_le": "YYYY-MM-DDTHH:MM:SS+01:00",
  "nombre_articles": <nombre>,
  "categories": ["liste des catégories utilisées"],
  "articles": [
    {
      "id": "slug-unique-minuscules-tirets",
      "titre": "Titre en français",
      "categorie": "Dette souveraine | Dette privee | Bourse | FCP / Fonds d'investissement | Fintech | Reglementation | Banque | Macroeconomie",
      "pays": "Pays ou CEMAC ou Regional",
      "resume": "2-3 phrases factuelles en français",
      "source": "Nom du média",
      "url": "URL source",
      "date_publication": "YYYY-MM-DD ou null",
      "image_url": "URL absolue image (jamais null)"
    }
  ]
}

ÉTAPE 4 — PUBLICATION GIT
1. Écris le fichier cemac_finance_news.json à la racine du dépôt
   /home/user/bankiba-routine/cemac_finance_news.json
2. git add cemac_finance_news.json
3. git commit -m "routine: flux actualités CEMAC du YYYY-MM-DD"
4. git push -u origin main
5. Confirme que le push a réussi.
```

## URL d'accès API (après chaque exécution)

### Repo public — URL raw directe
```
https://raw.githubusercontent.com/bankibafinancial-prog/bankiba-routine/main/cemac_finance_news.json
```

### Repo privé — GitHub API avec token
```
GET https://api.github.com/repos/bankibafinancial-prog/bankiba-routine/contents/cemac_finance_news.json
Authorization: Bearer VOTRE_GITHUB_TOKEN
Accept: application/vnd.github.raw+json
```

### Exemple Flutter/Dart (app Bankiba)
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<Map<String, dynamic>> fetchCemacNews() async {
  final uri = Uri.parse(
    'https://api.github.com/repos/bankibafinancial-prog/bankiba-routine/contents/cemac_finance_news.json',
  );
  final response = await http.get(uri, headers: {
    'Authorization': 'Bearer $githubToken',
    'Accept': 'application/vnd.github.raw+json',
  });
  if (response.statusCode == 200) {
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
  throw Exception('Erreur ${response.statusCode}');
}
```

### Exemple React Native / JavaScript
```javascript
const fetchCemacNews = async () => {
  const res = await fetch(
    'https://api.github.com/repos/bankibafinancial-prog/bankiba-routine/contents/cemac_finance_news.json',
    {
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: 'application/vnd.github.raw+json',
      },
    }
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};
```
