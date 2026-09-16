'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { BrandLogo } from '@/components/BrandLogo';
import { SidebarContent } from '@/components/app/Sidebar';
import { Header } from '@/components/app/Header';
import { Spinner } from '@/components/ui/Skeleton';
import { useAuth } from '@/hooks/useAuth';
import { useChat } from '@/hooks/useChat';
import { cn } from '@/lib/utils';

function Brand() {
  return (
    <a href="/" className="flex items-center gap-2.5 px-5 py-4">
      <BrandLogo />
      <div className="min-w-0 leading-tight">
        <p className="text-[15px] font-bold tracking-tight">ChuoAI</p>
        <p className="truncate text-[10px] uppercase tracking-wider text-muted-foreground">
          University Assistant
        </p>
      </div>
    </a>
  );
}

function SidebarFooter() {
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push('/login');
  }

  return (
    <div className="border-t px-3 py-3">
      <div className="mb-2 flex items-center gap-2 rounded-lg bg-secondary/60 px-3 py-2">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium">GPT-OSS 120B</p>
          <p className="truncate text-[10px] text-muted-foreground">Fast responses · Groq</p>
        </div>
      </div>
      <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">
          {(user?.username || 'U').charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="truncate text-xs font-semibold">{user?.username}</p>
          <p className="truncate text-[11px] text-muted-foreground">{user?.email}</p>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          aria-label="Sign out"
          title="Sign out"
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
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
        </button>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setMobileOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  const toggleSidebar = () => {
    if (window.innerWidth < 1024) setMobileOpen((o) => !o);
    else setCollapsed((c) => !c);
  };

  const navigateNewChat = () => {
    useChat.getState().clearChat();
    setMobileOpen(false);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Desktop sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r bg-card transition-transform duration-300 lg:flex',
          collapsed && '-translate-x-full'
        )}
      >
        <Brand />
        <SidebarContent
          activePath={pathname}
          onNavigate={() => {
            if (pathname !== '/chat') navigateNewChat();
          }}
        />
        <SidebarFooter />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r bg-card animate-slide-in lg:hidden">
            <div className="flex items-center justify-between pr-2">
              <Brand />
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                aria-label="Close menu"
                className="mr-2 inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="m2 2 10 10M12 2 2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <SidebarContent activePath={pathname} onNavigate={() => setMobileOpen(false)} />
            <SidebarFooter />
          </aside>
        </>
      )}

      {/* Main column */}
      <div className={cn('min-h-screen transition-[padding] duration-300 lg:pl-64', collapsed && 'lg:pl-0')}>
        <Header onToggleSidebar={toggleSidebar} sidebarOpen={!collapsed} />
        <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppShell;