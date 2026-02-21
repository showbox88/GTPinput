import json
import os
import streamlit as st

# Path to the locales directory relative to the project root
LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')

def get_locale_dict(lang_code):
    """Load the translation dictionary for a given language code."""
    file_path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading locale {lang_code}: {e}")
    
    # Fallback to empty if not found
    return {}

def init_i18n(user_lang_code="zh"):
    """
    Initialize the i18n dictionary into Streamlit's session state.
    This prevents hitting the disk on every single widget render.
    """
    if "i18n_dict" not in st.session_state or st.session_state.get("current_lang") != user_lang_code:
        st.session_state["i18n_dict"] = get_locale_dict(user_lang_code)
        st.session_state["current_lang"] = user_lang_code

def _(key, **kwargs):
    """
    The translation lookup function.
    Returns the translated string for the given key.
    If the key doesn't exist, returns the key itself as a fallback.
    Accepts kwargs for string formatting (e.g. _("hello_name", name="John")).
    """
    # Ensure i18n is initialized (fallback to Chinese if entirely missing from flow)
    if "i18n_dict" not in st.session_state:
        init_i18n("zh")
        
    translation = st.session_state["i18n_dict"].get(key)
    
    # If the current language is missing the key, try to fallback to the literal key
    if translation is None:
        translation = key
        
    # Format the string if kwargs are provided
    if kwargs and isinstance(translation, str):
        try:
            return translation.format(**kwargs)
        except KeyError:
            # If formatting fails due to mismatched keys, return raw translation
            pass
            
    return translation
