interface AnswerViewProps {
  answer: string;
  onCitationClick: (index: number) => void;
  selectedIndex: number | null;
}

const CITATION_RE = /\[(\d+)\]/g;

export function AnswerView({ answer, onCitationClick, selectedIndex }: AnswerViewProps) {
  const parts: Array<{ type: "text" | "cite"; value: string; index?: number }> = [];
  let last = 0;
  let match: RegExpExecArray | null;
  const re = new RegExp(CITATION_RE.source, "g");
  while ((match = re.exec(answer)) !== null) {
    if (match.index > last) {
      parts.push({ type: "text", value: answer.slice(last, match.index) });
    }
    parts.push({ type: "cite", value: match[0], index: Number(match[1]) });
    last = match.index + match[0].length;
  }
  if (last < answer.length) {
    parts.push({ type: "text", value: answer.slice(last) });
  }

  if (parts.length === 0) {
    return <div className="answer-body">{answer}</div>;
  }

  return (
    <div className="answer-body" data-testid="answer-body">
      {parts.map((part, i) =>
        part.type === "cite" && part.index !== undefined ? (
          <button
            key={`${i}-${part.index}`}
            type="button"
            className={`citation-link ${selectedIndex === part.index ? "selected" : ""}`}
            onClick={() => onCitationClick(part.index!)}
            aria-label={`Open source reference ${part.index}`}
            data-testid={`citation-link-${part.index}`}
          >
            {part.value}
          </button>
        ) : (
          <span key={i}>{part.value}</span>
        )
      )}
    </div>
  );
}
