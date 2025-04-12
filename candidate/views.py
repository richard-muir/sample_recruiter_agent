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
import markdown
from markupsafe import Markup

import asyncio
from pyppeteer import launch

from agents.recruiter_searching_agent import SearchingAgent
from agents.recruiter_advisor_agent import AdvisorAgent
from agents.recruiter_cv_writer_agent import CVWriterAgent
from agents.virtual_assistant import VirtualAssistantAgent

from . import candidate_bp
from utils import process_file, fetch_pdf_content_from_link
from connections import get_supabase_connection, get_github_connection

ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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


@candidate_bp.route('/')
def home():
    # No errors the first time
    errors = {
        'jd' : [],
        'cv' : [],
    }
    db = get_supabase_connection()
    jobs = db.get_all_jobs()
    return render_template('c_index.html', jobs=jobs, errors=errors)


@candidate_bp.route('/process', methods=['POST'])
def process_files():
    errors = {
        'jd' : [],
        'cv' : [],
    }
    gh = get_github_connection()
    db = get_supabase_connection()

    try:
        job_desc_extract_link = request.form.get('job_id')
        job_description_raw = gh.get_job_description(job_desc_extract_link)
        VA = VirtualAssistantAgent()
        job_description = VA.send_message("user", f"Please extract the job description from this text {job_description_raw}")
        job_obj = db.get_job_by_field_value('export_location', job_desc_extract_link)
        if 'error' in job_description.lower() and len(job_description) < 100:
            raise ValueError("Unable to extract job description.")
    except Exception as e:
        errors['jd'].append(str(e))


    cv_file = request.files.get('cv')
    cv_link = request.form.get('cv_link')
    if cv_file and allowed_file(cv_file.filename):
        try:
            cv_text = process_file(cv_file)
        except Exception as e:
            errors['cv'].append(str(e))
    elif cv_link:
        try:
            cv_text = fetch_pdf_content_from_link(cv_link)
        except ValueError as e:
            errors['cv'].append(str(e))
        
    if errors['cv'] or errors['jd']:
        return render_template('c_index.html', errors=errors, jobs=db.get_all_jobs())
    
    print("Generating candidate appraisal and advice")
    # Candidate appraisal
    searching_agent = SearchingAgent(
        job_description=job_description,
        cvs=[cv_text],
        n_candidates=1,
        min_suitability_score=8,
        suitability_threshold=0,
        most_important_skills='auto'
    )
    searching_agent.most_important_skills = ["Bitcoin knowledge and experience"] + searching_agent.most_important_skills

    searching_agent.appraise_candidates()
    candidate_bp.agent_store.candidate_agents['searching_agent'] = searching_agent
    candidate_appraisal = copy.deepcopy(searching_agent.candidates[0])

    # Candidate advice
    advisor_agent = AdvisorAgent(
        job_description=job_description,
        cv=cv_text,
        most_important_skills=searching_agent.most_important_skills,
        recruiter_appraisal_data=candidate_appraisal
    )
    candidate_advice = advisor_agent.advise_candidate()
    candidate_bp.agent_store.candidate_agents['advisor_agent'] = advisor_agent
    candidate_appraisal['skills'].update(candidate_advice['skills'])

    job_description_md = Markup(markdown.markdown(job_description))
    if errors['cv'] or errors['jd']:
        return render_template('c_index.html', errors=errors, jobs=db.get_all_jobs())
    return render_template('feedback_template.html', candidate=candidate_appraisal, job_description=job_description_md, link_to_job_details=job_obj['url'])




@candidate_bp.route('/update_cv', methods=['POST'])
def update_cv():
    updates = request.form
    if not updates:
        return jsonify({'error': 'No updates were provided.'}), 400

    # Process updates (e.g., save to a file, database, or pass to another agent)
    updated_cv_text = ''
    for key, exp in updates.items():
        skill = key.replace('updates[', '').replace(']', '')
        updated_cv_text += f"{skill}: {exp}\n"


    # Update the appraisal based on the updated cv text
    candidate_bp.agent_store.candidate_agents['searching_agent'].candidates[0]['cv_text'] += updated_cv_text
    candidate_bp.agent_store.candidate_agents['searching_agent'].appraise_candidates()
    candidate_appraisal = copy.deepcopy(candidate_bp.agent_store.candidate_agents['searching_agent'].candidates[0])

    candidate_bp.agent_store.candidate_agents['advisor_agent'].cv += updated_cv_text

    candidate_advice = candidate_bp.agent_store.candidate_agents['advisor_agent'].advise_candidate()

    
    candidate_appraisal['skills'].update(candidate_advice['skills'])

    # Provide feedback to the candidate or redirect
    return render_template('feedback_template.html', candidate=candidate_appraisal)



@candidate_bp.route('/generate_cv', methods=['POST'])
def generated_cv():

    writer_agent = CVWriterAgent(
        job_description=candidate_bp.agent_store.candidate_agents['advisor_agent'].job_description,
        cv=candidate_bp.agent_store.candidate_agents['advisor_agent'].cv,
        most_important_skills=candidate_bp.agent_store.candidate_agents['advisor_agent'].most_important_skills
    )

    candidate_bp.agent_store.candidate_agents['writer_agent'] = writer_agent

    cv_data = writer_agent.write_cv()

    return render_template('cv_templates/template_1/cv.html', profile=cv_data)


