export type ReplyLanguage = "German" | "English";

export type TicketAnalysis = {
  problem_summary: string;
  likely_causes: string[];
  troubleshooting_steps: string[];
  powershell_commands: string[];
  security_notes: string[];
  information_needed: string[];
  estimated_resolution_time: string;
  user_reply: string;
};