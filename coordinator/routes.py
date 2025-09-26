from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from .extensions import db, celery
from .models import TestResult, DNSRecord
import logging
import json

main_bp = Blueprint('main', __name__)

@celery.task(name='tasks.run_dig_task')
def run_dig_task(domain, record_type, test_type):
    # This is a placeholder signature.
    # The actual task logic will live in the agent's worker process.
    pass

@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main_bp.route('/submit', methods=['POST'])
def submit_test():
    domain = request.form.get('domain')
    record_type = request.form.get('record_type', 'A')
    test_type = request.form.get('test_type', 'server')

    if not domain:
        return "Error: Domain is required", 400

    logging.info(f"Dispatching task for domain: {domain}, type: {record_type}, test_type: {test_type}")
    run_dig_task.delay(domain, record_type, test_type)

    return redirect(url_for('main.index'))

@main_bp.route('/api/v1/results', methods=['POST'])
def receive_results():
    if not request.is_json:
        logging.error("Request was not JSON")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    logging.info("--- RESULT RECEIVED FROM AGENT ---")
    logging.info(json.dumps(data, indent=2))

    if data.get('error'):
        logging.error(f"Agent reported an error: {data['error']}")
        return jsonify({"status": "error", "message": "Agent error received"}), 400

    new_result = TestResult(
        domain=data.get('domain'),
        record_type=data.get('record_type'),
        query_time_ms=data.get('query_time_ms'),
        status=data.get('status')
    )

    if data.get('records'):
        for record_data in data['records']:
            new_record = DNSRecord(
                name=record_data.get('name'),
                ttl=record_data.get('ttl'),
                record_class=record_data.get('class'),
                record_type=record_data.get('type'),
                data=record_data.get('data'),
                test_result=new_result
            )
            db.session.add(new_record)

    db.session.add(new_result)
    db.session.commit()

    logging.info(f"Successfully saved test result for {data.get('domain')} to the database.")

    return jsonify({"status": "success", "message": "Data received and saved"}), 201

@main_bp.route('/results', methods=['GET'])
def list_results():
    results = TestResult.query.order_by(TestResult.created_at.desc()).all()
    return render_template('results.html', results=results)