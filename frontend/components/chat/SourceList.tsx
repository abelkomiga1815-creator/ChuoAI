// frontend/components/chat/SourceList.tsx
'use client';

import { ExternalLink, FileText, Shield, BookOpen } from 'lucide-react';
import type { Source } from '@/types';

interface SourceListProps {
  sources: Source[];
}

export function SourceList({ sources }: SourceListProps) {
  if (!sources || sources.length === 0) return null;

  const getSourceIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'tcu_official':
        return <Shield className="h-3.5 w-3.5 text-blue-600" />;
      case 'university_official':
        return <BookOpen className="h-3.5 w-3.5 text-green-600" />;
      default:
        return <FileText className="h-3.5 w-3.5 text-muted-foreground" />;
    }
  };

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        Sources
      </p>
      <div className="flex flex-wrap gap-2">
        {sources.map((source, index) => (
          <div            key={index}
            className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 text-xs"
          >
            {getSourceIcon(source.source_type || '')}
            <div className="flex flex-col">
              <span className="font-medium">{source.title}</span>
              {source.university && (
                <span className="text-muted-foreground">{source.university}</span>
              )}
              {source.academic_year && (
                <span className="text-muted-foreground">
                  Academic Year: {source.academic_year}
                </span>
              )}
            </div>
            {source.url && (
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-1 text-primary hover:text-primary/80"
              >
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}