from ai_module import ask_model, build_prompt

def test_ask_model():
    prompt = "What is the capital of France?"
    expected_answer = "Paris"  # Adjust based on the AI model's expected output
    answer = ask_model(prompt)
    assert answer.strip() == expected_answer, f"Expected '{expected_answer}', but got '{answer}'"

def test_build_prompt():
    ocr_text = "The capital of France is Paris."
    expected_prompt = "Based on the following text: 'The capital of France is Paris.', what can you tell me?"
    prompt = build_prompt(ocr_text)
    assert prompt.strip() == expected_prompt, f"Expected '{expected_prompt}', but got '{prompt}'"