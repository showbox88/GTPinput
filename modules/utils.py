import streamlit as st
from streamlit_javascript import st_javascript

def get_device_type():
    """
    Detects if the user is on mobile or desktop based on screen width.
    Returns: 'mobile' or 'desktop'
    """
    # Use session state to avoid re-run flicker if already detected
    if "device_type" in st.session_state:
        return st.session_state["device_type"]
        
    # Get window width via JS
    width = st_javascript("window.innerWidth")
    
    if width:
        if width < 768:
            st.session_state["device_type"] = "mobile"
            return "mobile"
        else:
            st.session_state["device_type"] = "desktop"
            return "desktop"
            
    # Default fallback (conservative)
    return "desktop"
