type ClassificationCardProps = {
  category: string;
  priority: string;
  priorityReason: string;
};

function getPriorityClasses(priority: string) {
  switch (priority) {
    case "Critical":
      return "bg-red-100 text-red-800";
    case "High":
      return "bg-orange-100 text-orange-800";
    case "Medium":
      return "bg-yellow-100 text-yellow-800";
    case "Low":
      return "bg-green-100 text-green-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
}

export function ClassificationCard({
  category,
  priority,
  priorityReason,
}: ClassificationCardProps) {
  return (
    <section className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          Category
        </p>

        <p className="mt-2 text-xl font-semibold text-gray-900">
          {category}
        </p>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          Priority
        </p>

        <div className="mt-2">
          <span
            className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${getPriorityClasses(
              priority
            )}`}
          >
            {priority}
          </span>
        </div>

        <p className="mt-3 text-sm leading-6 text-gray-600">
          {priorityReason}
        </p>
      </div>
    </section>
  );
}