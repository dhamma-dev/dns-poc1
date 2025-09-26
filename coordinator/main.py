from flask import Flask, request, jsonify, render_template, redirect, url_for
from celery import Celery
import logging
import json

# --- App & Celery Configuration ---

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from models import db, TestResult, DNSRecord

# Initialize Flask App
app = Flask(__name__)

import os

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/digdug_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure Celery
# The broker URL points to the Redis server, configured via environment variables.
# This makes it easy to use with Docker Compose.
app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Create a Celery instance
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


# --- Celery Task Definition ---

@celery.task(name='tasks.run_dig_task')
def run_dig_task(domain, record_type, test_type):
    # This is a placeholder signature.
    # The actual task logic will live in the agent's worker process.
    # The coordinator only needs to know the task's name and signature to call it.
    pass


# --- Database Initialization ---
# Create tables if they don't exist
with app.app_context():
    db.create_all()


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
    test_type = request.form.get('test_type', 'server')

    if not domain:
        return "Error: Domain is required", 400

    logging.info(f"Dispatching task for domain: {domain}, type: {record_type}, test_type: {test_type}")

    # Send the task to the Celery queue.
    # The agent worker will pick this up.
    run_dig_task.delay(domain, record_type, test_type)

    return redirect(url_for('index'))

@app.route('/api/v1/results', methods=['POST'])
def receive_results():
    """
    API endpoint for agents to post back their results.
    This now saves the results to the database.
    """
    if not request.is_json:
        logging.error("Request was not JSON")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    logging.info("--- RESULT RECEIVED FROM AGENT ---")
    logging.info(json.dumps(data, indent=2))

    if data.get('error'):
        logging.error(f"Agent reported an error: {data['error']}")
        return jsonify({"status": "error", "message": "Agent error received"}), 400

    # Create a new TestResult object
    new_result = TestResult(
        domain=data.get('domain'),
        record_type=data.get('record_type'),
        query_time_ms=data.get('query_time_ms'),
        status=data.get('status')
    )

    # Create associated DNSRecord objects
    if data.get('records'):
        for record_data in data['records']:
            new_record = DNSRecord(
                name=record_data.get('name'),
                ttl=record_data.get('ttl'),
                record_class=record_data.get('class'),
                record_type=record_data.get('type'),
                data=record_data.get('data'),
                test_result=new_result  # Associate with the parent TestResult
            )
            db.session.add(new_record)

    db.session.add(new_result)
    db.session.commit()

    logging.info(f"Successfully saved test result for {data.get('domain')} to the database.")

    return jsonify({"status": "success", "message": "Data received and saved"}), 201

@app.route('/results', methods=['GET'])
def list_results():
    """
    Fetches all test results from the database and displays them.
    """
    results = TestResult.query.order_by(TestResult.created_at.desc()).all()
    return render_template('results.html', results=results)

if __name__ == '__main__':
    # This is for local development only.
    # In production, use a proper WSGI server like Gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)