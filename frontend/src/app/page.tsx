"use client";

import { AnalysisResult } from "@/components/AnalysisResult";
import { TicketInput } from "@/components/TicketInput";
import { useTicketAnalysis } from "@/hooks/useTicketAnalysis";

export default function Home() {
  const {
    ticket,
    setTicket,
    result,
    loading,
    errorMessage,
    replyLanguage,
    setReplyLanguage,
    handleAnalyze,
  } = useTicketAnalysis();

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

        <TicketInput
          ticket={ticket}
          loading={loading}
          errorMessage={errorMessage}
          replyLanguage={replyLanguage}
          onTicketChange={setTicket}
          onReplyLanguageChange={setReplyLanguage}
          onAnalyze={handleAnalyze}
        />

        {result && <AnalysisResult result={result} />}
      </div>
    </main>
  );
}