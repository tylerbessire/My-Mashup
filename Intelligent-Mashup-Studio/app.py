import os
import uuid
from threading import Thread
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from tasks import create_mashup_task, revise_mashup_task

app = Flask(__name__)
CORS(app) # Allow cross-origin requests for our frontend

# In-memory storage for job statuses. For production, use Redis or a database.
jobs = {}

# Ensure necessary directories exist
os.makedirs("workspace", exist_ok=True)
os.makedirs("workspace/audio_sources", exist_ok=True)
os.makedirs("workspace/mashups", exist_ok=True)
os.makedirs("workspace/stems", exist_ok=True)

@app.route('/api/mashup/create', methods=['POST'])
def create_mashup():
    data = request.get_json()
    if not data or 'songs' not in data or len(data['songs']) < 2:
        return jsonify({"error": "Invalid request. Please provide at least two songs."}), 400

    job_id = f"mashup_job_{uuid.uuid4()}"
    jobs[job_id] = {"status": "pending", "progress": "queued"}
    
    # Run the long-running task in a background thread
    thread = Thread(target=create_mashup_task, args=(job_id, data['songs'], jobs))
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "pending",
        "message": "Mashup creation initiated. Use job_id to check status."
    }), 202

@app.route('/api/mashup/status/<job_id>', methods=['GET'])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)

@app.route('/api/mashup/revise', methods=['POST'])
def revise_mashup():
    data = request.get_json()
    if not data or 'mashup_id' not in data or 'current_recipe' not in data or 'user_command' not in data:
        return jsonify({"error": "Invalid revision request. Missing required fields."}), 400

    job_id = f"mashup_job_{uuid.uuid4()}"
    jobs[job_id] = {"status": "pending", "progress": "queued for revision"}
    
    thread = Thread(target=revise_mashup_task, args=(job_id, data, jobs))
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "pending",
        "message": "Mashup revision initiated. Use new job_id to check status."
    }), 202

@app.route('/api/mashup/audio/<filename>', methods=['GET'])
def get_audio(filename):
    directory = os.path.join(os.getcwd(), "workspace/mashups")
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
