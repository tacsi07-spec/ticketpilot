"use client";

import { useState } from "react";

import { analyzeTicket } from "@/services/api";
import type {
  ReplyLanguage,
  TicketAnalysis,
} from "@/types/ticket";

export function useTicketAnalysis() {
  const [ticket, setTicket] = useState("");
  const [result, setResult] =
    useState<TicketAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");
  const [replyLanguage, setReplyLanguage] =
    useState<ReplyLanguage>("German");

  async function handleAnalyze() {
    const trimmedTicket = ticket.trim();

    if (trimmedTicket.length < 5) {
      setErrorMessage(
        "Please enter a more detailed IT support ticket."
      );
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

  return {
    ticket,
    setTicket,
    result,
    loading,
    errorMessage,
    replyLanguage,
    setReplyLanguage,
    handleAnalyze,
  };
}