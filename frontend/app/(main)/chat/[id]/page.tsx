'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useChat } from '@/hooks/useChat';
import { ChatView } from '@/components/chat/ChatView';

export default function ConversationPage() {
  const params = useParams<{ id: string }>();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;

  // If the store still holds this thread (e.g. soft navigation), make sure we
  // don't reload it. Otherwise ChatView fetches it from the API.
  const storeId = useChat((s) => s.conversationId);
  const hasMessages = useChat((s) => s.messages.length > 0);

  useEffect(() => {
    if (storeId !== id || !hasMessages) {
      useChat.getState().clearChat();
    }
  }, [id, storeId, hasMessages]);

  return (
    <div className="-mx-4 -my-6 sm:-mx-6 lg:-mx-8">
      <ChatView conversationId={id} />
    </div>
  );
}