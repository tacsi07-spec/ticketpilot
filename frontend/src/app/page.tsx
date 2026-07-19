"use client";

import { useState } from "react";
import { analyzeTicket } from "@/services/api";

type TicketAnalysis = {
  problem_summary: string;
  likely_causes: string[];
  troubleshooting_steps: string[];
  powershell_commands: string[];
  security_notes: string[];
  information_needed: string[];
  estimated_resolution_time: string;
  user_reply: string;
};

function ListCard({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-gray-900">{title}</h2>

      <ol className="space-y-3">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="flex gap-3 text-gray-700">
            <span className="flex h-7 min-w-7 items-center justify-center rounded-full bg-gray-100 text-sm font-semibold">
              {index + 1}
            </span>

            <span className="pt-0.5">{item}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default function Home() {
  const [ticket, setTicket] = useState("");
  const [result, setResult] = useState<TicketAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [replyLanguage, setReplyLanguage] =
    useState<"German" | "English">("German");
  const [copiedCommand, setCopiedCommand] = useState<number | null>(null);
  const [replyCopied, setReplyCopied] = useState(false);

  async function handleAnalyze() {
    const trimmedTicket = ticket.trim();

    if (trimmedTicket.length < 5) {
      setErrorMessage("Please enter a more detailed IT support ticket.");
      return;
    }

    try {
      setLoading(true);
      setErrorMessage("");
      setResult(null);

      const data = await analyzeTicket(
        trimmedTicket,
        replyLanguage
      );

      setResult(data);
    } catch (error) {
      console.error(error);

      setErrorMessage(
        "The ticket could not be analyzed. Check whether the backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  async function copyCommand(command: string, index: number) {
    try {
      await navigator.clipboard.writeText(command);
      setCopiedCommand(index);

      window.setTimeout(() => {
        setCopiedCommand(null);
      }, 2000);
    } catch (error) {
      console.error("Could not copy command:", error);
    }
  }

  async function copyUserReply() {
    if (!result) {
      return;
    }

    try {
      await navigator.clipboard.writeText(result.user_reply);
      setReplyCopied(true);

      window.setTimeout(() => {
        setReplyCopied(false);
      }, 2000);
    } catch (error) {
      console.error("Could not copy reply:", error);
    }
  }

  return (
    <main className="min-h-screen bg-gray-100 px-4 py-12 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8">
          <h1 className="text-4xl font-bold tracking-tight text-gray-950">
            TicketPilot
          </h1>

          <p className="mt-2 text-gray-600">
            AI troubleshooting assistant for IT support engineers
          </p>
        </header>

        <section className="rounded-2xl bg-white p-6 shadow-sm sm:p-8">
          <label
            htmlFor="ticket"
            className="mb-3 block text-sm font-semibold text-gray-800"
          >
            IT support ticket
          </label>

          <textarea
            id="ticket"
            value={ticket}
            onChange={(event) => setTicket(event.target.value)}
            placeholder="Example: User cannot connect to the VPN after changing their password..."
            className="min-h-48 w-full resize-y rounded-xl border border-gray-300 p-4 text-gray-900 outline-none transition focus:border-gray-700"
          />

          <div className="mt-4">
            <label
              htmlFor="reply-language"
              className="mb-2 block text-sm font-semibold text-gray-800"
            >
              End-user reply language
            </label>

            <select
              id="reply-language"
              value={replyLanguage}
              onChange={(event) =>
                setReplyLanguage(
                  event.target.value as "German" | "English"
                )
              }
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900"
            >
              <option value="German">German</option>
              <option value="English">English</option>
            </select>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={loading}
              className="rounded-lg bg-gray-950 px-6 py-3 font-semibold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analyzing ticket..." : "Analyze Ticket"}
            </button>

            <span className="text-sm text-gray-500">
              {ticket.length} characters
            </span>
          </div>

          {errorMessage && (
            <p className="mt-4 rounded-lg bg-red-50 p-4 text-sm text-red-700">
              {errorMessage}
            </p>
          )}
        </section>

        {result && (
          <div className="mt-8 space-y-6">
            <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-3 text-xl font-semibold text-gray-900">
                Problem Summary
              </h2>

              <p className="leading-7 text-gray-700">
                {result.problem_summary}
              </p>
            </section>

            <ListCard title="Likely Causes" items={result.likely_causes} />

            <ListCard
              title="Troubleshooting Steps"
              items={result.troubleshooting_steps}
            />

            {result.powershell_commands.length > 0 && (
              <section className="rounded-xl bg-gray-950 p-6 shadow-sm">
                <h2 className="mb-4 text-xl font-semibold text-white">
                  PowerShell Commands
                </h2>

                <div className="space-y-4">
                  {result.powershell_commands.map((command, index) => (
                    <div
                      key={`command-${index}`}
                      className="overflow-hidden rounded-lg bg-black"
                    >
                      <div className="flex items-center justify-between border-b border-gray-800 px-4 py-2">
                        <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                          PowerShell
                        </span>

                        <button
                          type="button"
                          onClick={() => copyCommand(command, index)}
                          className="rounded-md px-3 py-1 text-sm text-gray-300 transition hover:bg-gray-800 hover:text-white"
                        >
                          {copiedCommand === index ? "Copied!" : "Copy"}
                        </button>
                      </div>

                      <pre className="overflow-x-auto p-4 text-sm text-green-300">
                        <code>{command}</code>
                      </pre>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <ListCard
              title="Security Notes"
              items={result.security_notes}
            />

            <ListCard
              title="Information Needed"
              items={result.information_needed}
            />

            <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-2 text-xl font-semibold text-gray-900">
                Estimated Resolution Time
              </h2>

              <p className="text-gray-700">
                {result.estimated_resolution_time}
              </p>
            </section>

            <section className="rounded-xl border border-blue-200 bg-blue-50 p-6 shadow-sm">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-semibold text-gray-900">
                  End-User Reply
                </h2>

                <button
                  type="button"
                  onClick={copyUserReply}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-800 transition hover:bg-gray-100"
                >
                  {replyCopied ? "Copied!" : "Copy Reply"}
                </button>
              </div>

              <p className="whitespace-pre-wrap leading-7 text-gray-700">
                {result.user_reply}
              </p>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}