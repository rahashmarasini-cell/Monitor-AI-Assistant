# ---- NEW FILE: src/ai_processor.py ----
import os
import openai
from .config import LLM_MODEL, PROMPT_TEMPLATE
from typing import Optional

# -------------------------------------------------
# 1️⃣  OpenAI configuration (API key can also be set in env var ``OPENAI_API_KEY``)
# -------------------------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set!")

# -------------------------------------------------
# 2️⃣  Prompt construction + post‑processing helpers
# -------------------------------------------------
def build_prompt(extracted_text: str) -> str:
    """
    Inject the OCR text into the user‑defined prompt template.
    """
    # Trim huge OCR bundles – keep first 3000 characters (most LLM context windows)
    max_len = 3000
    if len(extracted_text) > max_len:
        extracted_text = extracted_text[:max_len] + "\n...[truncated]"

    return PROMPT_TEMPLATE.format(extracted_text=extracted_text)


def clean_llm_response(raw: str) -> str:
    """
    Basic post‑processing:
        • Strip leading/trailing whitespace
        • Remove any stray markdown code fences if the model wrapped the answer.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        # Remove first line (``` or ```text) and trailing ```
        lines = raw.splitlines()
        # drop first and last line if they are fences
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw


# -------------------------------------------------
# 3️⃣  Core query function
# -------------------------------------------------
def query_llm(extracted_text: str, user_question: Optional[str] = None) -> str:
    """
    Send a request to the LLM and return a cleaned answer.
    ``user_question`` can be ``None`` – the prompt already asks the model
    to either answer a question *if* it exists in the OCR text, otherwise summarize.
    """
    prompt = build_prompt(extracted_text)

    # If the caller supplies a direct question (e.g. from a UI textbox), prepend it.
    if user_question:
        prompt = f"User question: {user_question}\n\n{prompt}"

    try:
        response = openai.ChatCompletion.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,        # low temperature for deterministic answers
            max_tokens=500,
        )
        raw_answer = response.choices[0].message["content"]
        return clean_llm_response(raw_answer)

    except openai.error.OpenAIError as e:
        # Graceful fallback – you could also raise a custom exception.
        return f"[LLM ERROR] {e}"
# -------------------------------------------------
