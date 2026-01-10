from flask import Blueprint 
red_team_bp = Blueprint('red_team', __name__, url_prefix='/api/red-team', template_folder='templates') 
