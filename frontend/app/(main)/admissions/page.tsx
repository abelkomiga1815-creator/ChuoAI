'use client';

import { useRouter } from 'next/navigation';
import { ClipboardCheck, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function AdmissionsPage() {
  const router = useRouter();

  const ask = (q: string) => router.push(`/chat?q=${encodeURIComponent(q)}`);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">Admission Requirements</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Understand what Tanzanian universities require before you apply.
        </p>
      </div>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ClipboardCheck className="h-4 w-4 text-primary" /> Basic entry qualifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
            <p><strong className="text-foreground">Bachelor’s degrees</strong> — you typically need two principal
              passes in relevant subjects at ACSE (A-Level), or the equivalent of a Diploma with a good credit
              for direct entry.</p>
            <p><strong className="text-foreground">Diploma programmes</strong> — usually require four passes at
              CSE (O-Level) with passes in relevant subjects.</p>
            <p><strong className="text-foreground">Certificates</strong> — typically require passes in core
              subjects at CSE (O-Level).</p>
            <p><strong className="text-foreground">Masters</strong> — a bachelor’s degree with a specific
              minimum GPA from an accredited university.</p>
            <p className="text-xs">
              Exact subjects, grades and points depend on the specific university and programme.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Info className="h-4 w-4 text-primary" /> How admission works
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
            <p>
              For government-sponsored and other centrally coordinated places, students are selected through the
              central admission system coordinated by TCU. Universities set their own entry requirements for
              privately sponsored students.
            </p>
            <p>The typical steps are:</p>
            <ol className="space-y-1.5">
              <li className="flex gap-2"><span className="font-semibold text-foreground">1.</span> Check that your qualifications meet the entry requirements.</li>
              <li className="flex gap-2"><span className="font-semibold text-foreground">2.</span> Apply through the official application window (usually including TCU’s central system).</li>
              <li className="flex gap-2"><span className="font-semibold text-foreground">3.</span> Be shortlisted based on your results and available places.</li>
              <li className="flex gap-2"><span className="font-semibold text-foreground">4.</span> Accept your place and complete registration at the university.</li>
            </ol>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Check programme requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <Button onClick={() => ask('What are the admission requirements for Bachelor of Computer Science at UDSM?')}>
              Ask ChuoAI
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Test your eligibility</CardTitle>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => router.push('/eligibility')}>
              Open Eligibility Checker
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Which Form Six subjects?</CardTitle>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => ask('Which Form Six subjects do I need for an engineering degree?')}>
              Ask ChuoAI
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}