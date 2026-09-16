'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChatView } from '@/components/chat/ChatView';

export default function ChatPage() {
  const router = useRouter();
  const [pending, setPending] = useState<string | undefined>(undefined);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('q');
    if (q && q.trim()) setPending(q.trim());
  }, []);

  return (
    <div className="-mx-4 -my-6 sm:-mx-6 lg:-mx-8">
      <ChatView pendingQuestion={pending} />
    </div>
  );
}