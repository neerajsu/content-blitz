# Agentic Content Marketing Assistant

Capstone-grade content marketing assistant built with LangChain, Streamlit, and SERP API. Generates research summaries, SEO blogs, LinkedIn posts, and image prompts while keeping brand voice consistent.

## Architecture
- **UI**: Streamlit Home page with research/content/image areas.
- **Agents** (`agents/`):
  - `router_agent`: intent classification (`research`, `blog`, `linkedin`, `image`, `mixed`).
  - `research_agent`: SERP search + summarization + SEO keywords.
  - `blog_agent`: brand-aware blog from research summary.
  - `linkedin_agent`: converts blog/research into LinkedIn post + optional carousel.
  - `image_agent`: brand-aware prompt, caption, alt text (image generation stub).
- **Memory Layers**:
  - Conversation buffer (`memory/conversation_memory.py`) for multi-turn chat context.
  - Streamlit `session_state` for UI/session data.
- **Utilities** (`utils/`): LLM loader with provider fallback, SERP client with stubbed results when key missing.

## Setup
1. **Install**  
   ```bash
   cd content_marketing_agent
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. **Configure env**  
   Copy `.env.example` + `.env` and set your keys (`OPENAI_API_KEY`, optional `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `SERPAPI_API_KEY`). Defaults to OpenAI; falls back to stubs if missing.
3. **Run Streamlit**  
   ```bash
   streamlit run content_marketing_agent/app.py
   ```

## Using the App
The app currently loads the Home page only (snapshots and stubs). Agents remain available in `agents/` for programmatic use or future UI wiring.

## Extensibility Notes
- Swap LLM providers via `.env` (`LLM_PROVIDER=openai|anthropic|gemini`).
- Integrate real image generation by replacing the stub in `agents/image_agent.py`.
