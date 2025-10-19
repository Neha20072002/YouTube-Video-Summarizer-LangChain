# YouTube Video Summarizer (LangChain + Streamlit)

Summarize the content of YouTube videos or arbitrary web pages in seconds using LangChain and a Hugging Face Inference Endpoint-backed LLM, all through a simple Streamlit UI.

This project loads transcripts from YouTube (or text from any URL), then prompts a modern instruction-tuned model to generate a concise summary (~300 words by default).

---

## Features
- Input any valid URL:
  - YouTube URLs are handled via `YoutubeLoader`
  - Other web pages are handled via `UnstructuredURLLoader`
- Hugging Face-hosted LLM via `HuggingFaceEndpoint` (default: `mistralai/Mistral-7B-Instruct-v0.3`)
- Streamlit UI for quick use—no notebooks needed
- Basic input validation and error handling

---

## Quickstart

### 1) Prerequisites
- Python 3.10+
- A Hugging Face API token with access to Inference Endpoints
  - Create at: https://huggingface.co/settings/tokens

### 2) Clone and install
```bash
git clone https://github.com/<your-username>/YouTube-Video-Summarizer-LangChain.git
cd YouTube-Video-Summarizer-LangChain
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment
The app expects a Hugging Face API token. You can provide it in the sidebar when running the app, or set it as an environment variable so it is prefilled by you later if you adapt the code.

Optional environment variables you may set in your shell (not required by default app UI):
- `HF_API_TOKEN` – your Hugging Face token
- `REPO_ID` – override the default model repo (e.g. `mistralai/Mistral-7B-Instruct-v0.3`)

### 4) Run the app
```bash
streamlit run app.py
```
Open the printed local URL in your browser. Enter:
- Your Hugging Face API token (left sidebar)
- A valid URL (YouTube or any web page)
Then click "Summarize".

---

## How it works
- The app detects if the provided URL is from YouTube. If so, it uses `YoutubeLoader` to fetch the transcript and metadata. Otherwise, it uses `UnstructuredURLLoader` to fetch and parse the page content.
- A concise summarization prompt (~300 words) is built with `PromptTemplate`.
- `HuggingFaceEndpoint` calls the configured model with temperature and max length settings.
- `load_summarize_chain(..., chain_type="stuff")` runs the summarization chain over the loaded documents.

Key modules involved are in `app.py`:
- `langchain.prompts.PromptTemplate`
- `langchain.chains.summarize.load_summarize_chain`
- `langchain_community.document_loaders.YoutubeLoader` and `UnstructuredURLLoader`
- `langchain_huggingface.HuggingFaceEndpoint`

---

## Configuration tips
- If you frequently use the same token/model, you may adapt `app.py` to read from environment variables to avoid manual entry.
- If you hit rate limits or slow responses, consider using a smaller/lighter model, or host a private Inference Endpoint.

---

## Troubleshooting
- "Please enter a valid URL": Ensure it starts with `http://` or `https://` and is reachable.
- YouTube transcript missing: Some videos disable transcripts or block access. Try another video or ensure regional access.
- Hugging Face token errors: Confirm your token is valid and has access to the target repo/endpoint.
- SSL or parsing errors on arbitrary sites: Not all sites allow scraping; consider alternative sources.
- CPU-only Torch wheels are pinned; if installation fails on your platform, you can remove the CPU-specific Torch lines in `requirements.txt` and install GPU builds or platform-appropriate binaries.

---

## Roadmap
- Add chunking and map-reduce summarization for very long texts
- Adjustable summary length and tone in the UI
- Optional local models via `llama.cpp`/`OLLAMA` or HF Transformers
- Persistent history and export (Markdown/JSON)
- Basic tests for loaders and prompt assembly

---

## Contributing
Contributions are welcome! Please see `CONTRIBUTING.md` for setup, coding standards, and how to submit changes. We follow a friendly and respectful community standard—see `CODE_OF_CONDUCT.md`.

---

## License
This project is released under the MIT License. See `LICENSE` for details.

---

## Acknowledgements
- Built with [LangChain](https://python.langchain.com/)
- UI with [Streamlit](https://streamlit.io/)
- Model served via [Hugging Face Inference Endpoints](https://huggingface.co/inference-endpoints)