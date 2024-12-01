import json
from flask import Flask, request, jsonify, render_template, send_file, abort

import os
from werkzeug.utils import secure_filename
from pathlib import Path
from agents import SearchingAgent  # Import your AI agent class

from . import recruiter_bp

app = Flask(__name__)

# Define upload paths specific to the candidate blueprint
UPLOAD_FOLDER = os.path.join('candidate', 'uploads')
CV_DIR = os.path.join(UPLOAD_FOLDER, 'cv')  # Candidate's CV upload folder
JOB_DIR = os.path.join(UPLOAD_FOLDER, 'jd')  # Candidate's CV upload folder

# Ensure the directory exists
os.makedirs(CV_DIR, exist_ok=True)
os.makedirs(JOB_DIR, exist_ok=True)

# Function to clear directory
def clear_directory(directory_path):
    if os.path.exists(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                # elif os.path.isdir(file_path):
                #     os.rmdir(file_path)  # Optional: if you want to delete subdirectories as well
            except Exception as e:
                print(f"Error clearing directory {directory_path}: {e}")



@recruiter_bp.route('/')
def home():
    print(99999999999999999999999999999999999)
    return render_template('r_index.html')


@recruiter_bp.route('/download_cv/<filename>')
def download_cv(filename):
    print(filename)
    # Check if the file exists
    if not os.path.exists(filename):
        abort(404)  # Return a 404 error if the file does not exist

    # Serve the file using send_file
    return send_file(filename, as_attachment=True)

@recruiter_bp.route('/process', methods=['POST'])
def process_files():
    # Job description
    job_file = request.files['job_description']
    if job_file:
        clear_directory(JOB_DIR)
        job_path = os.path.join(JOB_DIR, secure_filename(job_file.filename))
        job_file.save(job_path)
    else:
        return jsonify({'error': 'Job description file is required.'}), 400

    # CVs
    cv_files = request.files.getlist('cvs')
    if not cv_files:
        return jsonify({'error': 'At least one CV file is required.'}), 400
    
    clear_directory(CV_DIR)
    for cv_file in cv_files:
        cv_file.save(os.path.join(CV_DIR, secure_filename(cv_file.filename)))

    # Parameters
    try:
        n_candidates = int(request.form.get('n_candidates', 3))
        min_suitability_score = int(request.form.get('min_suitability_score', 8))
        suitability_threshold = float(request.form.get('suitability_threshold', 0.7))
    except ValueError:
        return jsonify({'error': 'Invalid input for parameters.'}), 400

    # Optional skills
    skills = request.form.getlist('skills')
    skills = [skill.strip() for skill in skills if skill.strip() != '']
    if not skills:
        skills = 'auto'  # Fallback to 'auto' if no valid skills are provided

    # Process with SearchingAgent
    agent = SearchingAgent(
        job_description=open(job_path, 'r').read(),
        cv_dir=CV_DIR,
        n_candidates=n_candidates,
        min_suitability_score=min_suitability_score,
        suitability_threshold=suitability_threshold,
        most_important_skills=skills
    )

    agent.appraise_candidates()
    agent.select_candidates()

    recruiter_bp.agent_store.recruiter_agents['searching_agents'] = agent

    # Separate selected and unselected candidates
    selected = [cand for cand in agent.candidates if cand['selected']]
    unselected = [cand for cand in agent.candidates if not cand['selected']]

    # with open("candidate_data.json", "r") as cdf:
    #     candidates = json.load(cdf)
    # print(candidates[0])

    # selected = [cand for cand in candidates if cand['selected']]
    # unselected = [cand for cand in candidates if not cand['selected']]

    # Sort candidates by their overall suitability score in descending order
    selected_sorted = sorted(selected, key=lambda cand: cand['overall_score'], reverse=True)
    unselected_sorted = sorted(unselected, key=lambda cand: cand['overall_score'], reverse=True)

    selected_top_n = selected_sorted[:n_candidates] 
    unselected_top_n = selected_sorted[n_candidates:] + unselected_sorted

    # return jsonify({'selected_candidates': selected_top_n, 'unselected_candidates': unselected_top_n})
    return render_template('output.html', selected_candidates=selected_top_n, unselected_candidates=unselected_top_n)
