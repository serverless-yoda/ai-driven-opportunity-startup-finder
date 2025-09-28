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

    "# {Startup Name}\n"
    "## {Tagline}\n"

    "### Overview\n"
    "- {1–2 sentence summary of the product and value proposition}\n"

    "### Assumptions\n"
    "- {only include if required context is missing; list clarifying assumptions used to generate the brief}\n"

    "### Problem\n"
    "- {primary pain point and who experiences it}\n"
    "- {impact of the problem in time/money/risk terms}\n"
    "- {why current alternatives are insufficient}\n"

    "### Evidence & Insights\n"
    "- {supporting signals: trends, regulations, or behavioral data}\n"
    "- {brief summary of user interviews, forums, reviews, or market reports}\n"

    "### Solution\n"
    "- {how the product solves the problem end-to-end}\n"
    "- {what is uniquely better vs. status quo and competitors}\n"

    "### Product (MVP Scope)\n"
    "- {top 3–5 MVP capabilities}\n"
    "- {what’s explicitly out of scope for v1}\n"

    "### AI Agent & System Design\n"
    "- {agent roles with brief responsibilities}\n"
    "- {orchestration: planning/memory/tools/HITL review}\n"
    "- {key integrations (APIs, data sources, SaaS connectors)}\n"
    "- {safety: guardrails, rate limits, PII handling, red-teaming}\n"

    "### Data & Models\n"
    "- {input data sources and frequency}\n"
    "- {model choices (proprietary/open), rationale, fallback strategy}\n"
    "- {eval plan with metrics: accuracy, latency, cost/token}\n"

    "### Target Users & ICP\n"
    "- {primary ICP: role, firmographics, budget owner}\n"
    "- {top jobs-to-be-done and success criteria}\n"
    "- {adjacent/secondary segments}\n"

    "### Market Opportunity\n"
    "- {TAM/SAM/SOM with methodology in 1–2 bullets}\n"
    "- {growth drivers, timing, and macro/tech tailwinds}\n"

    "### Competitive Landscape\n"
    "- {key competitors/alternatives and how we differ}\n"
    "- {switching costs or lock-in factors}\n"

    "### Differentiation & Moat\n"
    "- {data advantage, workflow advantage, distribution, or network effects}\n"
    "- {IP posture: proprietary prompts, fine-tuning, or integrations}\n"

    "### Monetization & Pricing\n"
    "- {primary model: subscription/seat/usage hybrid}\n"
    "- {tiers with rough price ranges and feature gates}\n"
    "- {add-ons/marketplace revenue and service upsells}\n"

    "### Unit Economics (Snapshot)\n"
    "- {COGS drivers: model inference, data, infra}\n"
    "- {target gross margin % and levers to improve it}\n"
    "- {payback period target and CAC assumptions}\n"

    "### Go-to-Market Strategy\n"
    "- {initial channels: community, partnerships, outbound, PLG}\n"
    "- {sales motion: self-serve → assisted → enterprise}\n"
    "- {activation funnel: key steps to first value}\n"

    "### Security, Privacy & Compliance\n"
    "- {data flow, storage, and retention}\n"
    "- {PII handling, encryption, and access controls}\n"
    "- {relevant standards/regulations (e.g., SOC 2, GDPR) and roadmap}\n"

    "### Risks & Mitigations\n"
    "- {top technical/product/market risks}\n"
    "- {concrete mitigation steps and contingency plans}\n"

    "### Implementation Plan & Timeline\n"
    "- {phase 0–1: discovery & prototyping (weeks)}\n"
    "- {phase 2: MVP build & internal alpha (weeks)}\n"
    "- {phase 3: beta, metrics, and hardening (weeks)}\n"

    "### Roadmap\n"
    "- {0–3 months: near-term features and success metrics}\n"
    "- {3–6 months: scale features, reliability, and ops}\n"
    "- {6–12 months: platform/marketplace or adjacent products}\n"

    "### Resource Plan\n"
    "- {core team roles and approximate monthly cost}\n"
    "- {external vendors/partners and responsibilities}\n"

    "### Financial Snapshot (12 Months)\n"
    "- {high-level projection: revenue range, burn, runway}\n"
    "- {key assumptions that drive the model}\n"

    "### Success Metrics & North Star\n"
    "- {north-star metric}\n"
    "- {activation/retention/expansion metrics with target ranges}\n"

    "### FAQ\n"
    "- {anticipated tough questions and crisp answers}\n"

    "### Next Steps\n"
    "- {immediate actions to validate risk and move forward}\n\n"

    "Rules:\n"
    "- Do not wrap the response in code fences.\n"
    "- Do not include literal braces; replace with concrete content.\n"
    "- Use concise, scannable bullets (no long paragraphs).\n"
    "- Quantify wherever possible with ranges and units (e.g., %, $, days, ms).\n"
    "- Prefer plain English; avoid jargon unless necessary, then define it.\n"
    "- If information is missing, add an Assumptions section and proceed.\n"
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
