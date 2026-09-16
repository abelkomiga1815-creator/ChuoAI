'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Building2 } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { api } from '@/lib/api';
import type { University } from '@/types';

export default function UniversitiesPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get('search') || '';

  const [search, setSearch] = useState(initialSearch);
  const [universities, setUniversities] = useState<University[] | null>(null);
  const [hasNext, setHasNext] = useState(false);

  const load = async (query: string) => {
    setUniversities(null);
    try {
      const data = await api.getUniversities({ search: query || undefined, limit: 20 });
      setUniversities(data);
      setHasNext(data.length === 20);
    } catch {
      setUniversities([]);
    }
  };

  useEffect(() => {
    load(initialSearch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSearch]);

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams(searchParams.toString());
    if (search.trim()) params.set('search', search.trim());
    else params.delete('search');
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold sm:text-2xl">Find Universities</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Browse public and private universities operating in Tanzania.
        </p>
      </div>

      <form onSubmit={submitSearch} className="flex max-w-lg gap-2">
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name…"
          aria-label="Search universities"
        />
        <Button type="submit">Search</Button>
      </form>

      {universities === null ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : universities.length === 0 ? (
        <EmptyState
          title="No universities found"
          description={
            search
              ? `No universities match “${search}”. The university catalogue is still being loaded — check the up-to-date list at TCU.`
              : 'The university catalogue is still being prepared. Check back soon.'
          }
          action={
            <Button variant="outline" onClick={() => router.push('/chat?q=Universities in Tanzania')}>
              Ask ChuoAI about universities
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {universities.map((university) => (
            <Link
              key={university.id}
              href={`/universities/${university.id}`}
              className="group rounded-xl border bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <Building2 className="h-5 w-5 text-primary" />
                </div>
                <Badge variant={university.type === 'PUBLIC' ? 'default' : 'secondary'}>
                  {university.type === 'PUBLIC' ? 'Public' : 'Private'}
                </Badge>
              </div>
              <h3 className="mt-3 text-sm font-semibold group-hover:text-primary">
                {university.abbreviation ? (
                  <>
                    {university.name} <span className="text-muted-foreground">({university.abbreviation})</span>
                  </>
                ) : (
                  university.name
                )}
              </h3>
              {(university.region || university.city) && (
                <p className="mt-1 text-xs text-muted-foreground">
                  {[university.city, university.region].filter(Boolean).join(', ')}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}

      {hasNext && (
        <p className="text-center text-xs text-muted-foreground">
          Showing the first 20 results. Refine your search for more specific results.
        </p>
      )}
    </div>
  );
}