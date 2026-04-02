const amqp = require('amqplib');
const http = require('http');
const os = require('os');

//------------------------
// CONFIGURATION
//------------------------
const BROKER_URL = process.env.BROKER_URL || 'amqp://localhost';
const LISTENER_COUNT = Number(process.env.LISTENER_COUNT) || 5;

const IN_QUEUE_NAME = process.env.IN_QUEUE_NAME || 'example';
const OUT_QUEUE_NAME = process.env.OUT_QUEUE_NAME || 'example_out';
const ENABLE_HEALTH_CHECK_SERVER = process.env.CONSUMER_ENABLE_HEALTH_CHECK_SERVER === 'true' || false; // Default to false if not set
const HEALTH_CHECK_PORT = Number(process.env.CONSUMER_HEALTH_CHECK_PORT) || 8080;
const HEALTH_CHECK_HOST = process.env.CONSUMER_HEALTH_CHECK_HOST || '0.0.0.0';

//------------------------
// FRAMEWORK
//------------------------


class HealthCheckServer {
    constructor(port, host, taskManager) {
        this.port = port;
        this.host = host
        this.taskManager = taskManager;
        this.server = null;
    }

    async start() {
        return new Promise((resolve, reject) => {
            this.server = http.createServer((req, res) => {
                let statusCode = 200;

                try {
                    if (req.url === '/health' && req.method === 'GET') {
                        const response = {
                            status: 'ok',
                            timestamp: new Date().toISOString(),
                            hostname: os.hostname()
                        };
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify(response));
                    } else if (req.url === '/ready' && req.method === 'GET') {
                        const response = {
                            status: 'ready',
                            timestamp: new Date().toISOString(),
                            hostname: os.hostname(),
                            broker_connected: this.taskManager ? !this.taskManager.isShuttingDown : false
                        };
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify(response));
                    } else {
                        statusCode = 404;
                        res.writeHead(404, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'Not Found' }));
                    }
                } finally {
                    console.log(`[HealthCheck] ${req.method} ${req.url} ${statusCode} - ${req.headers['user-agent'] || 'Unknown'}`);
                }
            });
            this.server.on('clientError', (err, socket) => {
                console.error('[HealthCheck] Client error:', err.message);
                socket.end('HTTP/1.1 400 Bad Request\r\n\r\n');
            });

            this.server.listen(this.port, this.host, (err) => {
                if (err) {
                    reject(err);
                } else {
                    console.log(`[HealthCheck] Server running at http://${this.host}:${this.port}/`);
                    resolve();
                }
            });
        });
    }

    async stop() {
        if (this.server) {
            return new Promise((resolve) => {
                this.server.close(() => {
                    console.log('[HealthCheck] Stop...');
                    resolve();
                });
            });
        }
    }
}

// Utilitaire d'envoie de message (Started/End)
class MessageSender {
    constructor(brokerUrl, outQueue) {
        this.brokerUrl = brokerUrl;
        this.outQueue = outQueue;
    }

    async _sendMessage(message) {
        const connection = await amqp.connect(this.brokerUrl);

        const channel = await connection.createChannel();
        await channel.assertQueue(this.outQueue, { durable: true });

        channel.sendToQueue(this.outQueue, Buffer.from(JSON.stringify(message)), {
            persistent: true,
        });

        console.log("Message envoyé:", message);
        await channel.close();
        await connection.close();
    }

    async sendStartMessage(task_id) {
        await this._sendMessage({
            task_id: task_id,
            data: {
                message_type: "started",
                hostname: os.hostname()
            }
        })
    }

    async sendProgressMessage(task_id, progress) {
        await this._sendMessage({
            task_id: task_id,
            data: {
                message_type: "progress",
                progress: progress
            }
        })
    }

    async sendSuccessMessage(task_id, result) {
        await this._sendMessage({
            task_id: task_id,
            data: {
                message_type: "success",
                response: result
            }
        })
    }

    async sendFailureMessage(task_id, cause) {
        await this._sendMessage({
            task_id: task_id,
            data: {
                message_type: "failure",
                error_message: cause
            }
        })
    }
}

// Consumer et exécution des tâches
class TaskManager {
    constructor(brokerUrl,inQueue, outQueue, parallelism, taskFactory, enableHealthCheckServer, healthCheckPort, healthCheckHost) {
        this.brokerUrl = brokerUrl;
        this.inQueue = inQueue;
        this.outQueue = outQueue;
        this.parallelism = parallelism;
        this.taskFactory = taskFactory;
        this.enableHealthCheckServer = enableHealthCheckServer;
        this.healthCheckPort = healthCheckPort;
        this.healthCheckHost = healthCheckHost;
        this.healthCheckServer = null;
        // Etat interne
        this.channels = [];
        this.inFlightMessages = new Map(); // Map(channel -> msg)
        this.isShuttingDown = false;
        this.messageSender = new MessageSender(brokerUrl, outQueue);
    }

    async start() {
        let connection = null;
        while (true) {
            try {
                connection = await amqp.connect(this.brokerUrl);
                break;
            } catch (error) {
                console.log("[TaskManager] Connection error, retry in 2s.", error.message);
                await sleepMs(2000)
            }
        }
        if (this.enableHealthCheckServer) {
            try {
                this.healthCheckServer = new HealthCheckServer(this.healthCheckPort, this.healthCheckHost, this);
                await this.healthCheckServer.start();
            } catch (err) {
                console.error('[HealthCheck] Erreur de démarrage du serveur de santé', err);
                process.exit(1);
            }
        }
        // Gestion SIGTERM
        process.on('SIGTERM', async () => {
        await this.shutdown(connection);
        });
        process.on('SIGINT', async () => {
            await this.shutdown(connection);
        });


        for (let channelIndex = 0; channelIndex < this.parallelism; channelIndex++) {
            const channel = await connection.createChannel();
            this.channels.push(channel);

            await channel.assertQueue(this.inQueue, { durable: true });
            channel.prefetch(1);

            console.log(`[Listener ${channelIndex}] En attente de messages...`);

            channel.consume(
                this.inQueue,
                async (msg) => { this.onMessage(channelIndex,msg) },
                { noAck: false }
            );
        }
    }


    async onMessage(channelIndex,msg) {
        let channel = this.channels[channelIndex];
        this.inFlightMessages.set(channel, msg); // suivi du msg en cours

        const content = msg.content.toString();
        console.log(`[Listener ${channelIndex}] Reçu : ${content}`);
        const submissionMessage = this.parseSubmissionMessage(content);

        try {
            if (submissionMessage) {
                console.log(`[Listener ${channelIndex}] Submission : `,submissionMessage);
                try {
                    await this.messageSender.sendStartMessage(submissionMessage.task_id);
                    let task = this.taskFactory();
                    let result = await task.run(submissionMessage.task_id,submissionMessage.data.body,(p) => this.messageSender.sendProgressMessage(submissionMessage.task_id,p));
                    await this.messageSender.sendSuccessMessage(submissionMessage.task_id,result);
                } catch (err) {
                    await this.messageSender.sendFailureMessage(submissionMessage.task_id, err.message || String(err));
                }
            } else {
                console.error(`[Listener ${channelIndex}] Message invalide : ${content}`);
            }
        } catch (err) {
            console.error(`[Listener ${channelIndex}] Erreur :`, err);
        } finally {
            // Dans tous les cas on ACK!
            channel.ack(msg);
            this.inFlightMessages.delete(channel);
        }
        if (this.oneShot) {
            // Sigterm par défaut
            process.kill(process.pid)
        }
    }

    parseSubmissionMessage(content) {
        try {
            let json = JSON.parse(content);
            if (json.task_id && json.data && json.data.message_type && json.data.body) {
                return json;
            } else {
                return null;
            }
        } catch (err) {
            return null;
        }
    }

    async shutdown(connection) {
        // Parfois le signal arrive 2 fois.
        if (this.isShuttingDown) {
            return;
        }
        console.log('SIGTERM reçu. Nettoyage en cours...');
        this.isShuttingDown=true;

        // Arrêt du serveur de santé
        if (this.healthCheckServer) {
            try {
                await this.healthCheckServer.stop();
            } catch (err) {
                console.error('[!] Échec d\'arrêt du serveur de santé', err);
            }
        }

        // Arret des channels sans message en cours.
        // On ne veut pas qu'un channel en attente
        // puisse capter un message lors de l'arret
        // d'un autre listener (requeue)
        for (const channelIndex in this.channels) {
            let channel = this.channels[channelIndex];
            const msg = this.inFlightMessages.get(channel);
            if (!msg) {
                try {
                    console.log(`Fermeture du channel ${channelIndex}`);
                    await channel.close();
                } catch (err) {
                    console.error(`[!] Échec de fermeture du channel ${channelIndex}`, err);
                }
            }
        }
        // Arret des channels en cours de traitement
        for (const channelIndex in this.channels) {
            let channel = this.channels[channelIndex];
            const msg = this.inFlightMessages.get(channel);
            if (msg) {
                console.log(`Message en cours sur le channel ${channelIndex}, nack et requeue`);
                try {
                    channel.nack(msg, false, true); // requeue = true
                } catch (err) {
                    console.error(`[!] Échec du nack sur le channel ${channelIndex}`, err);
                }

                try {
                    await channel.close();
                } catch (err) {
                    console.error(`[!] Échec de fermeture du channel ${channelIndex}`, err);
                }
            }
        }

        try {
            await connection.close();
            console.log('[✓] Connexion RabbitMQ fermée.');
        } catch (err) {
            console.error('[!] Échec fermeture connexion', err);
        }
        process.exit(0);
    }
}

function sleepMs(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


//------------------------
// IMPLEMENTATION DE LA TACHE
//------------------------
class MyTask {
    constructor(){}
    async run(task_id,{ sleep, mustSucceed }, progressCallback) {
        console.log("MyTask: "+task_id)
        if (mustSucceed) {
            for (var i = 0; i < sleep; i++) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                await progressCallback(100*i/sleep);
            }
            return { hello: "world" }
        } else {
            throw "Argh!"
        }
    }
}

//------------------------
// EXECUTION
//------------------------
let taskManager = new TaskManager(
    BROKER_URL,
    IN_QUEUE_NAME,
    OUT_QUEUE_NAME,
    LISTENER_COUNT,
    () => new MyTask(),
    ENABLE_HEALTH_CHECK_SERVER,
    HEALTH_CHECK_PORT,
    HEALTH_CHECK_HOST
);

taskManager.start().catch((err) => {
    console.error('[!] Erreur de démarrage', err);
    process.exit(1);
});

/* exemple de message:
{
  "task_id": "089373b8-1691-4462-8f78-25e3af1a1c6b",
  "data": { "message_type": "submission", "body": { "sleep": 10, "mustSucceed": true} }
}
*/
