'use client';

import { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Skeleton';
import { api } from '@/lib/api';
import type { EligibilityResponse } from '@/types';

const EMPTY_FORM = {
  programme: '',
  university: '',
  qualification_type: '',
  subjects: '',
  points: '',
  division: '',
};

export default function EligibilityPage() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [result, setResult] = useState<EligibilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof typeof EMPTY_FORM>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.programme.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.checkEligibility({
        programme: form.programme.trim(),
        university: form.university.trim() || undefined,
        qualifications: {
          qualification_type: form.qualification_type.trim() || undefined,
          subjects: form.subjects
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
          points: form.points ? Number(form.points) : undefined,
          division: form.division.trim() || undefined,
        },
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check eligibility');
    } finally {
      setLoading(false);
    }
  }

  const statusStyles: Record<string, { label: string; icon: React.ReactNode; className: string }> = {
    ELIGIBLE: {
      label: 'Eligible',
      icon: <CheckCircle2 className="h-5 w-5" />,
      className: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    },
    NOT_ELIGIBLE: {
      label: 'Not eligible',
      icon: <XCircle className="h-5 w-5" />,
      className: 'bg-destructive/10 text-destructive',
    },
    POTENTIALLY_ELIGIBLE: {
      label: 'Potentially eligible',
      icon: <AlertCircle className="h-5 w-5" />,
      className: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
    },
    MORE_INFO_REQUIRED: {
      label: 'More information needed',
      icon: <HelpCircle className="h-5 w-5" />,
      className: 'bg-primary/10 text-primary',
    },
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">Eligibility Checker</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter your programme of interest and your qualifications to get a quick eligibility assessment.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="space-y-1.5 sm:col-span-2">
                <span className="text-sm font-medium">Programme *</span>
                <Input
                  value={form.programme}
                  onChange={(e) => set('programme', e.target.value)}
                  placeholder="e.g. Bachelor of Computer Science"
                  required
                />
              </label>
              <label className="space-y-1.5 sm:col-span-2">
                <span className="text-sm font-medium">University (optional)</span>
                <Input
                  value={form.university}
                  onChange={(e) => set('university', e.target.value)}
                  placeholder="e.g. University of Dar es Salaam"
                />
              </label>
              <label className="space-y-1.5">
                <span className="text-sm font-medium">Qualification</span>
                <Input
                  value={form.qualification_type}
                  onChange={(e) => set('qualification_type', e.target.value)}
                  placeholder="e.g. ACSEE / Diploma"
                />
              </label>
              <label className="space-y-1.5">
                <span className="text-sm font-medium">Subjects (comma separated)</span>
                <Input
                  value={form.subjects}
                  onChange={(e) => set('subjects', e.target.value)}
                  placeholder="e.g. PCM"
                />
              </label>
              <label className="space-y-1.5">
                <span className="text-sm font-medium">Points</span>
                <Input
                  type="number"
                  value={form.points}
                  onChange={(e) => set('points', e.target.value)}
                  placeholder="e.g. 10"
                />
              </label>
              <label className="space-y-1.5">
                <span className="text-sm font-medium">Division</span>
                <Input
                  value={form.division}
                  onChange={(e) => set('division', e.target.value)}
                  placeholder="e.g. II"
                />
              </label>
            </div>

            <Button type="submit" disabled={loading}>
              {loading && <Spinner className="h-4 w-4" />}
              {loading ? 'Checking…' : 'Check eligibility'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {result && (
        <Card className="animate-fade-in">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-base">
                {result.programme}
                {result.university ? ` · ${result.university}` : ''}
              </CardTitle>
              {statusStyles[result.status] && (
                <span
                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${statusStyles[result.status].className}`}
                >
                  {statusStyles[result.status].icon}
                  {statusStyles[result.status].label}
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
              {result.reasoning}
            </p>

            {result.requirements && result.requirements.length > 0 && (
              <div>
                <p className="mb-1.5 text-sm font-semibold">Requirements</p>
                <ul className="space-y-1 text-sm">
                  {result.requirements.map((req, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-primary">•</span>
                      <span className="text-muted-foreground">
                        {typeof req === 'string' ? req : JSON.stringify(req)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.student_qualifications && (
              <div>
                <p className="mb-1.5 text-sm font-semibold">Your qualifications</p>
                <pre className="rounded-lg bg-muted p-3 text-xs text-muted-foreground whitespace-pre-wrap">
                  {JSON.stringify(result.student_qualifications, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <Badge>{result.programme}</Badge>
              {result.university && <Badge variant="secondary">{result.university}</Badge>}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}