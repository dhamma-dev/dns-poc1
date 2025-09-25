# dig-based DNS Monitoring Solution (Proof of Concept)

This project is a Proof of Concept (POC) for a DNS monitoring solution that uses the `dig` command-line utility to replicate the core functionality of a service like ThousandEyes.

## Architecture

The solution is composed of two main components for this MVP:

*   **Agent (`agent/`)**: A containerized Python script that executes `dig` commands against a specified domain and sends the parsed results to the Coordinator.
*   **Coordinator (`coordinator/`)**: A simple Python `http.server` that listens for incoming data from agents, logs the results to a file (`coordinator.log`), and sends a success response.

## Prerequisites

*   **Docker**: Required to build and run the containerized agent.
*   **Python 3**: Required to run the coordinator script.

## Setup & Running the MVP

Follow these steps to build the necessary components and run the end-to-end test.

### 1. Build the Agent Docker Image

First, build the Docker image for the agent. From the root of the repository, run:

```bash
sudo docker build -t dig-agent agent/
```

### 2. Start the Coordinator

Next, start the coordinator server. It will listen on port 5000 and log any received data to `coordinator.log` in the project root.

Open a terminal and run the following command from the project root:

```bash
python3 coordinator/main.py
```

Leave this terminal running. You should see a message indicating the server has started: `serving at port 5000`.

### 3. Run the Agent and Send Data

Now, open a **second terminal**. Run the agent container, instructing it to perform a `dig` on `google.com` and send the results to the coordinator.

The `--network="host"` flag is used to allow the Docker container to connect to the coordinator server running on `localhost:5000`.

```bash
sudo docker run --network="host" dig-agent google.com -c http://127.0.0.1:5000/api/v1/results
```

You should see a success message from the agent in your terminal:

```
Successfully sent results to http://127.0.0.1:5000/api/v1/results
{'message': 'Data received', 'status': 'success'}
```

### 4. Verify the Results

Finally, check the contents of the `coordinator.log` file in the project root. This file contains the data received and logged by the coordinator.

```bash
cat coordinator.log
```

You should see log entries detailing the data received from the agent, similar to this:

```
2025-09-25 11:15:00,123 - INFO - --- REQUEST RECEIVED ---
2025-09-25 11:15:00,123 - INFO - Received data from agent:
2025-09-25 11:15:00,123 - INFO - {
  "domain": "google.com",
  "record_type": "A",
  "query_time_ms": 10,
  "status": "NOERROR",
  "records": [
    {
      "name": "google.com.",
      "ttl": 250,
      "class": "IN",
      "type": "A",
      "data": "142.250.191.113"
    }
  ]
}
2025-09-25 11:15:00,123 - INFO - --- RESPONSE SENT ---
```

This confirms that the agent successfully performed the `dig` command and transmitted the results to the coordinator, completing the MVP test.