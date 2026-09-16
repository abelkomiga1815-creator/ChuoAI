'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Building2, Globe, Mail, MapPin, Phone } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/format';
import type { UniversityDetail } from '@/types';

export default function UniversityDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const router = useRouter();
  const [university, setUniversity] = useState<UniversityDetail | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .getUniversity(id)
      .then((data) => {
        if (!cancelled) setUniversity(data);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <EmptyState
        title="University not found"
        description="This university could not be found."
        action={
          <Button variant="outline" onClick={() => router.push('/universities')}>
            Back to universities
          </Button>
        }
      />
    );
  }

  if (!university) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-44 rounded-xl" />
      </div>
    );
  }

  const linkItems = [
    { icon: MapPin, label: 'Location', value: [university.city, university.region].filter(Boolean).join(', ') || '—' },
    { icon: Building2, label: 'Type', value: university.type === 'PUBLIC' ? 'Public university' : 'Private university' },
    { icon: Phone, label: 'Phone', value: university.contact_phone || '—' },
    { icon: Mail, label: 'Email', value: university.contact_email || '—' },
    { icon: Globe, label: 'Website', value: university.website || '—' },
  ];

  return (
    <div className="space-y-6">
      <Link
        href="/universities"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Universities
      </Link>

      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
              <Building2 className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">{university.name}</h1>
              <p className="text-sm text-muted-foreground">
                {[university.abbreviation, formatDate(university.established_year || university.created_at) && `Est. ${formatDate(university.established_year || university.created_at)}`]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Badge>{university.type === 'PUBLIC' ? 'Public' : 'Private'}</Badge>
            {university.programme_count !== undefined && (
              <Badge variant="secondary">{university.programme_count} programmes</Badge>
            )}
          </div>
        </div>

        {university.description && (
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted-foreground">
            {university.description}
          </p>
        )}

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {linkItems.map((item) => (
            <div key={item.label} className="flex items-center gap-3 rounded-lg border bg-muted/40 px-3 py-2.5">
              <item.icon className="h-4 w-4 shrink-0 text-primary" />
              <div className="min-w-0">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{item.label}</p>
                <p className="truncate text-sm font-medium">{item.value}</p>
              </div>
            </div>
          ))}
        </div>

        {university.website && (
          <a
            href={university.website}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
          >
            <Globe className="h-4 w-4" /> Visit official website
          </a>
        )}
      </div>

      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Ask ChuoAI about this university
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Get admission details, fee estimates or programme information.
        </p>
        <Button
          className="mt-4"
          onClick={() =>
            router.push(`/chat?q=${encodeURIComponent(`Tell me about ${university.abbreviation || university.name}`)}`)
          }
        >
          Ask about {university.abbreviation || university.name}
        </Button>
      </div>
    </div>
  );
}