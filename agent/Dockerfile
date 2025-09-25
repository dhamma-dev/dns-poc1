# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install dnsutils for dig and requests for sending data
RUN apt-get update && apt-get install -y dnsutils && pip install requests

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY agent.py .

# Define the entry point for the container.
ENTRYPOINT ["python", "./agent.py"]

# Default command
CMD ["google.com"]