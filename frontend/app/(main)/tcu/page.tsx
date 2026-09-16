'use client';

import { useRouter } from 'next/navigation';
import { Landmark, Quote } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function TcuPage() {
  const router = useRouter();

  const ask = (q: string) => router.push(`/chat?q=${encodeURIComponent(q)}`);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">TCU Information</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Everything you need to know about the Tanzania Commission for Universities.
        </p>
      </div>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Landmark className="h-4 w-4 text-primary" /> About the Commission
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
            <p>
              The <strong className="text-foreground">Tanzania Commission for Universities (TCU)</strong> is the
              statutory body responsible for regulating higher education in Tanzania. It was established in
              2005 under the Universities Act, Repealing the earlier 1985 University Act.
            </p>
            <p>TCU’s main responsibilities include:</p>
            <ul className="space-y-1.5">
              <li className="flex gap-2"><span className="text-primary">•</span> Registering and accrediting public and private universities</li>
              <li className="flex gap-2"><span className="text-primary">•</span> Approving quality-assured academic programmes before they are offered</li>
              <li className="flex gap-2"><span className="text-primary">•</span> Coordinating the central admission of students into universities</li>
              <li className="flex gap-2"><span className="text-primary">•</span> Recognising qualifications earned from accredited institutions</li>
              <li className="flex gap-2"><span className="text-primary">•</span> Advising the government on higher education policy and funding</li>
            </ul>
            <p>
              TCU publishes an official annual list of accredited universities as well as the list of approved
              programmes for each academic year.
            </p>
            <div className="flex gap-2">
              <Badge>Regulation</Badge>
              <Badge variant="secondary">Quality Assurance</Badge>
              <Badge variant="secondary">Admissions Coordination</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ask ChuoAI</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" size="sm" className="w-full justify-start" onClick={() => ask('What does TCU do?')}>
              What does TCU do?
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start" onClick={() => ask('How do I verify if a university is accredited by TCU?')}>
              How to verify accreditation?
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start" onClick={() => ask('How does TCU select students for admission?')}>
              How does student selection work?
            </Button>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardContent className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-3">
            <Quote className="h-6 w-6 shrink-0 text-primary" />
            <div>
              <p className="text-sm font-medium">Official information</p>
              <p className="text-sm text-muted-foreground">
                For authoritative details, always refer to the TCU website and official announcements for your
                application year.
              </p>
            </div>
          </div>
          <Button onClick={() => ask('Current TCU admission requirements')}>Ask about admission requirements</Button>
        </CardContent>
      </Card>
    </div>
  );
}