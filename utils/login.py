from functools import wraps
from flask import redirect, url_for, session, flash

def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash("You must be logged in to access this page.", "danger")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function

def protect_routes(app):
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('candidate.') | rule.endpoint.startswith('recruiter.'):
            app.view_functions[rule.endpoint] = login_required(app.view_functions[rule.endpoint])