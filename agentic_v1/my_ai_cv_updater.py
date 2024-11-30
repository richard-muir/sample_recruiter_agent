import random
import os
from flask import Flask, render_template, url_for, make_response, request, jsonify
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from datetime import datetime
from flask_weasyprint import HTML, render_pdf
import pdfkit
from werkzeug.utils import secure_filename

import asyncio
from pyppeteer import launch

from my_ai_recruiter import SearchingAgent
from recruiter_advisor import AdvisorAgent




    

app = Flask(__name__, template_folder='templates', static_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
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
    
    searching_agent = SearchingAgent(
            job_description=open(job_path, 'r').read(),
            cv_dir=CV_DIR,
            n_candidates=1,
            min_suitability_score=8,
            suitability_threshold=0,
            most_important_skills='auto'
        )
    
    searching_agent.appraise_candidates()
    candidate_appraisal = searching_agent.candidates[0]

    advisor_agent = AdvisorAgent(
        job_description=open(job_path, 'r').read(),
        cv=open(cv_path, 'r').read(),
        most_important_skills=searching_agent.most_important_skills,
        recruiter_appraisal_data=candidate_appraisal
    )

    candidate_advice = advisor_agent.advise_candidate()
    print(candidate_advice)

    candidate_appraisal['skills'].update(candidate_advice['skills'])

    return render_template('feedback_template.html', candidate=candidate_appraisal)




@app.route('/generate_cv', methods=['POST'])
def generated_cv():
    

    cv_data = get_cv_data()

    return render_template('cv_template_1.html', profile=cv_data)


def get_cv_data():
    profile_data = {
        "name": "Joe Bloggs",
        "job_title": "Software Engineer",
        "contact": {
            "email": "joe.bloggs@example.com",
            "phone": "+123456789",
            "website": "http://example.com"
        },
        "skills": ["Python", "Flask", "Docker"],
        'jobs': [
            {
                'title': 'Job Title at Company 1',
                'dates': 'April 2011 - Present',
                'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec ultricies massa et erat luctus hendrerit. Curabitur non consequat enim. Vestibulum bibendum mattis dignissim. Proin id sapien quis libero interdum porttitor.'
            },
            {
                'title': 'Job Title at Company 2',
                'dates': 'January 2007 - March 2011',
                'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec ultricies massa et erat luctus hendrerit. Curabitur non consequat enim. Vestibulum bibendum mattis dignissim. Proin id sapien quis libero interdum porttitor.'
            },
            {
                'title': 'Job Title at Company 3',
                'dates': 'October 2004 - December 2006',
                'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec ultricies massa et erat luctus hendrerit. Curabitur non consequat enim. Vestibulum bibendum mattis dignissim. Proin id sapien quis libero interdum porttitor.'
            }
        ],
        'education': [
            {
                'qualification': 'Bachelor of Science in Computer Science',
                'institution': 'University of Example',
                'dates': 'September 2010 - June 2014',
                'description': 'Studied various computer science concepts, including algorithms, data structures, and software engineering.'
            },
            {
                'qualification': 'Master of Science in Data Science',
                'institution': 'Tech University',
                'dates': 'September 2015 - June 2017',
                'description': 'Focused on machine learning, data mining, and big data technologies.'
            }
        ]
    }
    profile_data_3 = {
    "name": "Michael Johnson",
    "job_title": "DevOps Engineer",
    "contact": {
        "email": "michael.johnson@example.com",
        "phone": "+123987456",
        "website": "http://michaeljdevops.com"
    },
    "skills": ["AWS", "Kubernetes", "Terraform", "Jenkins", "Linux"],
    'jobs': [
        {
            'title': 'DevOps Engineer at CloudTech',
            'dates': 'June 2018 - Present',
            'description': 'Implemented CI/CD pipelines using Jenkins and GitLab CI. Automated cloud infrastructure management with Terraform and Ansible.'
        },
        {
            'title': 'System Administrator at IT Solutions',
            'dates': 'September 2015 - May 2018',
            'description': 'Maintained and optimized server environments. Introduced monitoring tools, reducing downtime by 20%.'
        },
        {
            'title': 'IT Support Technician at NetWorks',
            'dates': 'March 2013 - August 2015',
            'description': 'Provided technical support for hardware and software issues. Assisted in network troubleshooting and maintenance.'
        }
    ],
    'education': [
        {
            'qualification': 'Bachelor of Science in Information Technology',
            'institution': 'Tech Institute',
            'dates': 'September 2008 - June 2012',
            'description': 'Focused on network administration, operating systems, and cybersecurity.'
        },
        {
            'qualification': 'AWS Certified Solutions Architect',
            'institution': 'AWS Training and Certification',
            'dates': 'March 2019',
            'description': 'Earned certification in designing and deploying scalable cloud systems.'
        }
    ]
}
    profile_data_2 = {
    "name": "Jane Smith",
    "job_title": "Data Analyst",
    "contact": {
        "email": "jane.smith@example.com",
        "phone": "+987654321",
        "website": "http://janesmithdata.com"
    },
    "skills": ["SQL", "Tableau", "Excel", "Python"],
    'jobs': [
        {
            'title': 'Senior Data Analyst at Analytics Co.',
            'dates': 'March 2015 - Present',
            'description': 'Led a team of analysts to develop insightful dashboards and reports. Improved data quality processes, resulting in a 25% reduction in reporting errors.'
        },
        {
            'title': 'Data Analyst at Retail Insights',
            'dates': 'August 2012 - February 2015',
            'description': 'Analyzed sales trends and customer data to inform marketing strategies, contributing to a 15% increase in revenue.'
        },
        {
            'title': 'Junior Analyst at Market Trends Inc.',
            'dates': 'June 2010 - July 2012',
            'description': 'Supported senior analysts with data preparation and ad-hoc reporting. Gained expertise in data visualization tools.'
        }
    ],
    'education': [
        {
            'qualification': 'Bachelor of Arts in Economics',
            'institution': 'State University',
            'dates': 'September 2006 - June 2010',
            'description': 'Studied microeconomics, statistics, and econometrics. Developed a strong foundation in data analysis.'
        },
        {
            'qualification': 'Certified Data Analyst',
            'institution': 'Analytics Certification Program',
            'dates': 'July 2013 - December 2013',
            'description': 'Earned certification in advanced analytics and data visualization techniques.'
        }
    ]
}
    return random.choice([profile_data, profile_data_2, profile_data_3])


if __name__ == '__main__':
    app.run(debug=True)