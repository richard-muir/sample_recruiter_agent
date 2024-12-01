from flask import Blueprint

# Define the Blueprint
candidate_bp = Blueprint('candidate', __name__, template_folder='templates', static_folder='templates')

candidate_bp.agent_store = None

from . import views  # Import routes
