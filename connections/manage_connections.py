from flask import g
from .supabase import SupabaseConnection
from .github import GithubConnection

def get_supabase_connection():
    if 'supabase' not in g:
        g.supabase = SupabaseConnection()  # Initialize connection
    return g.supabase

def get_github_connection():
    if 'github' not in g:
        g.github = GithubConnection()  # Initialize connection
    return g.github
