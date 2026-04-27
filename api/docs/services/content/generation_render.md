
Service de remplissage de templates `.odt` et `.docx` (publipostage programmatique).

Envoie un template contenant des placeholders, fournit un dictionnaire de données,
et récupère un fichier rempli dans le même format que l'entrée.

## Templates d'exemple

Pour démarrer rapidement, téléchargez un template de référence et son jeu de données :

- [**test_template.odt**](/docs-examples/generation-render/test_template.odt) — template ODT
  couvrant les 3 types de balises Relatorio (simple, conditionnelle `if`, itérative `for`)
- [**test_template.docx**](/docs-examples/generation-render/test_template.docx) — template DOCX
  couvrant les 3 mêmes constructions en syntaxe Jinja2 (placeholder, `{% if %}`, `{% for %}`)
- [**test_data.json**](/docs-examples/generation-render/test_data.json) — jeu de données
  commun aux deux templates :

```json
{
  "nom": "Dupont",
  "ville": "Nice",
  "is_admin": true,
  "items": ["dossier-001", "dossier-002", "dossier-003"]
}
```

## Flux d'utilisation

1. Upload du template via `POST /storage/upload` → récupération d'un `file_id`
2. Création de la tâche via `POST /v1/services/generation-render/tasks`
   avec le `file_id` et les données à injecter
3. Polling du résultat via `GET /v1/services/generation-render/tasks/{task_id}`
   OU réception d'un callback HTTP (si `callback.url` est fourni à la soumission)

Le format de sortie correspond au format d'entrée : un template `.odt` produit un
`.odt`, un template `.docx` produit un `.docx`. Le moteur de rendu est sélectionné
automatiquement à partir de l'extension du fichier uploadé.

## Syntaxe ODT (Relatorio)

Les templates `.odt` utilisent [Relatorio](https://relatorio.readthedocs.io/) (basé sur Genshi).

- **Placeholders simples** : `<variable>` (via Insert → Field → Placeholder → Text dans LibreOffice)
- **Conditionnel** : lien hypertexte `relatorio://if test="condition"` ... `relatorio:///if`
- **Boucle** : lien hypertexte `relatorio://for each="item in items"` ... `relatorio:///for`

## Syntaxe DOCX (Jinja2)

Les templates `.docx` utilisent [docxtpl](https://docxtpl.readthedocs.io/), qui s'appuie
sur la syntaxe [Jinja2](https://jinja.palletsprojects.com/). Les balises sont saisies
directement dans le document Word.

- **Placeholders simples** : `{{ variable }}`
- **Conditionnel** : `{% if condition %}` ... `{% endif %}`
- **Boucle** : `{% for item in items %}` ... `{% endfor %}`

Exemple de contenu pour le `test_template.docx` :

```jinja
Bonjour {{ nom }}, vous habitez à {{ ville }}.
{% if is_admin %}Vous êtes administrateur.{% endif %}
Liste des éléments :
{% for item in items %}- {{ item }}
{% endfor %}
```

## Body de la requête

| Champ | Type | Description |
|---|---|---|
| `body.file_id` | string | Identifiant du template uploadé via `/storage/upload` (`.odt` ou `.docx`) |
| `body.data` | object | Dictionnaire clé-valeur des variables à injecter |
| `callback` (optionnel) | object | Callback HTTP appelé à la fin du traitement |

### Exemple de requête

```bash
curl -u <client_id>:<secret> -X POST \
  https://<host>/v1/services/generation-render/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "file_id": "prisme/abc123/info_procureur.odt",
      "data": {
        "tribunal_judiciaire_competent": "Nice",
        "courriel_tribunal_judiciaire": "nice@tribunal-judiciaire.fr",
        "identite_complete_etranger": "Madame DOE JANE",
        "date_courrier": "15.04.2026"
      }
    },
    "callback": {
      "type": "http",
      "url": "http://n8n-webhook.<namespace-n8n>.svc.cluster.local/webhook/brio-webhook"
    }
  }'
```

## Réponse de la tâche terminée

Quand le polling retourne `status: "success"`, le champ `result` contient :

| Champ | Type | Description |
|---|---|---|
| `output_file_id` | string | Clé S3 du fichier rempli (`{source_path}/{task_id}/rendered_{filename}`) |
| `download_url` | string | URL pre-signed valide 24h pour télécharger le fichier rempli |
| `warnings` | string[] | Clés du template absentes de `data` (ex: `"La donnée pour 'ville' n'est pas définie"`) |

### Exemple de réponse

```json
{
  "status": "success",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "success",
    "result": {
      "output_file_id": "prisme/abc123/550e8400.../rendered_info_procureur.odt",
      "download_url": "https://brio-staging-api-data.s3.fr-par.scw.cloud/...?X-Amz-Signature=...",
      "warnings": []
    },
    "submission_date": "2026-04-15T10:30:00Z",
    "start_date": "2026-04-15T10:30:05Z",
    "end_date": "2026-04-15T10:30:45Z"
  }
}
```

## Gestion des clés manquantes

Si une clé du template n'est pas fournie dans `data`, le rendu continue et le
champ `warnings` liste les clés manquantes. La tâche passe quand même en
`success`.

## Limites

- Taille maximum du template : 25 MB (contrainte ingress + parser)
- Formats supportés : `.odt` (Relatorio) et `.docx` (Jinja2 via docxtpl)
- Les valeurs dans `data` peuvent être : `string`, `boolean`, `array`
