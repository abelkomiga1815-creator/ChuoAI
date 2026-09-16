import { cn } from '@/lib/utils';

interface BrandLogoProps {
  className?: string;
  tileClassName?: string;
  showWordmark?: boolean;
  wordmarkClassName?: string;
}

export function BrandLogo({
  className,
  tileClassName,
  showWordmark = false,
  wordmarkClassName,
}: BrandLogoProps) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div
        className={cn(
          'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl',
          'bg-gradient-to-br from-chuoai-royal to-chuoai-accent shadow-sm',
          tileClassName
        )}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 text-white"
          aria-hidden="true"
        >
          <path
            d="M22 9.5 12 4 2 9.5l10 5.5 6-3.3v5.3l1.5.8V11l2.5-1.5Z"
            fill="currentColor"
          />
          <path
            d="M6.5 12.2v3.6c0 1 2.5 2.4 5.5 2.4s5.5-1.4 5.5-2.4v-3.6l-5.5 3-5.5-3Z"
            fill="currentColor"
            opacity="0.85"
          />
        </svg>
      </div>
      {showWordmark && (
        <div className="leading-none">
          <p className={cn('text-lg font-semibold tracking-tight', wordmarkClassName)}>
            ChuoAI
          </p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Tanzania University Assistant
          </p>
        </div>
      )}
    </div>
  );
}