# dig-based DNS Monitoring Solution (Proof of Concept)

This project is a Proof of Concept (POC) for a DNS monitoring solution that uses the `dig` command-line utility to replicate the core functionality of a service like ThousandEyes.

## Architecture (Phase 2)

The architecture has evolved to support dynamic test scheduling:

*   **Coordinator (`coordinator/`)**: A Flask web application that serves a UI for scheduling tests. It uses Celery to dispatch test jobs to a Redis message queue.
*   **Agent (`agent/`)**: A containerized Celery worker that listens for jobs on the Redis queue, executes `dig` commands, and posts the results back to the Coordinator's API.
*   **Redis**: Acts as the message broker between the Coordinator and the Agent(s).

## Prerequisites

*   **Docker**: Required to build and run the containerized agent.
*   **Python 3**: Required to run the coordinator script.
*   **Redis**: Required for the Celery message queue. You can install it via a package manager (e.g., `sudo apt-get install redis-server` or `brew install redis`).

## Setup & Running Phase 2

Follow these steps to run the complete Phase 2 stack.

### 1. Start Redis

First, ensure your Redis server is running. If you just installed it, it may have started automatically. You can check its status or start it manually.

```bash
# (On most systems)
sudo systemctl start redis-server

# Or run it directly
redis-server
```

Leave this terminal running.

### 2. Install Coordinator Dependencies

In a **new terminal**, navigate to the project root and install the Python dependencies for the coordinator.

```bash
pip install -r coordinator/requirements.txt
```

### 3. Start the Coordinator

In the same terminal, start the Flask coordinator application.

```bash
python3 coordinator/main.py
```

Leave this terminal running. It will serve the web UI and dispatch tasks.

### 4. Build and Run the Agent Worker

Open a **third terminal**. First, build the new agent Docker image.

```bash
sudo docker build -t dig-agent-worker agent/
```

Next, run the agent worker container. It needs to connect to both Redis and the coordinator on your host machine.

**Important:** The command to run the agent depends on your operating system.

**On Docker Desktop (macOS or Windows):**

Use `host.docker.internal` to connect to services on your host.

```bash
sudo docker run \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e COORDINATOR_URL=http://host.docker.internal:5000/api/v1/results \
  dig-agent-worker
```

**On Linux:**

Use `--network="host"` to share the host's network.

```bash
sudo docker run --network="host" \
  -e REDIS_URL=redis://localhost:6379/0 \
  -e COORDINATOR_URL=http://localhost:5000/api/v1/results \
  dig-agent-worker
```

Leave this terminal running. You should see Celery startup logs, and it will end with "celery@<hostname>: Ready".

### 5. Schedule a Test via the UI

Open your web browser and navigate to:

[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

You should see a simple form.
1.  Enter a domain (e.g., `github.com`).
2.  Select a record type.
3.  Click "Run Test".

### 6. Verify the Results

1.  **Agent Terminal**: You should see a log message indicating the agent received and executed the task (e.g., `Received task: dig github.com A`).
2.  **Coordinator Terminal**: You should see a log message showing the results posted back from the agent (e.g., `--- RESULT RECEIVED FROM AGENT ---`).

This confirms the full workflow: the UI dispatches a task via Celery, the agent receives and executes it, and the results are sent back to the coordinator.