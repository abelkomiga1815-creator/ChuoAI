'use client';

import { useEffect, useState, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/useTheme';
import { usePreferences } from '@/hooks/usePreferences';
import { cn } from '@/lib/utils';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/chat': 'Chat',
  '/conversations': 'Conversations',
  '/universities': 'Find Universities',
  '/programmes': 'Explore Programmes',
  '/admissions': 'Admission Requirements',
  '/eligibility': 'Eligibility Checker',
  '/compare': 'University Comparison',
  '/tcu': 'TCU Information',
  '/scholarships': 'Scholarships',
  '/search': 'Knowledge Base',
  '/settings': 'Settings',
  '/help': 'Help & Support',
};

function usePageTitle(pathname: string) {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  if (pathname.startsWith('/chat/')) return 'Conversation';
  if (pathname.startsWith('/universities/')) return 'University Details';
  return 'ChuoAI';
}

export function Header({
  onToggleSidebar,
  sidebarOpen,
}: {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, cycleLanguage } = usePreferences();

  const [search, setSearch] = useState('');
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const title = usePageTitle(pathname);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!search.trim()) return;
    router.push(`/search?q=${encodeURIComponent(search.trim())}`);
  }

  async function handleLogout() {
    setUserMenuOpen(false);
    await logout();
    router.push('/login');
  }

  const langLabel = language === 'auto' ? 'Auto' : language === 'en' ? 'EN' : 'SW';

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b bg-background/80 px-3 backdrop-blur-md sm:px-4">
      <button
        type="button"
        onClick={onToggleSidebar}
        aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          {sidebarOpen ? (
            <path
              d="M3 4.5h12M3 9h12M3 13.5h12M7 4.5v9"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          ) : (
            <path
              d="M3 4.5h12M3 9h12M3 13.5h12"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          )}
        </svg>
      </button>

      <div className="min-w-0">
        <h1 className="truncate text-sm font-semibold sm:text-base">{title}</h1>
        <p className="hidden text-xs text-muted-foreground lg:block">
          Tanzania University &amp; TCU AI Assistant
        </p>
      </div>

      <form
        onSubmit={onSearch}
        className="mx-2 hidden max-w-xl flex-1 md:block"
        role="search"
      >
        <div className="relative">
          <svg
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
          >
            <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5" />
            <path d="M10.5 10.5 14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search universities, programmes, TCU..."
            className="h-9 w-full rounded-lg border bg-card pl-9 pr-3 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </form>

      <div className="ml-auto flex items-center gap-1 sm:gap-1.5">
        {/* Language */}
        <button
          type="button"
          onClick={cycleLanguage}
          aria-label={`Language: ${langLabel}`}
          title="Language"
          className={cn(
            'inline-flex h-9 min-w-[42px] items-center justify-center rounded-lg px-2 text-xs font-semibold transition-colors hover:bg-muted',
            language !== 'auto' && 'bg-primary/10 text-primary'
          )}
        >
          {langLabel}
        </button>

        {/* Theme */}
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          {theme === 'dark' ? (
            <svg width="17" height="17" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle cx="10" cy="10" r="4" fill="currentColor" />
              <path
                d="M10 1.5v2M10 16.5v2M1.5 10h2M16.5 10h2M3.9 3.9l1.4 1.4M14.7 14.7l1.4 1.4M16.1 3.9l-1.4 1.4M5.3 14.7l-1.4 1.4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg width="17" height="17" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path
                d="M17.2 12.3A7 7 0 0 1 7.7 2.8a7 7 0 1 0 9.5 9.5Z"
                fill="currentColor"
              />
            </svg>
          )}
        </button>

        {/* User menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            type="button"
            onClick={() => setUserMenuOpen((o) => !o)}
            aria-haspopup="menu"
            aria-expanded={userMenuOpen}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground transition-transform hover:scale-105"
          >
            {(user?.username || 'U').charAt(0).toUpperCase()}
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-11 z-40 w-64 overflow-hidden rounded-xl border bg-popover shadow-lg animate-fade-in">
              <div className="border-b px-4 py-3">
                <p className="text-sm font-semibold">{user?.full_name || user?.username || 'User'}</p>
                <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-destructive transition-colors hover:bg-muted"
              >
                <svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M12.5 3.5h-7a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h7M14.5 7l3 3-3 3M8.5 10h9"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}