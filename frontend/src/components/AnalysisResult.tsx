import type { TicketAnalysis } from "@/types/ticket";

import { ClassificationCard } from "./ClassificationCard";
import { ConfidenceCard } from "./ConfidenceCard";
import { ListCard } from "./ListCard";
import { PowerShellCard } from "./PowerShellCard";
import { ReplyCard } from "./ReplyCard";

type AnalysisResultProps = {
  result: TicketAnalysis;
};

export function AnalysisResult({
  result,
}: AnalysisResultProps) {
  return (
    <div className="mt-8 space-y-6">
      <ClassificationCard
        category={result.category}
        priority={result.priority}
        priorityReason={result.priority_reason}
      />

      <ConfidenceCard
        score={result.confidence_score}
        reason={result.confidence_reason}
      />

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-xl font-semibold text-gray-900">
          Problem Summary
        </h2>

        <p className="leading-7 text-gray-700">
          {result.problem_summary}
        </p>
      </section>

      <ListCard
        title="Likely Causes"
        items={result.likely_causes}
      />

      <ListCard
        title="Troubleshooting Steps"
        items={result.troubleshooting_steps}
      />

      <PowerShellCard
        commands={result.powershell_commands}
      />

      <ListCard
        title="Security Notes"
        items={result.security_notes}
      />

      <ListCard
        title="Information Needed"
        items={result.information_needed}
      />

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-xl font-semibold text-gray-900">
          Estimated Resolution Time
        </h2>

        <p className="text-gray-700">
          {result.estimated_resolution_time}
        </p>
      </section>

      <ReplyCard reply={result.user_reply} />
    </div>
  );
}