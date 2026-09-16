'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { BookOpen } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { api } from '@/lib/api';
import type { Programme } from '@/types';

export default function ProgrammesPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get('search') || '';

  const [search, setSearch] = useState(initialSearch);
  const [programmes, setProgrammes] = useState<Programme[] | null>(null);
  const [hasNext, setHasNext] = useState(false);

  const load = async (query: string) => {
    setProgrammes(null);
    try {
      const data = await api.getProgrammes({ search: query || undefined, limit: 20 });
      setProgrammes(data);
      setHasNext(data.length === 20);
    } catch {
      setProgrammes([]);
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
        <h1 className="text-xl font-bold sm:text-2xl">Explore Programmes</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Search degree programmes offered by Tanzanian universities.
        </p>
      </div>

      <form onSubmit={submitSearch} className="flex max-w-lg gap-2">
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search programmes, e.g. Medicine…"
          aria-label="Search programmes"
        />
        <Button type="submit">Search</Button>
      </form>

      {programmes === null ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      ) : programmes.length === 0 ? (
        <EmptyState
          title="No programmes found"
          description={
            search
              ? `No programmes match “${search}”. The programme catalogue is still being loaded — check current offerings with TCU.`
              : 'The programme catalogue is still being prepared. Check back soon.'
          }
          action={
            <Button variant="outline" onClick={() => router.push(`/chat?q=${encodeURIComponent('What programmes are available in Tanzania?')}`)}>
              Ask ChuoAI about programmes
            </Button>
          }
        />
      ) : (
        <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
          <ul className="divide-y">
            {programmes.map((programme) => (
              <li
                key={programme.id}
                className="flex items-center gap-4 px-4 py-3.5 transition-colors hover:bg-muted/50"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <BookOpen className="h-4 w-4 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{programme.name}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {[programme.code, programme.level, programme.faculty].filter(Boolean).join(' · ') || 'Programme'}
                  </p>
                </div>
                <div className="hidden shrink-0 gap-2 sm:flex">
                  {programme.duration && <Badge variant="secondary">{programme.duration}</Badge>}
                  {programme.study_mode && <Badge variant="outline">{programme.study_mode}</Badge>}
                </div>
              </li>
            ))}
          </ul>
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