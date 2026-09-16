// frontend/components/chat/ChatInput.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Square, Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isLoading?: boolean;
  isStreaming?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  onStop,
  isLoading,
  isStreaming,
  disabled,
  placeholder = 'Uliza swali lako hapa... / Ask your question here...',
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSubmit = () => {
    const trimmed = message.trim();
    if (!trimmed || isLoading || disabled) return;
    
    onSend(trimmed);
    setMessage('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t bg-background px-4 py-4">
      <div className="mx-auto max-w-3xl">
        <div
          className={cn(
            'relative flex items-end gap-2 rounded-2xl border bg-background p-2 shadow-sm transition-shadow',
            'focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50',
            disabled && 'opacity-50'
          )}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={1}
            className={cn(
              'flex-1 resize-none bg-transparent px-2 py-2 text-sm',
              'placeholder:text-muted-foreground',
              'focus:outline-none',
              'scrollbar-thin'
            )}
            style={{ maxHeight: '200px' }}
          />

          <div className="flex items-center gap-1">
            {/* Attachment button */}
            <button
              type="button"
              className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Attach file"
              disabled={disabled}
            >
              <Paperclip className="h-4 w-4" />
            </button>

            {/* Send / Stop button */}
            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                className="rounded-lg bg-destructive p-2 text-destructive-foreground hover:bg-destructive/90"
                title="Stop generation"
              >
                <Square className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!message.trim() || isLoading || disabled}
                className={cn(
                  'rounded-lg p-2 transition-colors',
                  message.trim() && !isLoading && !disabled
                    ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                    : 'bg-muted text-muted-foreground cursor-not-allowed'
                )}
                title="Send message (Enter)"
              >
                <Send className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        {/* Helper text */}
        <p className="mt-2 text-center text-xs text-muted-foreground">
          ChuoAI inaweza kufanya makosa. Tafadhali thibitisha taarifa muhimu. / ChuoAI can make mistakes. Please verify important information.
        </p>
      </div>
    </div>
  );
}