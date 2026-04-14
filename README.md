# Monitor-AI-Assistant

## Local‑LLM (no OpenAI needed)

The assistant now runs a **local LLM** via `llama-cpp-python`.  
Follow these steps once:

1. **Install the Python dependencies** (the `requirements.txt` already includes `llama-cpp-python`).

2. **Download a GGML quantised model** – e.g. Mistral‑7B‑Instruct:

   ```powershell
   mkdir models
   cd models
   curl -L -o mistral-7b-instruct.Q4_0.ggmlv3.bin ^
     https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGML/resolve/main/mistral-7b-instruct-v0.1.Q4_0.ggmlv3.bin
   cd ..

