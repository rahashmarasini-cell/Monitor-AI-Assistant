# ---- UPDATED FILE: src/ai_processor.py ----
"""
AI processor – builds the prompt, calls the local LLM, and cleans the answer.
"""

from typing import Optional

from .config import PROMPT_TEMPLATE
from .local_llm import LocalLLM

# Initialise a single global instance (lazy load the model once)
_llm_instance = LocalLLM()

def build_prompt(extracted_text: str) -> str:
    """
    Insert the OCR‑extracted text into the user‑defined prompt template.
    """
    # Truncate very long OCR output – keep within context window.
    max_len = 3000
    if len(extracted_text) > max_len:
        extracted_text = extracted_text[:max_len] + "\n...[truncated]"

    return PROMPT_TEMPLATE.format(extracted_text=extracted_text)


def clean_llm_response(raw: str) -> str:
    """
    Very light post‑processing:
        * strip whitespace
        * remove surrounding Markdown code fences if the model wrapped the answer.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        # Remove the first and/or last fence line
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw


def query_llm(extracted_text: str, user_question: Optional[str] = None) -> str:
    """
    Build the full prompt, query the local model, and return a cleaned answer.
    ``user_question`` is optional – the base prompt already says *if there is a
    question in the OCR text, answer it; otherwise summarise*.
    """
    prompt = build_prompt(extracted_text)

    if user_question:
        # Simple prepend – you could incorporate a more elaborate chat format later.
        prompt = f"User question: {user_question}\n\n{prompt}"

    # Call the global LLM wrapper.
    raw_answer = _llm_instance.generate(prompt)

    return clean_llm_response(raw_answer)
# -------------------------------------------------
