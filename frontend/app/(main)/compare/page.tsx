'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton, Spinner } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { api } from '@/lib/api';
import type { CompareResponse, University } from '@/types';

const FIELDS: { key: keyof CompareResponse['universities'][number]; label: string }[] = [
  { key: 'location', label: 'Location' },
  { key: 'type', label: 'Type' },
  { key: 'ownership', label: 'Ownership' },
  { key: 'programme', label: 'Programme' },
  { key: 'duration', label: 'Duration' },
  { key: 'entry_requirements', label: 'Entry requirements' },
  { key: 'fees', label: 'Fees' },
  { key: 'accommodation', label: 'Accommodation' },
  { key: 'application_info', label: 'Application info' },
];

export default function ComparePage() {
  const router = useRouter();
  const [universities, setUniversities] = useState<University[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [programme, setProgramme] = useState('');
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getUniversities({ limit: 100 })
      .then((data) => {
        if (!cancelled) setUniversities(data);
      })
      .catch(() => {
        if (!cancelled) setUniversities([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleUniversity(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((u) => u !== id) : prev.length < 3 ? [...prev, id] : prev
    );
  }

  async function submit() {
    if (selected.length < 2) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.compareUniversities({
        university_ids: selected,
        programme: programme.trim() || undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare universities');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">University Comparison</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Select up to 3 universities to compare them side by side.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select universities</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {universities === null ? (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 rounded-lg" />
              ))}
            </div>
          ) : universities.length === 0 ? (
            <EmptyState
              title="No universities to compare"
              description="The university catalogue is still being prepared."
            />
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {universities.map((university) => {
                const active = selected.includes(university.id);
                return (
                  <button
                    key={university.id}
                    type="button"
                    onClick={() => toggleUniversity(university.id)}
                    className={`flex items-center justify-between rounded-lg border px-3 py-2.5 text-left transition-colors ${
                      active
                        ? 'border-primary bg-primary/5 text-primary'
                        : 'hover:bg-muted'
                    }`}
                    aria-pressed={active}
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{university.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {[university.abbreviation, university.region].filter(Boolean).join(' · ')}
                      </p>
                    </div>
                    <span
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-bold ${
                        active ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-transparent'
                      }`}
                    >
                      ✓
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          <label className="block space-y-1.5">
            <span className="text-sm font-medium">Programme (optional)</span>
            <Input
              value={programme}
              onChange={(e) => setProgramme(e.target.value)}
              placeholder="e.g. Bachelor of Computer Science"
            />
          </label>

          <Button
            onClick={submit}
            disabled={selected.length < 2 || loading}
          >
            {loading && <Spinner className="h-4 w-4" />}
            {loading ? 'Comparing…' : `Compare ${selected.length} ${selected.length === 1 ? 'university' : 'universities'}`}
          </Button>
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
            <CardTitle className="text-base">
              {programme.trim() ? `Comparison · ${programme.trim()}` : 'Comparison'}
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Criterion
                  </th>
                  {result.universities.map((u) => (
                    <th key={u.university_id} className="px-3 py-2 text-left text-xs font-semibold">
                      {u.university_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FIELDS.map((field) => (
                  <tr key={field.key} className="border-b last:border-0">
                    <td className="py-2.5 pr-4 align-top text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      {field.label}
                    </td>
                    {result.universities.map((u) => (
                      <td key={u.university_id} className="px-3 py-2.5 align-top text-muted-foreground">
                        {u[field.key] ? String(u[field.key]) : '—'}
                      </td>
                    ))}
                  </tr>
                ))}
                <tr>
                  <td className="py-2.5 pr-4 align-top text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Sources
                  </td>
                  {result.universities.map((u) => (
                    <td key={u.university_id} className="px-3 py-2.5 align-top text-xs text-muted-foreground">
                      {u.sources && u.sources.length > 0
                        ? u.sources.map((s: any) => s.title).filter(Boolean).join(', ')
                        : '—'}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>

            {result.notes && (
              <p className="mt-4 text-sm text-muted-foreground">{result.notes}</p>
            )}

            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => router.push(`/chat?q=${encodeURIComponent(`Compare ${result.universities.map((u) => u.university_name).join(', ')}`)}`)}
            >
              Ask ChuoAI to explain further
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}