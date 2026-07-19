"use client";

import { useState } from "react";

type ReplyCardProps = {
  reply: string;
};

export function ReplyCard({
  reply,
}: ReplyCardProps) {
  const [copied, setCopied] = useState(false);

  async function copyReply() {
    await navigator.clipboard.writeText(reply);
    setCopied(true);

    window.setTimeout(() => {
      setCopied(false);
    }, 2000);
  }

  return (
    <section className="rounded-xl border border-blue-200 bg-blue-50 p-6 shadow-sm">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-gray-900">
          End-User Reply
        </h2>

        <button
          type="button"
          onClick={copyReply}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-800 transition hover:bg-gray-100"
        >
          {copied ? "Copied!" : "Copy Reply"}
        </button>
      </div>

      <p className="whitespace-pre-wrap leading-7 text-gray-700">
        {reply}
      </p>
    </section>
  );
}