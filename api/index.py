# saas/api/index.py
import os
from openai import AzureOpenAI
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials 

app = FastAPI()

clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

SYSTEM_PROMPT = (
    "You are a product ideation assistant. Always respond in GitHub-Flavored Markdown "
    "with exactly this structure and no preamble or epilogue:\n\n"
    "# {Title}\n"
    "## {Subtitle}\n"
    "### Problem\n"
    "- {bullet}\n"
    "- {bullet}\n"
    "### AI Agent Design\n"
    "- {bullet}\n"
    "- {bullet}\n"
    "### Target Users\n"
    "- {bullet}\n"
    "### Monetization\n"
    "- {bullet}\n\n"
    "Rules:\n"
    "- Do not wrap the response in code fences.\n"
    "- Do not include literal braces; replace with concrete content.\n"
    "- Use concise, scannable bullets.\n"
)

def _stream_idea_chunks():
    endpoint    = "https://dgrea-mfxaprip-swedencentral.cognitiveservices.azure.com/"
    deployment  = "gpt-5-nano"                 # deployment name
    api_version = "2024-12-01-preview"
    api_key     = os.environ["AZURE_OPENAI_API_KEY"]

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=api_key,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Invent a unique and innovative business idea that leverages AI Agents to solve a real-world problem "
                "or create a new market opportunity. Make it practical and not complicated and yet forward‑thinking."
            ),
        },
    ]

    stream = client.chat.completions.create(
        model=deployment,
        stream=True,
        messages=messages,
        # If the API complains about this param name, switch to `max_tokens=16384`
        max_completion_tokens=16384,
    )

    # Stream token deltas as SSE events
    for chunk in stream:
        delta = getattr(chunk.choices[0].delta, "content", None) if chunk.choices else None
        if delta:
            # Each SSE frame must end with a blank line
            yield f"data: {delta}\n\n"

    # Signal completion (optional but useful for the client)
    yield "event: done\ndata: [DONE]\n\n"

@app.get("/api")
def stream_sse(creds: HTTPAuthorizationCredentials = Depends(clerk_guard)):
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # Some proxies buffer; this header asks them not to (harmless if ignored)
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(_stream_idea_chunks(), media_type="text/event-stream", headers=headers)
