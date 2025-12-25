# Agentic Content Marketing Assistant

Capstone-grade, multi-agent content marketing assistant built with LangChain, LangGraph, FAISS RAG, Streamlit, and SERP API. Generates research summaries, SEO blogs, LinkedIn posts, and image prompts while keeping brand voice consistent.

## Architecture
- **LangGraph Orchestration**: `graph/content_graph.py` defines a `StateGraph` with nodes `router -> (research | blog | linkedin | image) -> END`. The router classifies intent and conditionally routes execution.
- **Agents** (`agents/`):
  - `router_agent`: intent classification (`research`, `blog`, `linkedin`, `image`, `mixed`).
  - `research_agent`: SERP search → summarization + SEO keywords → caches in `research_cache`.
  - `blog_agent`: RAG brand voice + research summary → markdown blog + meta title/description → logs to `past_outputs`.
  - `linkedin_agent`: Converts blog/research into LinkedIn post + optional carousel; logs to `past_outputs`.
  - `image_agent`: Brand-aware prompt, caption, alt text (image generation stub) → logs to `past_outputs`.
- **RAG (FAISS)**: Used **only** for brand voice, past outputs, and research cache. Collections: `brand_voice`, `past_outputs`, `research_cache`.
- **Memory Layers**:
  - Conversation buffer (`memory/conversation_memory.py`) for multi-turn chat context.
  - Long-term FAISS memory via `memory/vector_store.py`.
  - Streamlit `session_state` for UI/session data.
- **Utilities** (`utils/`): LLM loader with provider fallback, embeddings with fallbacks (OpenAI → HuggingFace → fake), SERP client with stubbed results when key missing.

## Setup
1. **Install**  
   ```bash
   cd content_marketing_agent
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. **Configure env**  
   Copy `.env.example` → `.env` and set your keys (`OPENAI_API_KEY`, optional `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `SERPAPI_API_KEY`). Defaults to OpenAI; falls back to stubs if missing.
3. **Run Streamlit**  
   ```bash
   streamlit run content_marketing_agent/app.py
   ```

## Using the App
1. **Brand Setup**: Provide brand name, tone, audience, and writing guidelines; save to store brand voice in FAISS (`brand_voice`).
2. **Chat**: Enter a request (e.g., “Research AI tools for B2B SaaS founders”). Click **Run Agents**. Router decides which node to execute.
3. **Outputs**: Review results in tabs (Research, Blog, LinkedIn, Image). Conversation memory is shown in the Session Memory expander.

## How LangGraph Is Used
- `content_graph.py` builds a `StateGraph` with explicit nodes and conditional routing. The compiled graph is invoked with state containing user input, brand profile, and conversation history.
- Router node sets `intent`; downstream nodes populate `research/blog/linkedin/image` fields before reaching `END`.

## How RAG Is Used (and why only there)
- FAISS collections:
  - `brand_voice`: retrieved to enforce tone/voice in blog and image agents.
  - `past_outputs`: keeps prior blogs/LinkedIn/image captions for long-term recall.
  - `research_cache`: stores summaries of prior research queries.
- RAG is **not** applied to every call; only brand/past content and cached research leverage similarity search to maintain consistency without unnecessary retrieval overhead.

## Example Flows
- **Research → Blog → LinkedIn**: Ask “Research trends in edge AI for manufacturing.” Router → research node → summary/keywords. Next, ask “Write a blog on this.” Router → blog node uses research summary + brand voice. Then “Turn that into a LinkedIn post.” Router → linkedin node uses latest blog.
- **Image Prompting**: “Create a hero image idea for the blog on edge AI.” Router → image node, applies brand voice RAG, returns prompt/caption/alt text.

## Extensibility Notes
- Swap LLM providers via `.env` (`LLM_PROVIDER=openai|anthropic|gemini`).
- Integrate real image generation by replacing the stub in `agents/image_agent.py`.
- Add analytics or persistence by extending `VectorStoreManager` or adding new LangGraph nodes.
