"use client";

import { useState } from "react";

type PowerShellCardProps = {
  commands: string[];
};

export function PowerShellCard({
  commands,
}: PowerShellCardProps) {
  const [copiedCommand, setCopiedCommand] =
    useState<number | null>(null);

  if (commands.length === 0) {
    return null;
  }

  async function copyCommand(
    command: string,
    index: number
  ) {
    await navigator.clipboard.writeText(command);
    setCopiedCommand(index);

    window.setTimeout(() => {
      setCopiedCommand(null);
    }, 2000);
  }

  return (
    <section className="rounded-xl bg-gray-950 p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-white">
        PowerShell Commands
      </h2>

      <div className="space-y-4">
        {commands.map((command, index) => (
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
                onClick={() =>
                  copyCommand(command, index)
                }
                className="rounded-md px-3 py-1 text-sm text-gray-300 transition hover:bg-gray-800 hover:text-white"
              >
                {copiedCommand === index
                  ? "Copied!"
                  : "Copy"}
              </button>
            </div>

            <pre className="overflow-x-auto p-4 text-sm text-green-300">
              <code>{command}</code>
            </pre>
          </div>
        ))}
      </div>
    </section>
  );
}