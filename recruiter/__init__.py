from flask import Blueprint

# Define the Blueprint
recruiter_bp = Blueprint('recruiter', __name__, template_folder='templates', static_folder='static')

# Add a placeholder for the agent store
recruiter_bp.agent_store = None

from . import views  # Import routes