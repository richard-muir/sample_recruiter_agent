from flask import Flask, render_template, redirect, url_for

from recruiter import recruiter_bp
from candidate import candidate_bp
from agents import AgentStore

app = Flask(__name__)

# Create a shared agent store instance
agent_store = AgentStore()

# Pass agent_store to Blueprints
candidate_bp.agent_store = agent_store
recruiter_bp.agent_store = agent_store

# Register Blueprints
app.register_blueprint(recruiter_bp, url_prefix='/recruiter')
app.register_blueprint(candidate_bp, url_prefix='/candidate')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
