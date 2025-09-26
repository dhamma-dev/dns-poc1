import subprocess
import re
import json
import os
import requests
from celery import Celery

# --- Configuration ---

# The agent needs to know where to connect for the Celery queue (Redis)
# and where to post results back to (the coordinator's API).
# We use environment variables for this.
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
COORDINATOR_URL = os.environ.get('COORDINATOR_URL', 'http://localhost:5000/api/v1/results')

# --- Celery App Initialization ---

# The first argument to Celery is the name of the current module.
# The `broker` and `backend` are set to our Redis server.
celery = Celery('tasks', broker=REDIS_URL, backend=REDIS_URL)


# --- Helper Functions (from MVP) ---

def send_results(results):
    """
    Sends the parsed results back to the coordinator's API.
    """
    try:
        response = requests.post(COORDINATOR_URL, json=results)
        response.raise_for_status()
        print(f"Successfully sent results to {COORDINATOR_URL}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending results to coordinator: {e}")
        return None

def parse_dig_output(output, domain, record_type):
    """
    Parses the raw text output from the dig command.
    """
    query_time_match = re.search(r';; Query time: (\d+) msec', output)
    status_match = re.search(r'status: (\w+),', output)
    answer_section_match = re.search(r';; ANSWER SECTION:\n(.*?)\n\n', output, re.DOTALL)

    records = []
    if answer_section_match:
        answer_section = answer_section_match.group(1)
        for line in answer_section.splitlines():
            if line.strip() and not line.startswith(';'):
                parts = re.split(r'\s+', line)
                if len(parts) >= 5:
                    records.append({
                        'name': parts[0],
                        'ttl': int(parts[1]),
                        'class': parts[2],
                        'type': parts[3],
                        'data': parts[4]
                    })
    return {
        'domain': domain,
        'record_type': record_type,
        'query_time_ms': int(query_time_match.group(1)) if query_time_match else None,
        'status': status_match.group(1) if status_match else 'UNKNOWN',
        'records': records
    }

# --- Celery Task Definition ---

@celery.task(name='tasks.run_dig_task')
def run_dig_task(domain, record_type, test_type):
    """
    This is the core Celery task the agent worker will execute.
    It runs `dig`, parses the output, and sends it back to the coordinator.
    """
    print(f"Received task: dig {domain} {record_type} (Test Type: {test_type})")

    command = ['dig']

    if test_type == 'trace':
        command.append('+trace')
        command.append(domain)
        # The specific record_type is not used in a trace command
    else: # Default to 'server' test
        command.extend([domain, record_type])

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        if test_type == 'trace':
            # For a trace, we will just store the raw output in a single record for now.
            # A more detailed parser could be a future enhancement.
            parsed_results = {
                'domain': domain,
                'record_type': 'TRACE',
                'status': 'COMPLETE',
                'records': [{'data': result.stdout, 'name': domain, 'ttl': 0, 'class': 'IN', 'type': 'TRACE'}]
            }
        else:
            parsed_results = parse_dig_output(result.stdout, domain, record_type)

        send_results(parsed_results)
        return parsed_results

    except subprocess.CalledProcessError as e:
        error_info = {'error': str(e), 'stdout': e.stdout, 'stderr': e.stderr}
        send_results(error_info)
        return error_info
    except FileNotFoundError:
        error_info = {'error': 'dig command not found in container.'}
        send_results(error_info)
        return error_info