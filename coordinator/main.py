from flask import Flask, request, jsonify, render_template, redirect, url_for
from celery import Celery
import logging

# --- App & Celery Configuration ---

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask App
app = Flask(__name__)

# Configure Celery
# The broker URL points to the Redis server.
# The backend is also Redis, used to store task results.
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Create a Celery instance
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


# --- Celery Task Definition ---

@celery.task(name='tasks.run_dig_task')
def run_dig_task(domain, record_type, target_server=None):
    # This is a placeholder signature.
    # The actual task logic will live in the agent's worker process.
    # The coordinator only needs to know the task's name and signature to call it.
    pass


# --- Flask Routes ---

@app.route('/', methods=['GET'])
def index():
    """Serves the main page with the test submission form."""
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_test():
    """
    Handles test submission from the UI.
    Dispatches a Celery task for the agent to execute.
    """
    domain = request.form.get('domain')
    record_type = request.form.get('record_type', 'A')

    if not domain:
        return "Error: Domain is required", 400

    logging.info(f"Dispatching task for domain: {domain}, type: {record_type}")

    # Send the task to the Celery queue.
    # The agent worker will pick this up.
    run_dig_task.delay(domain, record_type)

    return redirect(url_for('index'))

@app.route('/api/v1/results', methods=['POST'])
def receive_results():
    """
    API endpoint for agents to post back their results.
    """
    if not request.is_json:
        logging.error("Request was not JSON")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    logging.info("--- RESULT RECEIVED FROM AGENT ---")
    logging.info(json.dumps(data, indent=2))

    return jsonify({"status": "success", "message": "Data received"}), 201

if __name__ == '__main__':
    # This is for local development only.
    # In production, use a proper WSGI server like Gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)