'use client';

import { useRouter } from 'next/navigation';
import { Wallet } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function ScholarshipsPage() {
  const router = useRouter();

  const ask = (q: string) => router.push(`/chat?q=${encodeURIComponent(q)}`);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">Scholarships &amp; Funding</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Learn about the main funding options available to Tanzanian students.
        </p>
      </div>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Wallet className="h-4 w-4 text-primary" /> HESLB loans
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
            <p>
              The <strong className="text-foreground">Higher Education Students’ Loans Board (HESLB)</strong>{' '}
              provides government loans for tuition and living costs to needy Tanzanian students admitted to
              accredited institutions.
            </p>
            <p>Loans are applied for online every year through HESLB’s application portal during the official window.</p>
            <p className="text-xs">
              Loan allocation is based on set criteria and is repayable after your studies.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Government scholarships</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
            <p>
              Public universities offer merit-based scholarships and fee waivers for top-performing students,
              and some programmes (like teacher training and medicine fields) receive government funding for
              selected students.
            </p>
            <p className="text-xs">
              Availability changes yearly — confirm with the specific university.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Private scholarships</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
            <p>
              Universities and external organisations offer private scholarships based on academic merit, gender,
              region or field of study. Many are announced on official university websites and TCU communication
              channels.
            </p>
            <p className="text-xs">
              Always verify scholarship announcements from the official source.
            </p>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardContent className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium">Not sure what you qualify for?</p>
            <p className="text-sm text-muted-foreground">Ask ChuoAI about funding options for your situation.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => ask('How do I apply for a HESLB loan?')}>Ask about HESLB</Button>
            <Button variant="outline" onClick={() => ask('What scholarships are available for Tanzanian university students?')}>
              Ask about scholarships
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}