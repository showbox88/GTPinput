# Plan: Multi-Language AI Assistant Support (Postponed)

> [!NOTE]
> This feature is planned but implementation is currently on hold per user request.

Currently, the AI assistant is hardcoded to respond in Simplified Chinese, regardless of the user's interface language setting. This plan aims to make the AI respond in the user's preferred language while maintaining its ability to understand multilingual input.

## Proposed Changes

### [AI Logic]
- **File**: `expense_chat.py`
- **Dynamic Prompting**: Replace hardcoded "Simplified Chinese" instruction with a `%LANGUAGE%` placeholder.
- **Parametrization**: Update `process_user_message` to accept a `language` argument.

### [UI Logic]
- **File**: `modules/ui_v2.py`
- **Session Sync**: Pass `st.session_state["current_lang"]` to the AI processing function.

## Verification
- Use mock scripts to ensure code-to-prompt mapping works (e.g., `en` -> `English`).
- Manual toggle in settings and chat verification.
