import copy
import random
import os
from flask import Flask, render_template, url_for, make_response, request, jsonify
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from datetime import datetime
from flask_weasyprint import HTML, render_pdf
from flask_caching import Cache
import pdfkit
from werkzeug.utils import secure_filename

import asyncio
from pyppeteer import launch

from my_ai_recruiter import SearchingAgent
from recruiter_advisor import AdvisorAgent
from recruiter_cv_writer import CVWriterAgent




    

app = Flask(__name__, template_folder='templates', static_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'cache'
cache = Cache(app)

app_agents = {}

UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
JOB_DIR = os.path.join(UPLOAD_FOLDER, 'job_description')
CV_DIR = os.path.join(UPLOAD_FOLDER, 'cvs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(JOB_DIR, exist_ok=True)
os.makedirs(CV_DIR, exist_ok=True)

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

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/update_cv', methods=['POST'])
def update_cv():
    updates = request.form
    if not updates:
        return jsonify({'error': 'No updates were provided.'}), 400

    # Process updates (e.g., save to a file, database, or pass to another agent)
    update_cv_text = ''
    for key, exp in updates.items():
        skill = key.replace('updates[', '').replace(']', '')
        update_cv_text += f"{skill}: {exp}\n"
    
    app_agents['advisor_agent'].cv += update_cv_text

    print(app_agents['advisor_agent'].cv)

    candidate_advice = app_agents['advisor_agent'].advise_candidate()

    candidate_appraisal = copy.deepcopy(app_agents['searching_agent'].candidates[0])

    candidate_appraisal['skills'].update(candidate_advice['skills'])

    # Provide feedback to the candidate or redirect
    return render_template('feedback_template.html', candidate=candidate_appraisal)



@app.route('/upload', methods=['POST'])
def upload():
    job_file = request.files.get('job_description')
    if job_file:
        clear_directory(JOB_DIR)
        job_path = os.path.join(JOB_DIR, secure_filename(job_file.filename))
        job_file.save(job_path)
    else:
        return jsonify({'error': 'Job description file is required.'}), 400


    cv_file = request.files.get('cv_file')
    if cv_file:
        clear_directory(CV_DIR)
        cv_path = os.path.join(CV_DIR, secure_filename(cv_file.filename))
        cv_file.save(cv_path)

    else:
        return jsonify({'error': 'At least one CV file is required.'}), 400
    
    job_content = open(job_path, 'r').read()
    cv_content = open(cv_path, 'r').read()

    # Use caching for candidate appraisal and advice
    cache_key = f"appraisal_{hash(job_content)}_{hash(cv_content)}"
    cached_data = cache.get(cache_key)

    if cached_data:
        print("Using cached candidate appraisal and advice")
        candidate_appraisal, candidate_advice = cached_data
    else:
        print("Generating candidate appraisal and advice")
        # Candidate appraisal
        searching_agent = SearchingAgent(
            job_description=job_content,
            cv_dir=CV_DIR,
            n_candidates=1,
            min_suitability_score=8,
            suitability_threshold=0,
            most_important_skills='auto'
        )
        searching_agent.appraise_candidates()
        app_agents['searching_agent'] = searching_agent
        candidate_appraisal = copy.deepcopy(searching_agent.candidates[0])

        # Candidate advice
        advisor_agent = AdvisorAgent(
            job_description=job_content,
            cv=cv_content,
            most_important_skills=searching_agent.most_important_skills,
            recruiter_appraisal_data=candidate_appraisal
        )
        candidate_advice = advisor_agent.advise_candidate()
        app_agents['advisor_agent'] = advisor_agent
        candidate_appraisal['skills'].update(candidate_advice['skills'])

        # Store in cache
        cache.set(cache_key, (candidate_appraisal, candidate_advice), timeout=3600)


    return render_template('feedback_template.html', candidate=candidate_appraisal)




@app.route('/generate_cv', methods=['POST'])
def generated_cv():

    writer_agent = CVWriterAgent(
        job_description=app_agents['advisor_agent'].job_description,
        cv=app_agents['advisor_agent'].cv,
        most_important_skills=app_agents['advisor_agent'].most_important_skills
    )

    cv_data = writer_agent.write_cv()
    

    # cv_data = get_cv_data()

    return render_template('cv_template_1.html', profile=cv_data)



if __name__ == '__main__':
    app.run(debug=True)