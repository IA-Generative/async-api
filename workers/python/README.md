# Async Worker Package

Un package Python pour créer des workers asynchrones qui traitent des tâches à partir de queues RabbitMQ.

## Fonctionnalités

- Support des tâches synchrones et asynchrones
- Gestion automatique des connexions RabbitMQ avec reconnexion
- Health check HTTP intégré
- Gestion des signaux de shutdown gracieux
- Support du mode one-shot et infinite avec concurrence configurable
- Logging structuré avec callbacks de progression

## Installation

Via `pip`

```bash
pip install mic-worker
```

Via `uv`

```bash
uv add mic-worker
```

## Utilisation

### Exemple de tâche asynchrone

```python
from async_worker import AsyncTaskInterface, IncomingMessage
import asyncio

class MyAsyncTask(AsyncTaskInterface):
    async def execute(self, incoming_message: IncomingMessage, progress):
        # Votre logique de traitement ici
        await asyncio.sleep(1)
        await progress(0.5)  # Reporter le progrès
        await asyncio.sleep(1)
        return {"result": "success"}
```

### Exemple de tâche synchrone

```python
from async_worker import SyncTaskInterface, IncomingMessage

class MySyncTask(SyncTaskInterface):
    def execute(self, incoming_message: IncomingMessage, progress):
        # Votre logique de traitement ici
        time.sleep(1)
        progress(0.5)  # Reporter le progrès
        time.sleep(1)
        return {"result": "success"}
```

### Configuration du runner

```python
from async_worker import AsyncWorkerRunner, Infinite, HealthCheckConfig

runner = AsyncWorkerRunner(
    amqp_url="amqp://localhost:5672",
    amqp_in_queue="input_queue",
    amqp_out_queue="output_queue",
    task_provider=lambda: MyAsyncTask(),
    worker_mode=Infinite(concurrency=5),
    health_check_config=HealthCheckConfig(host="0.0.0.0", port=8000)
)

await runner.start()
```

## Intégration conteneurisé

### Construction de l'image

```bash
docker build -t python-worker .
```

### Lancement du conteneur

```bash
docker run -e BROKER_URL="amqp://rabbitmq:5672" \
           -e IN_QUEUE_NAME="my_input_queue" \
           -e OUT_QUEUE_NAME="my_output_queue" \
           -e WORKER_CONCURRENCY="3" \
           -p 8000:8000 \
           python-worker
```

## Variables d'environnement

- `BROKER_URL`: URL de connexion RabbitMQ (obligatoire)
- `IN_QUEUE_NAME`: Nom de la queue d'entrée (défaut: "in_queue_python")
- `OUT_QUEUE_NAME`: Nom de la queue de sortie (défaut: "example_out_queue")
- `WORKER_CONCURRENCY`: Nombre de tâches concurrentes (défaut: "5")
