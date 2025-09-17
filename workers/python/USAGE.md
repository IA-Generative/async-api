# Guide d'utilisation du Worker Python

## Structure du projet

```bash
workers/python/
├── async_worker/           # Package Python
│   ├── __init__.py        # Exports du package
│   └── worker.py          # Code principal du worker
├── demo.py                # Application de démonstration
├── test_worker.py         # Script de test
├── Dockerfile             # Configuration Docker
├── docker-compose.yml     # Stack complète avec RabbitMQ
├── Makefile              # Commandes utilitaires
├── pyproject.toml        # Configuration Python existante
├── setup.py              # Configuration du package
├── README.md             # Documentation du package
└── .dockerignore         # Fichiers exclus du build Docker
```

## 🚀 Démarrage rapide

### 1. Construction et lancement avec Docker Compose

```bash
# Lancer la stack complète (RabbitMQ + Worker)
make build
docker-compose up -d

# Ou directement
docker-compose up --build -d
```

### 2. Test du worker

```bash
# Installer les dépendances pour le script de test
uv add aio-pika

# Envoyer des messages de test
python test_worker.py
```

### 3. Monitoring

```bash
# Consulter les logs du worker
docker-compose logs -f python-worker

# Accéder à l'interface RabbitMQ
# http://localhost:15672 (admin/admin123)

# Vérifier le health check du worker
curl http://localhost:8000/
```

## 🛠️ Développement

### Installation en mode développement

```bash
# Installer le package en mode éditable
make install-dev

# Ou manuellement
pip install -e ".[dev]"
```

### Commandes Make disponibles

```bash
make help              # Affiche l'aide
make build             # Construit l'image Docker
make run               # Lance le conteneur
make run-detached      # Lance en arrière-plan
make stop              # Arrête le conteneur
make clean             # Nettoie containers et images
make logs              # Affiche les logs
make shell             # Ouvre un shell dans le conteneur
make test              # Lance les tests
make lint              # Vérifie le code
make format            # Formate le code
make health-check      # Teste le health check
```

## 📦 Utilisation du package async_worker

### Exemple de tâche asynchrone

```python
from async_worker import AsyncTaskInterface, IncomingMessage
import asyncio

class MyAsyncTask(AsyncTaskInterface):
    async def execute(self, incoming_message: IncomingMessage, progress):
        data = incoming_message.body
        task_id = incoming_message.task_id
        # Votre logique ici
        await asyncio.sleep(1)
        await progress(0.3)
        await asyncio.sleep(1)
        await progress(0.6)
        return {"result": "success", "processed_data": data}
```

### Configuration du runner

```python
from async_worker import AsyncWorkerRunner, Infinite, HealthCheckConfig

runner = AsyncWorkerRunner(
    amqp_url="amqp://user:pass@localhost:5672",
    amqp_in_queue="input_queue",
    amqp_out_queue="output_queue",
    task_provider=lambda: MyAsyncTask(),
    worker_mode=Infinite(concurrency=5),  # ou OnShot()
    health_check_config=HealthCheckConfig(host="0.0.0.0", port=8000)
)

await runner.start()
```

## 🔧 Configuration

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `BROKER_URL` | URL RabbitMQ (obligatoire) | - |
| `IN_QUEUE_NAME` | Queue d'entrée | `"in_queue_python"` |
| `OUT_QUEUE_NAME` | Queue de sortie | `"example_out_queue"` |
| `WORKER_CONCURRENCY` | Nombre de tâches concurrentes | `"5"` |

### Format des messages

#### Message d'entrée

```json
{
  "task_id": "uuid-string",
  "data": {
    "body": {
      "mustSucceed": true,
      "sleep": 5
    }
  }
}
```

#### Messages de sortie

**Démarrage**

```json
{
  "task_id": "uuid-string",
  "data": {
    "message_type": "started",
    "hostname": "container-hostname"
  }
}
```

**Progression**

```json
{
  "task_id": "uuid-string",
  "data": {
    "message_type": "progress",
    "progress": 0.5
  }
}
```

**Succès**

```json
{
  "task_id": "uuid-string",
  "data": {
    "message_type": "success",
    "response": {"result": "data"}
  }
}
```

**Échec**

```json
{
  "task_id": "uuid-string",
  "data": {
    "message_type": "failure",
    "error_message": "Description de l'erreur"
  }
}
```

## 🐳 Docker

### Build manuel

```bash
docker build -t python-worker .
```

### Run manuel

```bash
docker run -e BROKER_URL="amqp://localhost:5672" \
           -e IN_QUEUE_NAME="my_queue" \
           -e OUT_QUEUE_NAME="my_out_queue" \
           -e WORKER_CONCURRENCY="3" \
           -p 8000:8000 \
           python-worker
```

## 🧪 Tests

Le script `test_worker.py` permet d'envoyer des messages de test :

- **Test 1** : Tâche qui réussit avec progression
- **Test 2** : Tâche qui échoue pour tester la gestion d'erreur

Les résultats sont visibles dans les logs du worker et les messages de réponse sont envoyés sur la queue de sortie.

## 🔍 Troubleshooting

### Problèmes courants

1. **Worker ne démarre pas**
   - Vérifiez que `BROKER_URL` est définie
   - Vérifiez que RabbitMQ est accessible

2. **Messages non traités**
   - Vérifiez les queues dans l'interface RabbitMQ
   - Consultez les logs du worker

3. **Health check échoue**
   - Le worker expose un serveur HTTP sur le port 8000
   - Endpoint : `GET http://localhost:8000/`
