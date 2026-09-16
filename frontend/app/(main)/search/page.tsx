'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Search as SearchIcon, Building2, BookOpen } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { api } from '@/lib/api';
import { truncate } from '@/lib/format';
import type { SearchResults } from '@/types';

function SearchContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get('q') || '';
  const [query, setQuery] = useState(q);
  const [results, setResults] = useState<SearchResults | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setQuery(q);
    if (!q.trim()) {
      setResults(null);
      return;
    }
    let cancelled = false;
    setResults(null);
    setError(false);
    api
      .search(q.trim())
      .then((data) => {
        if (!cancelled) setResults(data);
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setResults({ universities: [], programmes: [] });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [q]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    window.location.href = `/search?q=${encodeURIComponent(query.trim())}`;
  }

  const total =
    results && !error ? (results.universities?.length || 0) + (results.programmes?.length || 0) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">Knowledge Base</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Search the knowledge base for universities and programmes.
        </p>
      </div>

      <form onSubmit={submit} className="flex max-w-lg gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search…"
          aria-label="Search knowledge base"
        />
        <Button type="submit">
          <SearchIcon className="h-4 w-4" />
          Search
        </Button>
      </form>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Search is temporarily unavailable. Try again in a moment.
        </div>
      )}

      {results === null ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      ) : results.universities?.length === 0 && results.programmes?.length === 0 ? (
        <EmptyState
          title={q ? `No results for “${q}”` : 'Search the knowledge base'}
          description={
            q
              ? 'No universities or programmes matched your search. Try different keywords or ask ChuoAI directly.'
              : 'Type a query above to search universities and programmes.'
          }
          action={
            q ? (
              <Button
                variant="outline"
                onClick={() => (window.location.href = `/chat?q=${encodeURIComponent(q)}`)}
              >
                Ask ChuoAI “{truncate(q, 30)}”
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="space-y-6">
          {total > 0 && (
            <p className="text-sm text-muted-foreground">{total} result{total === 1 ? '' : 's'} for “{q}”</p>
          )}

          {results.universities && results.universities.length > 0 && (
            <section className="space-y-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                <Building2 className="h-4 w-4" /> Universities ({results.universities.length})
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {results.universities.map((u) => (
                  <Link
                    key={u.id}
                    href={`/universities/${u.id}`}
                    className="rounded-xl border bg-card p-4 shadow-sm transition-colors hover:border-primary/40"
                  >
                    <p className="text-sm font-semibold">
                      {u.name} {u.abbreviation && <span className="text-muted-foreground">({u.abbreviation})</span>}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {[u.city, u.region].filter(Boolean).join(', ') || u.type}
                    </p>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {results.programmes && results.programmes.length > 0 && (
            <section className="space-y-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                <BookOpen className="h-4 w-4" /> Programmes ({results.programmes.length})
              </h2>
              <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
                <ul className="divide-y">
                  {results.programmes.map((p) => (
                    <li key={p.id} className="px-4 py-3">
                      <p className="text-sm font-medium">{p.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {[p.code, p.level, p.faculty].filter(Boolean).join(' · ') || 'Programme'}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 rounded-xl" />}>
      <SearchContent />
    </Suspense>
  );
}