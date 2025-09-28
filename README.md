# AI‑Driven Opportunity Startup Finder

Generate **beautiful, structured startup ideas** in real time.  
This app streams **GitHub‑flavored Markdown** from **Azure OpenAI** (via **FastAPI**) straight into a **Next.js** UI and renders it nicely with **Tailwind Typography**.

---

## ✨ Features
- **Realtime streaming** from Azure OpenAI (Chat Completions with `stream=True`)
- **Clean Markdown** output (GFM) rendered with `react-markdown` + Tailwind `prose`
- **SSE** endpoint (`/api`) served by **FastAPI** (Python Serverless Function on Vercel)
- Minimal setup—one page, one function, production‑ready routing

---

## 🧱 Tech Stack
- **Frontend:** Next.js (Pages Router), React, `react-markdown`, `remark-gfm`, Tailwind CSS, `@tailwindcss/typography`
- **Backend:** FastAPI, Azure OpenAI SDK (`AzureOpenAI`)
- **Infra:** Vercel (Serverless Functions for Python + static hosting)

---

## 📂 Project Structure
--tbd--