'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronDown, HelpCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

const FAQ = [
  {
    question: 'What is ChuoAI?',
    answer:
      'ChuoAI is an AI assistant that helps you find information about Tanzanian universities, programmes, admission requirements, TCU regulations and scholarships. You can ask in English or Kiswahili.',
  },
  {
    question: 'How accurate is the information?',
    answer:
      'ChuoAI will eventually answer from an indexed knowledge base of official sources. Until that content is fully loaded, answers come from general knowledge and may make mistakes — always verify critical information with the official source (the university or TCU).',
  },
  {
    question: 'Can I use ChuoAI without an account?',
    answer: 'No. You need to create a free account so your chat history can be saved across sessions.',
  },
  {
    question: 'What languages are supported?',
    answer: 'English and Kiswahili. You can set a preferred language in Settings, or leave it on Auto to follow your question.',
  },
  {
    question: 'How do I share or report an issue?',
    answer: 'Use the options below — you can ask ChuoAI directly (it can help with most questions) or reach out to our support team by email.',
  },
];

export default function HelpPage() {
  const router = useRouter();
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const ask = (q: string) => router.push(`/chat?q=${encodeURIComponent(q)}`);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">Help &amp; Support</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Frequently asked questions and ways to get in touch.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <HelpCircle className="h-4 w-4 text-primary" /> Frequently asked questions
          </CardTitle>
        </CardHeader>
        <CardContent className="divide-y">
          {FAQ.map((item, index) => (
            <div key={item.question} className="py-1">
              <button
                type="button"
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                aria-expanded={openIndex === index}
                className="flex w-full items-center justify-between gap-3 py-3 text-left"
              >
                <span className="text-sm font-medium">{item.question}</span>
                <ChevronDown
                  className={cn(
                    'h-4 w-4 shrink-0 text-muted-foreground transition-transform',
                    openIndex === index && 'rotate-180'
                  )}
                />
              </button>
              {openIndex === index && (
                <p className="pb-4 pr-6 text-sm leading-relaxed text-muted-foreground animate-fade-in">
                  {item.answer}
                </p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Still stuck?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>Ask ChuoAI directly — it can explain concepts, guide you step by step, and point you to the right tools.</p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => ask('How do I apply to university in Tanzania?')}>Ask about applying</Button>
            <Button variant="outline" onClick={() => ask('How do I use the eligibility checker?')}>
              Using the tools
            </Button>
          </div>
          <p className="pt-2 text-xs">
            Or email our team at <a className="text-primary hover:underline" href="mailto:support@chuoai.tz">support@chuoai.tz</a>.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}