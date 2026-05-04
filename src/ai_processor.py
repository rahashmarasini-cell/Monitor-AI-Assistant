# ---- UPDATED FILE: src/ai_processor.py ----
"""
AI processor – builds the prompt, calls the local LLM, and cleans the answer.

Features:
  * Text-based analysis via OCR
  * Graph/chart analysis and interpretation
  * Integrated analysis combining both approaches
"""

from typing import Optional
from pathlib import Path

from .config import PROMPT_TEMPLATE, TEMP_SCREENSHOT_PATH
from .local_llm import LocalLLM

# Initialise a single global instance (lazy load the model once)
_llm_instance = LocalLLM()

def build_prompt(extracted_text: str) -> str:
    """
    Insert the OCR‑extracted text into the user‑defined prompt template.
    """
    # Truncate very long OCR output – keep within context window.
    max_len = 1800  # keeps total prompt safely within 2048-token context window
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
    Build the full prompt and return a cleaned answer.
    Uses Mistral [INST] format. When a user_question is provided and the OCR
    text is thin, the question is answered directly without screen context.
    """
    has_context = extracted_text and len(extracted_text.strip()) > 30

    if user_question:
        if has_context:
            context = extracted_text.strip()[:1800]
            prompt = (
                f"<s>[INST] You are an expert assistant. Use the screen content below as context "
                f"to answer the user's question. Show your reasoning clearly.\n\n"
                f"Screen content:\n{context}\n\n"
                f"Question: {user_question} [/INST]"
            )
        else:
            prompt = (
                f"<s>[INST] You are an expert assistant. Answer the following question "
                f"clearly and step by step.\n\nQuestion: {user_question} [/INST]"
            )
    else:
        prompt = build_prompt(extracted_text)

    raw_answer = _llm_instance.generate(prompt)
    return clean_llm_response(raw_answer)


# -------------------------------------------------
# Graph Analysis Integration
# -------------------------------------------------

def analyze_graph_with_llm(image_path: Path = TEMP_SCREENSHOT_PATH, user_question: Optional[str] = None) -> str:
    """
    Detect and analyze graphs in a screenshot using pytesseract,
    then feed the analysis to the LLM for interpretation.
    
    Args:
        image_path: Path to the screenshot (default: last capture)
        user_question: Optional user question about the graph
        
    Returns:
        LLM's analysis of the graph
    """
    try:
        from .ocr_processor import analyze_graphs_in_screenshot
        
        graph_description = analyze_graphs_in_screenshot(image_path)
        if not graph_description or "No graphs" in graph_description:
            return "No graphs detected in the screenshot."
        
        # Build a prompt specifically for graph analysis
        graph_prompt = f"""You are analyzing a graph/chart from a screenshot.

Graph Analysis:
{graph_description}

Based on this graph analysis, provide:
1. Key findings or trends visible in the data
2. Any anomalies or notable patterns
3. What the graph appears to be measuring
4. Suggested interpretations or insights

Be concise and focus on actionable insights."""
        
        if user_question:
            graph_prompt = f"User's question: {user_question}\n\n{graph_prompt}"
        
        raw_answer = _llm_instance.generate(graph_prompt)
        return clean_llm_response(raw_answer)
        
    except Exception as e:
        print(f"[ERROR] Graph analysis with LLM failed: {e}")
        return f"Error analyzing graph: {str(e)}"


def combined_analysis(
    extracted_text: str,
    image_path: Path = TEMP_SCREENSHOT_PATH,
    user_question: Optional[str] = None
) -> str:
    """
    Perform both text-based OCR analysis and graph analysis,
    then combine them for comprehensive screenshot understanding.
    
    Args:
        extracted_text: OCR-extracted text from the screenshot
        image_path: Path to the screenshot
        user_question: Optional user question
        
    Returns:
        Combined analysis from the LLM
    """
    try:
        from .ocr_processor import analyze_graphs_in_screenshot
        
        graph_analysis = analyze_graphs_in_screenshot(image_path)
        
        # Build combined prompt
        combined_prompt = f"""Analyze this screenshot containing both text content and potential graphs.

OCR Extracted Text:
{extracted_text}

Graph Analysis:
{graph_analysis}

Please provide:
1. Summary of the text content
2. Analysis of any graphs/charts present
3. How the text and graphs relate to each other
4. Key insights or findings

Keep response focused and under 500 words."""
        
        if user_question:
            combined_prompt = f"User's question: {user_question}\n\n{combined_prompt}"
        
        raw_answer = _llm_instance.generate(combined_prompt)
        return clean_llm_response(raw_answer)
        
    except Exception as e:
        print(f"[ERROR] Combined analysis failed: {e}")
        # Fallback to text-only analysis
        return query_llm(extracted_text, user_question)

# -------------------------------------------------

