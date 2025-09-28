// saas/pages/index.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ⬇️ NEW: normalize streamed Markdown so GFM renders correctly
function normalizeMarkdown(raw: string): string {
  return raw
    // ensure headings start on a new line (or blank line) if they were glued to previous text
    .replace(/([^\n])(\#{1,6}\s)/g, "$1\n\n$2")
    // ensure a blank line before any heading (avoid triple newlines later)
    .replace(/\n(\#{1,6}\s)/g, "\n\n$1")
    // ensure list items start on a new line
    .replace(/([^\n])([*-]\s)/g, "$1\n$2")
    // fix cases like "### Problem- item" → "### Problem\n- item"
    .replace(/(#{3,6} [^\n]+)-\s/g, "$1\n- ")
    // collapse >2 blank lines to exactly two
    .replace(/\n{3,}/g, "\n\n");
}

export default function Home() {
  const [idea, setIdea] = useState<string>("…loading");
  const bufferRef = useRef<string>("");

  useEffect(() => {
    const es = new EventSource("/api"); // FastAPI SSE route (see server note below)
    let raf = 0;

    es.onmessage = (e) => {
      bufferRef.current += e.data;
      const fixed = normalizeMarkdown(bufferRef.current);
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setIdea(fixed));
    };

    // Optional: if your server emits a "done" event, close cleanly.
    es.addEventListener("done", () => es.close());

    es.onerror = () => {
      console.error("SSE error; closing connection");
      es.close();
    };

    return () => {
      cancelAnimationFrame(raf);
      es.close();
    };
  }, []);

  const isLoading = idea === "…loading";

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            AI-Driven Opportunity Startup Finder
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Discover untapped markets and profitable ideas with AI-powered insights
          </p>
        </header>

        {/* Content Card */}
        <div className="max-w-3xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 backdrop-blur-lg bg-opacity-95">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-pulse text-gray-400">
                  Generating your business idea...
                </div>
              </div>
            ) : (
              <div className="markdown-content text-gray-700 dark:text-gray-300">
                {/* Tailwind Typography styles Markdown nicely */}
                <article className="prose prose-slate dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {idea}
                  </ReactMarkdown>
                </article>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
