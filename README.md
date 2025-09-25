# dig-based DNS Monitoring Solution (Proof of Concept)

This project is a Proof of Concept (POC) for a DNS monitoring solution that uses the `dig` command-line utility to replicate the core functionality of a service like ThousandEyes.

## Architecture (Phase 2 - Containerized)

The entire application stack is managed by `docker-compose`, which orchestrates the following services:

*   **Coordinator**: A containerized Flask web application that serves a UI for scheduling tests. It uses Celery to dispatch test jobs.
*   **Agent**: A containerized Celery worker that listens for jobs on the Redis queue, executes `dig` commands, and posts the results back to the Coordinator's API.
*   **Redis**: A container running Redis, which acts as the message broker between the Coordinator and the Agent(s).

## Prerequisites

*   **Docker**
*   **Docker Compose**

## Running the Application

With Docker and Docker Compose, running the entire application stack is as simple as a single command.

### 1. Build and Run the Services

From the root of the repository, run:

```bash
docker-compose up --build
```

This command will:
1.  Build the Docker images for the `coordinator` and `agent` services.
2.  Start containers for `redis`, `coordinator`, and `agent`.
3.  Stream the logs from all services to your terminal.

You will see logs from all three services. The `agent` service will eventually show a "Ready" status, indicating it is waiting for tasks.

### 2. Schedule a Test via the UI

Open your web browser and navigate to:

[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

You should see a simple form.
1.  Enter a domain (e.g., `github.com`).
2.  Select a record type.
3.  Click "Run Test".

### 3. Verify the Results

Check the logs in your terminal where `docker-compose` is running. You should see:
1.  A log from the `coordinator` service indicating a task was dispatched.
2.  A log from the `agent` service showing it received the task and is running the `dig` command.
3.  A final log from the `coordinator` service showing the results posted back from the agent (e.g., `--- RESULT RECEIVED FROM AGENT ---`).

This confirms that the fully containerized application is working correctly.

### 4. Stopping the Application

To stop all the services, press `Ctrl+C` in the terminal where `docker-compose` is running. To remove the containers, you can run:

```bash
docker-compose down
```