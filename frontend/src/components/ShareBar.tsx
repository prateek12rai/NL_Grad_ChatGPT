import { useEffect, useRef } from "react";

interface ShareBarProps {
  open: boolean;
  onClose: () => void;
}

/** Prototype: platform logos only — no share API / external URLs. */
const PLATFORMS: {
  id: string;
  label: string;
  icon: JSX.Element;
}[] = [
  {
    id: "x",
    label: "X",
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="share-icon">
        <path
          fill="currentColor"
          d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
        />
      </svg>
    ),
  },
  {
    id: "whatsapp",
    label: "WhatsApp",
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="share-icon">
        <path
          fill="currentColor"
          d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.435 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"
        />
      </svg>
    ),
  },
  {
    id: "facebook",
    label: "Facebook",
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="share-icon">
        <path
          fill="currentColor"
          d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
        />
      </svg>
    ),
  },
  {
    id: "teams",
    label: "Teams",
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="share-icon">
        <path
          fill="currentColor"
          d="M20.625 8.25h-3.375V5.625A2.625 2.625 0 0014.625 3h-5.25A2.625 2.625 0 006.75 5.625V8.25H3.375A1.125 1.125 0 002.25 9.375v9A2.625 2.625 0 004.875 21h14.25A2.625 2.625 0 0021.75 18.375v-9a1.125 1.125 0 00-1.125-1.125zM8.25 5.625a1.125 1.125 0 011.125-1.125h5.25A1.125 1.125 0 0115.75 5.625V8.25H8.25V5.625zm10.5 12.75a1.125 1.125 0 01-1.125 1.125H4.875a1.125 1.125 0 01-1.125-1.125v-7.5h14.625v7.5z"
        />
      </svg>
    ),
  },
];

export function ShareBar({ open, onClose }: ShareBarProps) {
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="share-bar"
      ref={barRef}
      data-testid="share-bar"
      role="dialog"
      aria-label="Share platforms (prototype)"
    >
      <p className="share-bar-label">Share (coming soon)</p>
      <div className="share-bar-platforms">
        {PLATFORMS.map((p) => (
          <span
            key={p.id}
            className={`share-platform share-platform--${p.id}`}
            data-testid={`share-${p.id}`}
            title={`${p.label} — coming soon`}
            aria-label={`${p.label} share (prototype, not connected)`}
          >
            {p.icon}
          </span>
        ))}
      </div>
    </div>
  );
}
