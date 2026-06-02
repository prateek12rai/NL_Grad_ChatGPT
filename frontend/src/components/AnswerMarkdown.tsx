import type { ReactNode } from "react";

interface AnswerMarkdownProps {
  answer: string;
  onCitationClick: (index: number) => void;
  selectedIndex: number | null;
}

const CITATION_RE = /\[(\d+)\]/g;

function normalizeAnswerMarkdown(answer: string): string {
  const raw = (answer ?? "").replace(/\r\n/g, "\n");
  const lines = raw.split("\n");
  const out: string[] = [];

  const headingWords =
    "(?:article summary|summary|key points|important points|direct answer|top articles|sources|limitations|methods|results|findings|clinical implications)";
  const headerOnly = new RegExp(`^${headingWords}\\s*$`, "i");
  for (const line of lines) {
    const original = line;
    const trimmed = original.trim();
    if (!trimmed) {
      out.push("");
      continue;
    }

    // Normalize Markdown headings from the LLM: "## Article Summary" -> "**Article Summary:**"
    const markdownHeading = trimmed.match(/^#{1,6}\s+(.+)$/);
    if (markdownHeading) {
      const text = markdownHeading[1].replace(/:$/, "").trim();
      out.push(`**${text}:**`);
      continue;
    }

    // Repair malformed bold headings like "*Summary:**" before bullet handling.
    const malformedBoldHeading = trimmed.match(/^\*([^*]+):\*\*$/);
    if (malformedBoldHeading) {
      out.push(`**${malformedBoldHeading[1]}:**`);
      continue;
    }

    // Ensure common section headers are bolded even if the LLM forgets.
    // Examples: "Summary:", "Key points:", "Direct answer:", "Sources:"
    const header = trimmed.match(
      new RegExp(`^(${headingWords})\\s*:(.*)$`, "i")
    );
    if (header) {
      const label = header[1];
      const rest = header[2] ?? "";
      const normalizedLabel =
        label
          .split(/\s+/)
          .map((w) => w[0].toUpperCase() + w.slice(1).toLowerCase())
          .join(" ");
      out.push(`**${normalizedLabel}:**${rest}`);
      continue;
    }

    // Headings sometimes appear as a single word line (no colon).
    if (headerOnly.test(trimmed)) {
      const normalizedLabel =
        trimmed
          .split(/\s+/)
          .map((w) => w[0].toUpperCase() + w.slice(1).toLowerCase())
          .join(" ");
      out.push(`**${normalizedLabel}:**`);
      continue;
    }

    // Normalize bullets from common variants, but do NOT treat markdown bold
    // markers like "**Summary:**" as a "*" bullet.
    const bullet = trimmed.match(/^(?:•|-+\s+|\d+[.)]\s+|\*(?!\*)\s+)(.*)$/);
    if (bullet) {
      out.push(`- ${bullet[1]}`);
      continue;
    }

    out.push(original);
  }

  return out.join("\n");
}

function renderBoldItalic(text: string): ReactNode {
  const parts: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|_[^_]+_)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const token = m[0];
    if (token.startsWith("**")) {
      parts.push(<strong key={`b-${i++}`}>{token.slice(2, -2)}</strong>);
    } else {
      parts.push(<em key={`e-${i++}`}>{token.slice(1, -1)}</em>);
    }
    last = m.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length ? parts : text;
}

function renderInline(
  segment: string,
  onCitationClick: (index: number) => void,
  selectedIndex: number | null,
  keyPrefix: string
): ReactNode[] {
  const nodes: ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;
  const re = new RegExp(CITATION_RE.source, "g");
  let k = 0;
  while ((match = re.exec(segment)) !== null) {
    if (match.index > last) {
      nodes.push(
        <span key={`${keyPrefix}-t-${k++}`}>
          {renderBoldItalic(segment.slice(last, match.index))}
        </span>
      );
    }
    const idx = Number(match[1]);
    nodes.push(
      <button
        key={`${keyPrefix}-c-${idx}`}
        type="button"
        className={`citation-link ${selectedIndex === idx ? "selected" : ""}`}
        onClick={() => onCitationClick(idx)}
        data-testid={`citation-link-${idx}`}
        aria-label={`Open source reference ${idx}`}
      >
        {match[0]}
      </button>
    );
    last = match.index + match[0].length;
  }
  if (last < segment.length) {
    nodes.push(
      <span key={`${keyPrefix}-end`}>{renderBoldItalic(segment.slice(last))}</span>
    );
  }
  return nodes;
}

export function AnswerMarkdown({ answer, onCitationClick, selectedIndex }: AnswerMarkdownProps) {
  const safe = normalizeAnswerMarkdown(answer ?? "");
  const lines = safe.split("\n");
  const blocks: ReactNode[] = [];
  let bulletBuffer: ReactNode[] = [];
  let blockId = 0;

  const flushBullets = () => {
    if (bulletBuffer.length === 0) return;
    blocks.push(
      <ul key={`ul-${blockId++}`} className="answer-list">
        {bulletBuffer}
      </ul>
    );
    bulletBuffer = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      flushBullets();
      blocks.push(<div key={`sp-${blockId++}`} className="answer-spacer" />);
      continue;
    }
    const bullet = trimmed.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      bulletBuffer.push(
        <li key={`li-${blockId}-${bulletBuffer.length}`}>
          {renderInline(bullet[1], onCitationClick, selectedIndex, `b${blockId}`)}
        </li>
      );
      continue;
    }
    flushBullets();
    if (trimmed.startsWith("**") && trimmed.endsWith("**") && !trimmed.slice(2, -2).includes("**")) {
      blocks.push(
        <p key={`h-${blockId++}`} className="answer-heading">
          <strong>{trimmed.slice(2, -2)}</strong>
        </p>
      );
    } else if (trimmed.startsWith("**") && trimmed.slice(2).includes("**")) {
      // LLM sometimes emits lines like "**Summary:** ..." (with bold token but not ending with **).
      // Render the whole line as a headline block so the label stays prominent.
      blocks.push(
        <p key={`h-${blockId++}`} className="answer-heading">
          {renderInline(trimmed, onCitationClick, selectedIndex, `h${blockId}`)}
        </p>
      );
    } else {
      blocks.push(
        <p key={`p-${blockId++}`} className="answer-para">
          {renderInline(trimmed, onCitationClick, selectedIndex, `p${blockId}`)}
        </p>
      );
    }
  }
  flushBullets();

  return (
    <div className="answer-body answer-markdown" data-testid="answer-body">
      {blocks}
    </div>
  );
}
