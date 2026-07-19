import type { ReplyLanguage } from "@/types/ticket";

type TicketInputProps = {
  ticket: string;
  loading: boolean;
  errorMessage: string;
  replyLanguage: ReplyLanguage;
  onTicketChange: (value: string) => void;
  onReplyLanguageChange: (value: ReplyLanguage) => void;
  onAnalyze: () => void;
};

export function TicketInput({
  ticket,
  loading,
  errorMessage,
  replyLanguage,
  onTicketChange,
  onReplyLanguageChange,
  onAnalyze,
}: TicketInputProps) {
  return (
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
        onChange={(event) => onTicketChange(event.target.value)}
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
            onReplyLanguageChange(
              event.target.value as ReplyLanguage
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
          onClick={onAnalyze}
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
  );
}