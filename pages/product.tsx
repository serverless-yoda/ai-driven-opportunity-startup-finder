"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@clerk/nextjs";
import { fetchEventSource, EventSourceMessage } from "@microsoft/fetch-event-source";

// Optional: normalize streamed Markdown so headings/lists render correctly
function normalizeMarkdown(raw: string): string {
  return raw
    .replace(/([^\n])(\#{1,6}\s)/g, "$1\n\n$2")
    .replace(/\n(\#{1,6}\s)/g, "\n\n$1")
    .replace(/([^\n])([*-]\s)/g, "$1\n$2")
    .replace(/(#{3,6}\s[^\n]+)-\s/g, "$1\n- ")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/\s*\[DONE\]\s*$/g, "");
}

export default function Product() {
  const { getToken } = useAuth();
  const [idea, setIdea] = useState<string>("…loading");
  const bufferRef = useRef<string>("");

  useEffect(() => {
    let cancelled = false;
    const ctrl = new AbortController();
    let raf = 0;

    (async () => {
      const jwt = await getToken();
      if (!jwt) {
        setIdea("Authentication required");
        return;
      }

      await fetchEventSource("/api", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${jwt}`,
          Accept: "text/event-stream",
        },
        signal: ctrl.signal,
        openWhenHidden: true,

        // ✅ async ensures Promise<void> return type
        async onopen(res: Response): Promise<void> {
          const isSSE =
            res.ok && res.headers.get("content-type")?.includes("text/event-stream");
          if (!isSSE) {
            throw new Error(`Unexpected response: ${res.status} ${res.statusText}`);
          }
        },

        onmessage(ev: EventSourceMessage) {
          if (cancelled) return;

          // Close when server signals completion
          if (ev.event === "done" || ev.data === "[DONE]") {
            ctrl.abort();
            return;
          }

          bufferRef.current += ev.data;
          const fixed = normalizeMarkdown(bufferRef.current);

          cancelAnimationFrame(raf);
          raf = requestAnimationFrame(() => setIdea(fixed));
        },

        onerror(err) {
          console.error("SSE error:", err);
          // Let the library handle retries; don't throw
        },
      });
    })();

    return () => {
      cancelled = true;
      ctrl.abort();
      cancelAnimationFrame(raf);
    };
  }, [getToken]);

  const isLoading = idea === "…loading";

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-12">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            AI-Driven Opportunity Startup Finder
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Discover untapped markets and profitable ideas with AI-powered insights
          </p>
        </header>

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
                <article className="prose prose-slate dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{idea}</ReactMarkdown>
                </article>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
