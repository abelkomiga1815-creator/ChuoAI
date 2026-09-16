'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { MessagesSquare, Pencil, Trash2, X, Check } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { api } from '@/lib/api';
import { timeAgo, truncate } from '@/lib/format';
import type { Conversation } from '@/types';

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[] | null>(null);
  const [error, setError] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const load = useCallback(async () => {
    setConversations(null);
    try {
      const data = await api.getConversations({ limit: 100 });
      setConversations(data);
    } catch {
      setError(true);
      setConversations([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDelete(id: string) {
    if (!window.confirm('Delete this conversation?')) return;
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev?.filter((c) => c.id !== id) || []);
    } catch {
      window.alert('Failed to delete conversation.');
    }
  }

  async function handleRename(id: string) {
    const title = editingTitle.trim();
    if (!title) {
      setEditingId(null);
      return;
    }
    try {
      const updated = await api.updateConversation(id, title);
      setConversations((prev) => prev?.map((c) => (c.id === id ? { ...c, title: updated.title } : c)) || []);
    } catch {
      window.alert('Failed to rename conversation.');
    }
    setEditingId(null);
  }

  if (conversations === null) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-16 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold sm:text-2xl">Conversations</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Your conversation history with ChuoAI.
          </p>
        </div>
        <Button onClick={() => (window.location.href = '/chat')}>New chat</Button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Could not load conversations. Please try again.
        </div>
      )}

      {conversations.length === 0 && !error ? (
        <EmptyState
          title="No conversations yet"
          description="When you chat with ChuoAI, your conversations will be saved here for easy access."
          action={<Button onClick={() => (window.location.href = '/chat')}>Start a new chat</Button>}
        />
      ) : (
        <ul className="divide-y overflow-hidden rounded-xl border bg-card shadow-sm">
          {conversations.map((conversation) => (
            <li key={conversation.id} className="group flex items-center gap-3 px-4 py-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                <MessagesSquare className="h-4 w-4 text-primary" />
              </div>

              <div className="min-w-0 flex-1">
                {editingId === conversation.id ? (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleRename(conversation.id);
                    }}
                    className="flex items-center gap-2"
                  >
                    <Input
                      autoFocus
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      className="h-8"
                    />
                    <button type="submit" aria-label="Save" className="rounded-md p-1.5 text-emerald-600 hover:bg-muted">
                      <Check className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      aria-label="Cancel"
                      onClick={() => setEditingId(null)}
                      className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </form>
                ) : (
                  <Link href={`/chat/${conversation.id}`} className="block">
                    <p className="truncate text-sm font-medium group-hover:text-primary">
                      {truncate(conversation.title || 'Untitled chat', 80)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {timeAgo(conversation.updated_at || conversation.created_at)}
                    </p>
                  </Link>
                )}
              </div>

              {editingId !== conversation.id && (
                <div className="flex shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    type="button"
                    aria-label="Rename"
                    onClick={() => {
                      setEditingId(conversation.id);
                      setEditingTitle(conversation.title || '');
                    }}
                    className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    aria-label="Delete"
                    onClick={() => handleDelete(conversation.id)}
                    className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}