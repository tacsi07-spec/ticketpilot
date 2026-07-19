type ListCardProps = {
  title: string;
  items: string[];
};

export function ListCard({ title, items }: ListCardProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-gray-900">
        {title}
      </h2>

      <ol className="space-y-3">
        {items.map((item, index) => (
          <li
            key={`${title}-${index}`}
            className="flex gap-3 text-gray-700"
          >
            <span className="flex h-7 min-w-7 items-center justify-center rounded-full bg-gray-100 text-sm font-semibold">
              {index + 1}
            </span>

            <span className="pt-0.5">{item}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}