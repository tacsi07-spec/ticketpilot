"use client";

import { useState } from "react";
import { analyzeTicket } from "../services/api";

export default function Home() {
  const [ticket, setTicket] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    try {
      setLoading(true);

      const data = await analyzeTicket(ticket);

      setResult(data);
    } catch (error) {
      alert("Backend connection failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-100 flex items-center justify-center p-8">
      <div className="bg-white shadow-xl rounded-xl p-8 max-w-4xl w-full">

        <h1 className="text-4xl font-bold mb-2">
          TicketPilot
        </h1>

        <p className="text-gray-500 mb-6">
          AI Assistant for IT Support Engineers
        </p>

        <textarea
          value={ticket}
          onChange={(e) => setTicket(e.target.value)}
          placeholder="Describe your IT issue..."
          className="w-full border rounded-lg p-4 h-48"
        />

        <button
          onClick={handleAnalyze}
          className="mt-4 bg-black text-white px-6 py-3 rounded-lg"
        >
          {loading ? "Analyzing..." : "Analyze Ticket"}
        </button>

        {result && (
          <pre className="mt-8 bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}

      </div>
    </main>
  );
}