'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowUp } from 'lucide-react';

const SUGGESTIONS = [
  'Understand TCU admission requirements',
  'Compare universities for a programme',
  'How does TCU allocate students?',
  'Check my eligibility for Medicine',
];

export function DashboardComposer() {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    router.push(`/chat?q=${encodeURIComponent(trimmed)}`);
  }

  function handleSubmit() {
    submit(message);
    setMessage('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="w-full">
      <div className="flex items-end gap-2 rounded-2xl border bg-card p-2 shadow-sm transition-shadow focus-within:ring-2 focus-within:ring-primary/25">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            e.target.style.height = 'auto';
            e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
          }}
          onKeyDown={handleKeyDown}
          placeholder="Ask about universities, programmes, admission, TCU, funding…"
          rows={1}
          className="flex-1 resize-none bg-transparent px-2 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none scrollbar-thin"
          style={{ maxHeight: '160px' }}
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!message.trim()}
          aria-label="Ask ChuoAI"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          <ArrowUp className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground">
        Enter to send · Shift+Enter for a new line
      </p>
    </div>
  );
}

export function SuggestionChips() {
  const router = useRouter();
  return (
    <div className="mt-4 flex flex-wrap justify-center gap-2">
      {SUGGESTIONS.map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => router.push(`/chat?q=${encodeURIComponent(s)}`)}
          className="rounded-full border bg-card px-3.5 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-primary"
        >
          {s}
        </button>
      ))}
    </div>
  );
}