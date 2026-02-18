import os
import json
import streamlit as st

SESSION_FILE = ".session_cache"

def save_session_to_file(session):
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({
                "access_token": session.access_token,
                "refresh_token": session.refresh_token
            }, f)
    except Exception as e:
        print(f"Failed to save session: {e}")

def load_session_from_file():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                return data
        except:
            return None
    return None

def delete_session_file():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def restore_session(supabase):
    """
    Attempts to restore session from file and sets it in the supabase client.
    Returns (session, user) if successful, else (None, None).
    """
    saved_session = load_session_from_file()
    if saved_session:
        try:
            res = supabase.auth.set_session(
                saved_session["access_token"], 
                saved_session["refresh_token"]
            )
            return res.session, res.user
        except Exception as e:
            delete_session_file()
    return None, None

def sign_in(supabase, email, password, remember=True):
    """
    Signs in user and optionally saves session.
    Returns response object.
    """
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if remember and res.session:
        save_session_to_file(res.session)
    return res

def sign_up(supabase, email, password):
    """
    Signs up a new user.
    """
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_out(supabase):
    """
    Signs out user and deletes local session file.
    """
    try:
        supabase.auth.sign_out()
    except:
        pass
    delete_session_file()
