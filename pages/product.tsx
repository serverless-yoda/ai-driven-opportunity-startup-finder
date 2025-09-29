// pages/product.tsx
"use client";

import Head from "next/head";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
// ⚠️ Do NOT use remarkBreaks; it breaks Markdown semantics for lists/paragraphs
// import remarkBreaks from "remark-breaks";
import { useAuth, Protect, PricingTable, UserButton } from "@clerk/nextjs";
import { fetchEventSource } from "@microsoft/fetch-event-source";

/**
 * Minimal normalization for streamed markdown:
 * - Remove literal "A blank line"
 * - Ensure a newline after headings
 * - Collapse 3+ newlines to exactly 2
 * (Avoid aggressive transformations that can harm lists/paragraphs)
 */
function normalizeMarkdown(text: string): string {
  return text
}

function IdeaGenerator() {
  const { getToken } = useAuth();
  const [idea, setIdea] = useState<string>("…loading");

  const bufferRef = useRef<string>("");
  const rafRef = useRef<number>(0);

  useEffect(() => {
    bufferRef.current = "";
    let aborted = false;
    const abortCtrl = new AbortController();

    (async () => {
      // If you use a Clerk JWT template for backend validation:
      // const jwt = await getToken({ template: "backend" });
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
        signal: abortCtrl.signal,
        async onopen(res) {
          const ctype = res.headers.get("content-type") || "";
          if (!res.ok || !ctype.includes("text/event-stream")) {
            const body = await res.text().catch(() => "");
            console.error("SSE open failed:", res.status, body);
            throw new Error(`HTTP ${res.status}`);
          }
          bufferRef.current = "";
          setIdea("…loading");
        },
        onmessage(ev) {
          if (aborted) return;

          if (ev.event === "done" || ev.data === "[DONE]") {
            aborted = true;
            abortCtrl.abort();
            setIdea((prev) => normalizeMarkdown(bufferRef.current || prev));
            return;
          }

          if (ev.event === "error") {
            bufferRef.current += `\n\n**Server Error:** ${ev.data}\n`;
            setIdea(bufferRef.current);
            return;
          }

          // --- CHANGE START: ensure a boundary between events ---
          // If the new chunk starts a block (heading/list) and the buffer doesn't end with a newline,
          // insert one so things like "## Idea Name- Bullet" don't glue together.
          const startsBlock = /^(?:-\s|\d+\.\s|#{1,6}\s)/.test(ev.data);
          const needsBreak =
            bufferRef.current.length > 0 && !bufferRef.current.endsWith("\n") && startsBlock;

          // Always append a newline after each SSE event to keep lines intact across chunk boundaries
          bufferRef.current += (needsBreak ? "\n" : "") + ev.data + "\n";
          // --- CHANGE END ---

          // Debounce UI updates to reduce flicker during streaming
          if (!rafRef.current) {
            rafRef.current = requestAnimationFrame(() => {
              rafRef.current = 0;
              setIdea(normalizeMarkdown(bufferRef.current));
            });
          }
        },
        onerror(err) {
          console.error("SSE error:", err);
          // Let fetch-event-source retry by not throwing
        },
        openWhenHidden: true,
      });
    })();

    return () => {
      aborted = true;
      abortCtrl.abort();
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [getToken]);

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Header */}
      <header className="text-center mb-12">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
          Business Idea Generator
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          AI-powered innovation at your fingertips
        </p>
      </header>

      {/* Content Card */}
      <div className="max-w-3xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 backdrop-blur-lg bg-opacity-95">
          {idea === "…loading" ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-pulse text-gray-400">
                Generating your business idea...
              </div>
            </div>
          ) : (
            // ✅ Tailwind Typography styles for clean Markdown rendering
            <div className="prose prose-slate dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {idea}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ProductPage() {
  return (
    <>
      {/* ✅ Satisfies @next/next/no-title-in-document-head */}
      <Head>
        <title>Business Idea Generator</title>
        <meta name="robots" content="noindex" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        {/* User Menu in Top Right */}
        <div className="absolute top-4 right-4">
          <UserButton showName={true} />
        </div>

        {/* Subscription Protection */}
        <Protect
          plan="premium_subscription"
          fallback={
            <div className="container mx-auto px-4 py-12">
              <header className="text-center mb-12">
                <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
                  Choose Your Plan
                </h1>
                <p className="text-gray-600 dark:text-gray-400 text-lg mb-8">
                  Unlock unlimited AI-powered business ideas
                </p>
              </header>
              <div className="max-w-4xl mx-auto">
                <PricingTable />
              </div>
            </div>
          }
        >
          <IdeaGenerator />
        </Protect>
      </main>
    </>
  );
}
