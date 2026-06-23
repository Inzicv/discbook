# DiscBook

DiscBook est un bot Python exécuté via GitHub Actions qui surveille les nouveautés EPUB francophones de Z-Library et publie automatiquement les nouveaux livres sur Discord.

Le projet utilise Firecrawl pour le scraping et un webhook Discord pour la diffusion.

---

# Fonctionnalités

- Recherche automatique des nouveaux EPUB en français.
- Exécution planifiée via GitHub Actions.
- Publication sur Discord sous forme d'embed.
- Gestion d'un historique des livres déjà publiés.
- Détection des doublons malgré plusieurs URLs ou plusieurs uploads d'une même œuvre.
- Mise à jour automatique de `seen_books.json`.

---

# Architecture

```
GitHub Actions
        │
        ▼
    scraper.py
        │
        ▼
    Firecrawl
        │
        ▼
    Z-Library
        │
        ▼
Détection des nouveautés
        │
        ▼
Webhook Discord
```

---

# Source surveillée

```
https://z-lib.fm/s/?yearFrom=2026&languages[]=french&extensions[]=EPUB&order=date
```

Le scraper utilise :

```python
max_age=0
```

afin de forcer Firecrawl à récupérer les données les plus récentes.

---

# Informations récupérées

Pour chaque livre :

- Titre
- Auteur
- Couverture
- Résumé
- Lien de téléchargement

---

# Publication Discord

Chaque nouveauté est envoyée sous forme d'embed :

```text
📚 Titre

✍ Auteur

Résumé

📥 Lien de téléchargement
```

avec la couverture du livre.

---

# Gestion des doublons

Z-Library peut contenir plusieurs entrées pour une même œuvre :

- plusieurs URLs ;
- plusieurs uploaders ;
- titres légèrement différents ;
- descriptions plus ou moins complètes.

Exemples :

```
God of Fury
Rina Kent
```

et

```
God of Fury: A Dark MM College Romance (Legacy of Gods Book 5)
Rina Kent
```

doivent être considérés comme le même livre.

DiscBook utilise :

- une normalisation des titres ;
- une normalisation des auteurs ;
- une comparaison par auteur ;
- la détection des numéros de tomes (`Tome 3`, `Book 5`, `#2`, etc.) ;
- un système de similarité pour éviter les faux doublons.

Ainsi :

### Même œuvre

```
God of Fury
God of Fury: A Dark MM College Romance (Legacy of Gods Book 5)
```

➡️ une seule publication.

### Livres différents

```
Les Somber Jann, Tome 2
Les Somber Jann, Tome 3
```

➡️ deux publications distinctes.

---

# Historique

Les livres déjà publiés sont stockés dans :

```
seen_books.json
```

Ce fichier est automatiquement :

1. mis à jour après chaque exécution ;
2. commit ;
3. poussé dans le dépôt GitHub.

Cela permet au bot de conserver son historique entre les exécutions.

---

# Technologies

- Python 3
- Firecrawl
- GitHub Actions
- Discord Webhooks
- JSON

---

# Dépôt

```
discbook
```

---

# Objectif

Recevoir automatiquement les dernières sorties EPUB francophones sur Discord sans republier plusieurs fois la même œuvre malgré les doublons présents sur Z-Library.
