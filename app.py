from flask import Flask, render_template, redirect, url_for, session, request, flash
from dotenv import load_dotenv

from candidate import candidate_bp
from agents import AgentStore
from utils import protect_routes

import os

app = Flask(__name__)

# Create a shared agent store instance
agent_store = AgentStore()

load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Needed to use Flask's session

# Predefined user credentials
USERNAME = os.getenv("FLASK_LOGIN_USERNAME")
PASSWORD = os.getenv("FLASK_LOGIN_PASSWORD")

# Pass agent_store to Blueprints
candidate_bp.agent_store = agent_store

# Register Blueprints
app.register_blueprint(candidate_bp, url_prefix='/candidate')
protect_routes(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate user credentials
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    
    # Render the login form
    return render_template('login.html')

@app.route('/')
def home():
    # Check if the user is logged in
    if 'logged_in' in session and session['logged_in']:
        # return render_template('index.html')
        return redirect(url_for('candidate.home'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
