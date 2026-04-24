
Ordre de mise à disposition progressive des services sur AsyncTaskAPI. Les services
sont déployés au fil des validations fonctionnelles et techniques.

## Vue d'ensemble

| # | Service | Identifiant API | Statut |
|---|---|---|---|
| 1 | Remplissage de template | `generation-render` | ✅ **Disponible** |
| 2 | Extraction de texte | `extract-text` | 🚧 À venir |
| 3 | Classification de documents | _à définir_ | 🚧 À venir |
| 4 | Extraction de données (entités nommées) | _à définir_ | 🚧 À venir |

---

## 1. ✅ Remplissage de template

**Statut : disponible en production.** **Identifiant API :** `generation-render`

Remplit un template `.odt` (format OpenDocument) à partir d'un dictionnaire de données,
via un moteur de publipostage programmatique (Relatorio / Genshi). Gère les placeholders
simples, les conditionnelles (`if`) et les boucles (`for`). Utile pour la génération
automatisée de courriers, convocations, attestations, etc.

→ [Voir la documentation complète]({generation_render_anchor})

---

## 2. 🚧 Extraction de texte

**Statut : à venir.** **Identifiant API :** `extract-text`

Extrait le texte brut depuis des documents numériques ou scannés. Prend en charge les PDF
(natifs comme scannés), les images (PNG, JPEG, TIFF, …) et s'appuie sur un pipeline OCR
pour les contenus non textuels.

Service fondamental : il alimente les traitements en aval (classification, extraction
d'entités). Un document scanné devient exploitable dès que son contenu textuel est
récupérable.

---

## 3. 🚧 Classification de documents

**Statut : à venir.**

Identifie automatiquement le type d'un document à partir de son contenu textuel (issu
par exemple du service `extract-text`). Permet de router un document vers le processus
métier adapté : pièce d'identité, jugement, formulaire administratif, courrier, etc.

Typiquement utilisé en amont d'une extraction d'entités pour appliquer le bon modèle
selon la catégorie détectée.

---

## 4. 🚧 Extraction de données (entités nommées)

**Statut : à venir.**

Extrait les entités nommées structurées présentes dans un texte : personnes, dates,
adresses, numéros de dossier, montants, identifiants, etc. Transforme un document brut
en données exploitables par les systèmes métier.

Conçu pour s'articuler avec les services amont (`extract-text` + classification) afin
de couvrir l'ensemble de la chaîne : document brut → texte → type → données structurées.

---

## Légende

- ✅ **Disponible** — service en production, consommable via `POST /v1/services/{service}/tasks`
- 🚧 **À venir** — service planifié, contrat d'API en cours de définition

> Pour toute demande d'accès anticipé ou de cadrage, contacter l'équipe BRIO.
