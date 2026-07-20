type Props = {
  score: number;
  reason: string;
};

function getColor(score: number) {
  if (score >= 90) return "bg-green-500";
  if (score >= 75) return "bg-lime-500";
  if (score >= 60) return "bg-yellow-500";
  if (score >= 40) return "bg-orange-500";
  return "bg-red-500";
}

export function ConfidenceCard({
  score,
  reason,
}: Props) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">
        Confidence
      </h2>

      <div className="mb-4 h-4 overflow-hidden rounded-full bg-gray-200">
        <div
          className={`${getColor(score)} h-full transition-all`}
          style={{ width: `${score}%` }}
        />
      </div>

      <p className="text-3xl font-bold">
        {score}%
      </p>

      <p className="mt-3 text-gray-600">
        {reason}
      </p>
    </section>
  );
}