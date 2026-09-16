// frontend/components/chat/ChatWelcome.tsx
'use client';

import {
  GraduationCap,
  BookOpen,
  ClipboardCheck,
  Landmark,
  Wallet,
  UserCheck,
  Scale,
  Building2,
} from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';

interface SuggestionCard {
  icon: React.ReactNode;
  title: string;
  description: string;
  prompt: string;
  color: string;
}

const suggestions: SuggestionCard[] = [
  {
    icon: <Building2 className="h-5 w-5" />,
    title: 'Find a University',
    description: 'Search Tanzanian universities',
    prompt: 'Nipe orodha ya vyuo vikuu Tanzania',
    color: 'bg-blue-500/10 text-blue-600',
  },
  {
    icon: <BookOpen className="h-5 w-5" />,
    title: 'Explore Programmes',
    description: 'Discover available programmes',
    prompt: 'Ni programmes gani zinapatikana kwa Computer Science?',
    color: 'bg-purple-500/10 text-purple-600',
  },
  {
    icon: <ClipboardCheck className="h-5 w-5" />,
    title: 'Admission Requirements',
    description: 'Check entry requirements',
    prompt: 'What are the admission requirements for Bachelor of Computer Science?',
    color: 'bg-green-500/10 text-green-600',
  },
  {
    icon: <Landmark className="h-5 w-5" />,
    title: 'TCU Information',
    description: 'TCU regulations and guidance',
    prompt: 'TCU ni nini na inafanya kazi gani?',
    color: 'bg-amber-500/10 text-amber-600',
  },
  {
    icon: <Wallet className="h-5 w-5" />,
    title: 'Fees & Scholarships',
    description: 'Find funding options',
    prompt: 'What scholarships are available for Tanzanian students?',
    color: 'bg-rose-500/10 text-rose-600',
  },
  {
    icon: <UserCheck className="h-5 w-5" />,
    title: 'Check My Eligibility',
    description: 'See if you qualify',
    prompt: 'Nina Division II PCM, naweza kusoma Computer Science?',
    color: 'bg-cyan-500/10 text-cyan-600',
  },
  {
    icon: <Scale className="h-5 w-5" />,
    title: 'Compare Universities',
    description: 'Compare universities side by side',
    prompt: 'Compare UDSM, UDOM and MUST for Computer Science',
    color: 'bg-indigo-500/10 text-indigo-600',
  },
  {
    icon: <GraduationCap className="h-5 w-5" />,
    title: 'Transfers',
    description: 'Learn about university transfers',
    prompt: 'How do I transfer from one university to another in Tanzania?',
    color: 'bg-teal-500/10 text-teal-600',
  },
];

interface ChatWelcomeProps {
  onSuggestionClick: (prompt: string) => void;
}

export function ChatWelcome({ onSuggestionClick }: ChatWelcomeProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-10">
      <div className="mx-auto max-w-5xl text-center">
        {/* Logo / Brand */}
        <div className="mb-5 flex justify-center">
          <BrandLogo tileClassName="h-14 w-14 rounded-2xl shadow-lg" />
        </div>

        <h1 className="mb-2 text-3xl font-bold tracking-tight sm:text-4xl">
          ChuoAI
        </h1>
        <p className="mb-8 text-base text-muted-foreground">
          Your AI guide to universities, programmes, admissions and TCU in Tanzania.
          <br className="hidden sm:block" />
          <span className="text-sm text-muted-foreground/80">
            Mwongozo wako wa vyuo vikuu, kozi, uandikishaji na TCU Tanzania.
          </span>
        </p>

        {/* Suggestion cards */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => onSuggestionClick(suggestion.prompt)}
              className="group flex flex-col gap-3 rounded-xl border bg-card p-4 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-md"
            >
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-lg ${suggestion.color}`}
              >
                {suggestion.icon}
              </div>
              <div>
                <h3 className="text-sm font-medium group-hover:text-primary">
                  {suggestion.title}
                </h3>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {suggestion.description}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}