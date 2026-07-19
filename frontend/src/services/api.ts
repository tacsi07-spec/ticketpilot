const API_URL = "http://127.0.0.1:8000";

export async function analyzeTicket(
  ticket: string,
  replyLanguage: "German" | "English"
) {
  const response = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ticket,
      reply_language: replyLanguage,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    throw new Error(
      errorData?.detail ?? "The backend returned an error."
    );
  }

  return response.json();
}