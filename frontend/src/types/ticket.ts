export type ReplyLanguage = "German" | "English";

export type TicketAnalysis = {
  category: string;
  priority: string;
  priority_reason: string;
  confidence_score: number;
  confidence_reason: string;
  problem_summary: string;
  likely_causes: string[];
  troubleshooting_steps: string[];
  powershell_commands: string[];
  security_notes: string[];
  information_needed: string[];
  estimated_resolution_time: string;
  user_reply: string;
};