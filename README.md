# Agentic Content Marketing Assistant

Capstone-grade content marketing assistant built with LangChain and Streamlit. Generates research summaries, SEO blogs, LinkedIn posts, and images while keeping brand voice consistent.

## Agents

- `intent_agent`: classify whether the user wants a blog, LinkedIn post, or both.
- `topic_and_sections_agent`: extract topic and section outline directly from the prompt.
- `topic_and_section_generator_agent`: generate a topic/outline from stored research metadata.
- `research_agent`: Perplexity Sonar research with citations and structured outputs.
- `guard_agent`: ensure new prompts stay relevant to the existing research thread.
- `content_orchestrator_agent`: pull Pinecone vector context and normalize state fields.
- `blog_agent`: draft long-form blog content using brand voice and vector context.
- `linkedin_agent`: generate LinkedIn posts and optional carousel copy.
- `image_agent`: craft prompts and generate images via OpenAI.
- `title_agent`: generate concise titles from research summaries.

## Architecture Diagram

```
User
  |
  v
Streamlit UI  <--------------------->  MongoDB (projects, chats, research)
  |
  v
Content Graph (routing + state)
  |
  +--> Research Agent -----> Perplexity API
  |
  +--> Content Orchestrator -----> Pinecone Vector DB
  |                                   |
  |                                   v
  +--> Blog/LinkedIn Agents -----> LLM Provider (OpenAI/Anthropic/Gemini)
  |
  +--> Image Agent -----------> OpenAI Images API
```

## Setup

1. **Install dependencies**
   ```bash
   cd content_marketing_agent
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. **Create a `.env` file**
   ```bash
   copy .env.example .env
   ```
3. **Configure required keys**
   - `OPENAI_API_KEY` for LLM + image generation.
   - `PERPLEXITY_API_KEY` for research.
   - `PINECONE_API_KEY` for vector search.
   - `GOOGLE_API_KEY` for generating image prompts.
   - `MONGO_URI` / `MONGO_DB_NAME` for persistence (local dev defaults are fine).
4. **Provision Pinecone**
   - Create a Pinecone project and get the API key.
   - Set `PINECONE_INDEX_NAME` (default: `content-blitz`).
   - Optional: set `PINECONE_CLOUD` and `PINECONE_REGION` for serverless.
5. **Start MongoDB (local dev)**
   ```bash
   docker-compose up -d mongo
   ```
6. **Run Streamlit**
   ```bash
   streamlit run content_marketing_agent/app.py
   ```

## Notes

- Switch providers with `LLM_PROVIDER=openai|anthropic|gemini`.
- Pinecone indexes are created automatically if missing and credentials are valid.
