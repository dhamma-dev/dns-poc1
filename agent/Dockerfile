# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install dnsutils for dig
RUN apt-get update && apt-get install -y dnsutils

# Set the working directory in the container
WORKDIR /app

# Copy the agent script into the container
COPY agent.py .

# Install Python dependencies for the agent
# requests is for posting results back to the coordinator
# celery and redis are for the worker queue
RUN pip install requests celery redis

# Define the entry point for the container.
# This command starts a Celery worker.
# -A agent: Specifies the application instance is in the 'agent.py' file.
# worker:  Starts the worker process.
# --loglevel=info: Sets the logging level.
ENTRYPOINT ["celery", "-A", "agent", "worker", "--loglevel=info"]