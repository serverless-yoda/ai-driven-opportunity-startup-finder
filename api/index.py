# api/index.py
import os
from openai import AzureOpenAI
from fastapi import FastAPI

# Hard-fail early if anything is missing (shows up in Vercel logs)
required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]
missing  = [k for k in required if not os.getenv(k)]
if missing:
    raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

#client = AzureOpenAI(
#    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
#    api_key=os.environ["AZURE_OPENAI_API_KEY"],
#    api_version="2024-06-01",  # use the version shown in AI Foundry "View code"
#)


app = FastAPI()

@app.get("/api")
def startup_idea():
    endpoint = "https://dgrea-mfxaprip-swedencentral.cognitiveservices.azure.com/"
    model_name = "gpt-5-nano"
    deployment = "gpt-5-nano"

    subscription_key = os.environ["AZURE_OPENAI_API_KEY"]
    api_version = "2024-12-01-preview"

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

    response = client.chat.completions.create(

        messages=[
            {
                "role": "user",
                "content": 
                """
                    Invent a unique and innovative business idea that leverages AI Agents to solve a real-world problem 
                    or create a new market opportunity. The idea should include:

                    - A clear description of the problem it addresses.
                    - How AI Agents will be used (their roles, autonomy, and interaction).
                    - The target audience or industry.
                    - A potential monetization model.
                    - Make it practical yet forward-thinking.
                """
            }
        ],

        #---
        
        max_completion_tokens=16384,
        model=deployment
    )

    return response.choices[0].message.content



