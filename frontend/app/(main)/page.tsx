'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Building2, BookOpen, ClipboardCheck, Scale, Landmark, Wallet, MessagesSquare } from 'lucide-react';
import { DashboardComposer, SuggestionChips } from '@/components/dashboard/DashboardComposer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAuth } from '@/hooks/useAuth';
import { useChat } from '@/hooks/useChat';
import { api } from '@/lib/api';
import { timeAgo, truncate } from '@/lib/format';
import type { Conversation } from '@/types';

const TOOLS = [
  {
    title: 'Find Universities',
    description: 'Browse Tanzanian universities by name, region or type.',
    href: '/universities',
    icon: Building2,
  },
  {
    title: 'Explore Programmes',
    description: 'Search degree programmes offered across universities.',
    href: '/programmes',
    icon: BookOpen,
  },
  {
    title: 'Admission Requirements',
    description: 'Understand TCU admission guidelines and requirements.',
    href: '/admissions',
    icon: ClipboardCheck,
  },
  {
    title: 'Eligibility Checker',
    description: 'Check your qualifications against programme requirements.',
    href: '/eligibility',
    icon: CheckCircle2Icon,
  },
  {
    title: 'University Comparison',
    description: 'Compare universities side by side on key criteria.',
    href: '/compare',
    icon: Scale,
  },
  {
    title: 'Scholarships',
    description: 'Discover funding and loan opportunities for students.',
    href: '/scholarships',
    icon: Wallet,
  },
];

function CheckCircle2Icon(props: React.ComponentProps<typeof Building2>) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M9 12l2 2 4-4" />
      <circle cx="12" cy="12" r="9" />
    </svg>
  );
}

function RecentConversations() {
  const [conversations, setConversations] = useState<Conversation[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getConversations({ limit: 5 })
      .then((data) => {
        if (!cancelled) setConversations(data);
      })
      .catch(() => {
        if (!cancelled) setConversations([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (conversations === null) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No conversations yet. Start a new chat and your history will appear here.
      </p>
    );
  }

  return (
    <ul className="divide-y">
      {conversations.map((conversation) => (
        <li key={conversation.id}>
          <Link
            href={`/chat/${conversation.id}`}
            className="flex items-center gap-3 py-3 transition-colors hover:bg-muted/60 -mx-2 px-2 rounded-lg"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <MessagesSquare className="h-4 w-4 text-primary" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{truncate(conversation.title || 'Untitled chat', 50)}</p>
              <p className="text-xs text-muted-foreground">{timeAgo(conversation.updated_at || conversation.created_at)}</p>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const clearChat = useChat((s) => s.clearChat);

  return (
    <div className="space-y-8">
      {/* AI composer hero */}
      <section className="relative overflow-hidden rounded-2xl border bg-gradient-to-b from-primary/[0.06] to-transparent p-6 sm:p-10">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Karibu, {user?.username || 'there'}
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
          ChuoAI is your AI guide to universities, programmes, admissions and TCU in
          Tanzania. Ask anything in English or Kiswahili.
        </p>

        <div className="mt-6">
          <DashboardComposer />
        </div>
        <SuggestionChips />
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Tools */}
        <section className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Tools &amp; Knowledge
            </h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {TOOLS.map((tool) => (
              <Link
                key={tool.href}
                href={tool.href}
                className="group rounded-xl border bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <tool.icon className="h-4 w-4" />
                </div>
                <h3 className="mt-3 text-sm font-semibold group-hover:text-primary">
                  {tool.title}
                </h3>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {tool.description}
                </p>
              </Link>
            ))}
          </div>
        </section>

        {/* Recent + status */}
        <section className="space-y-6">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Recent conversations</CardTitle>
              <Link
                href="/conversations"
                className="text-xs font-medium text-primary hover:underline"
              >
                View all
              </Link>
            </CardHeader>
            <CardContent>
              <RecentConversations />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">AI engine</span>
                <Badge variant="success">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  </span>
                  Online
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Model</span>
                <span className="font-medium">GPT-OSS 120B</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Knowledge base</span>
                <span className="font-medium text-muted-foreground">Preparing content…</span>
              </div>
              <Link
                href="/chat"
                onClick={clearChat}
                className="mt-3 block"
              >
                <Button variant="outline" className="w-full">
                  Start a new chat
                </Button>
              </Link>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}