type Props = { url: string | null };

export default function TraceLink({ url }: Props) {
  if (!url) return null;
  return (
    <a href={url} target="_blank" rel="noreferrer" className="text-sm text-accent hover:underline">
      View trace ↗
    </a>
  );
}
