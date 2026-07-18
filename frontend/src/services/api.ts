const API_URL = "http://127.0.0.1:8000";

export async function analyzeTicket(ticket: string) {
  const response = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ticket,
    }),
  });

  if (!response.ok) {
    throw new Error("Backend error");
  }

  return response.json();
}