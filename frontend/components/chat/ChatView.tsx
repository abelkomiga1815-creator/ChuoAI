'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatWelcome } from '@/components/chat/ChatWelcome';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Skeleton';
import { useChat } from '@/hooks/useChat';
import { api } from '@/lib/api';

interface ChatViewProps {
  /** Conversation id taken from the URL, if any. */
  conversationId?: string;
  /** Question handed over from the dashboard composer. */
  pendingQuestion?: string;
}

export function ChatView({ conversationId, pendingQuestion }: ChatViewProps) {
  const router = useRouter();
  const {
    messages,
    isLoading,
    isStreaming,
    error,
    conversationId: storeId,
    sendMessage,
    regenerate,
    setConversation,
    clearChat,
    stopGeneration,
  } = useChat();

  const scrollRef = useRef<HTMLDivElement>(null);
  const failedRef = useRef(false);
  const contentKey = messages
    .map((m) => (m.id + m.content.length).toString())
    .join('|');

  // Auto-scroll to the latest message
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [isStreaming, messages.length, contentKey]);

  // Load an existing conversation from the URL
  const loadConversation = useCallback(async () => {
    if (!conversationId || storeId === conversationId) return;
    try {
      const conv = await api.getConversation(conversationId);
      setConversation(conv.id, conv.messages || []);
    } catch {
      // Conversation not found/accessible -> start fresh
      clearChat();
    }
  }, [conversationId, storeId, setConversation, clearChat]);

  useEffect(() => {
    loadConversation();
  }, [loadConversation]);

  // Fire a question handed off from the dashboard composer
  useEffect(() => {
    if (!pendingQuestion || messages.length > 0 || failedRef.current) return;
    failedRef.current = true;
    clearChat();
    sendMessage(pendingQuestion);
    router.replace('/chat', { scroll: false });
  }, [pendingQuestion, messages.length, clearChat, sendMessage, router]);

  const handleSend = useCallback(
    async (content: string) => {
      const newId = await sendMessage(content);
      // Publish the conversation id so the URL matches the current thread.
      if (newId && newId !== storeId && !conversationId) {
        router.replace(`/chat/${newId}`, { scroll: false });
      }
    },
    [sendMessage, storeId, conversationId, router]
  );

  return (
    <div className="flex flex-col overflow-hidden" style={{ height: 'calc(100vh - 3.5rem)' }}>
      {messages.length === 0 ? (
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <ChatWelcome onSuggestionClick={handleSend} />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto scrollbar-thin" ref={scrollRef}>
          <div className="mx-auto max-w-3xl py-4">
            <div className="mb-4 flex items-center justify-between px-4">
              <p className="text-xs font-medium text-muted-foreground">
                {messages.length} {messages.length === 1 ? 'message' : 'messages'} · GPT-OSS 120B
              </p>
              <Button variant="ghost" size="sm" onClick={() => router.push('/chat')}>
                New chat
              </Button>
            </div>

            {messages.map((message, index) => {
              const isLast = index === messages.length - 1;
              return (
                <ChatMessage
                  key={message.id || index}
                  message={message}
                  isStreaming={isStreaming && isLast && message.role === 'ASSISTANT'}
                  onRegenerate={isLast && message.role === 'ASSISTANT' ? regenerate : undefined}
                  onStop={stopGeneration}
                />
              );
            })}

            {isLoading && messages.length === 0 && (
              <div className="flex justify-center py-8">
                <Spinner className="h-6 w-6 text-primary" />
              </div>
            )}

            {error && (
              <div className="mx-4 mb-4 flex items-center justify-between rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                <span>{error}</span>
                <button
                  type="button"
                  onClick={() => clearChat()}
                  className="ml-3 text-xs font-medium underline underline-offset-2"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <ChatInput
        onSend={handleSend}
        onStop={stopGeneration}
        isLoading={isLoading}
        isStreaming={isStreaming}
      />
    </div>
  );
}