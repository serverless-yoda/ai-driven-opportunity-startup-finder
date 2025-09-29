# saas/api/index.py
import os
import time
from typing import Iterator
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from openai import AzureOpenAI

app = FastAPI()

# --- Clerk Auth ---
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

# --- Azure OpenAI config (keep your values; allow env overrides) ---
AZURE_OPENAI_ENDPOINT = "https://dgrea-mfxaprip-swedencentral.openai.azure.com/"
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
AZURE_OPENAI_DEPLOYMENT = "gpt-5-nano"

@app.get("/healthz")
def health():
    return {"ok": True}


@app.get("/api")
def idea(creds: HTTPAuthorizationCredentials = Depends(clerk_guard)):
    user_id = creds.decoded.get("sub", "unknown")

    def err_stream(msg: str):
        def gen():
            yield f"event: error\ndata: {msg}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")

    # Validate critical config and surface errors to the client UI
    if not AZURE_OPENAI_ENDPOINT or ".openai.azure.com" not in AZURE_OPENAI_ENDPOINT:
        return err_stream("Invalid AZURE_OPENAI_ENDPOINT (expected https://<resource>.openai.azure.com)")
    if not AZURE_OPENAI_API_KEY:
        return err_stream("AZURE_OPENAI_API_KEY not set")
    if not AZURE_OPENAI_DEPLOYMENT:
        return err_stream("AZURE_OPENAI_DEPLOYMENT not set (must be Azure deployment name)")
    if not AZURE_OPENAI_API_VERSION:
        return err_stream("AZURE_OPENAI_API_VERSION not set")

    client = AzureOpenAI(
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
    )

    
    
    SYSTEM_PROMPT = (
        "You are a product ideation assistant. Respond ONLY in valid GitHub-Flavored Markdown with this structure:\n\n"
        "## Idea Name\n\n"
        "## One-Liner\n\n"
        "### Problem\n"
        "- Bullet 1\n"
        "- Bullet 2\n\n"
        "### AI Agent Design\n"
        "- Bullet 1\n"
        "- Bullet 2\n\n"
        "### Target Users\n"
        "- Bullet 1\n\n"
        "### Monetization\n"
        "- Bullet 1\n\n"
        "Rules:\n"
        "- Every bullet MUST start with '- ' (dash + space).\n"
        "- Insert a blank line after each heading and before lists.\n"
        "- Do NOT include phrases like 'A blank line'.\n"
        "- Do NOT wrap the response in code fences.\n"
        "- Keep the entire response under 150 words.\n"
        "- Do NOT insert extra spaces inside words. Keep words intact.\n"
    )


    # Put format rules in SYSTEM, keep USER short/goal-focused
    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }

    user_message = {
        "role": "user",
        "content": "Generate one concise business idea for AI Agents.",
    }

    def sse() -> Iterator[str]:
        # Initial comment confirms the stream opened (SSE)
        yield ": stream-open\n\n"
        try:
            stream = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,   # deployment name
                messages=[system_message, user_message],
                stream=True,
                # Optional knobs to keep it tight and consistent
                max_completion_tokens=5000,  # adjust to taste (ensures brevity)
            )

            last_keepalive = time.time()
            for chunk in stream:
                text = None
                try:
                    delta = chunk.choices[0].delta
                    text = delta.get("content") if isinstance(delta, dict) else getattr(delta, "content", None)
                except Exception:
                    text = None

                if text:
                    # SSE spec: if the payload has newlines, emit one data: per line,
                    # then end the event with a blank line.
                    for line in text.splitlines():
                        yield f"data: {line}\n"
                    yield "\n"

                # Optional: keep-alive comment every 15s for some proxies
                if time.time() - last_keepalive > 15:
                    yield ":\n\n"
                    last_keepalive = time.time()

            # End-of-stream signal (helps client stop cleanly)
            yield "event: done\ndata: [DONE]\n\n"

        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(sse(), media_type="text/event-stream", headers=headers)
