import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  href: string;
}

const NAV: { section: string; items: NavItem[] }[] = [
  {
    section: 'GENERAL',
    items: [
      { label: 'Dashboard', href: '/' },
      { label: 'New Chat', href: '/chat' },
      { label: 'Conversations', href: '/conversations' },
    ],
  },
  {
    section: 'AI TOOLS',
    items: [
      { label: 'Find Universities', href: '/universities' },
      { label: 'Explore Programmes', href: '/programmes' },
      { label: 'Admission Requirements', href: '/admissions' },
      { label: 'Eligibility Checker', href: '/eligibility' },
      { label: 'University Comparison', href: '/compare' },
    ],
  },
  {
    section: 'KNOWLEDGE',
    items: [
      { label: 'TCU Information', href: '/tcu' },
      { label: 'Scholarships', href: '/scholarships' },
      { label: 'Knowledge Base', href: '/search' },
    ],
  },
  {
    section: 'SYSTEM',
    items: [
      { label: 'Settings', href: '/settings' },
      { label: 'Help & Support', href: '/help' },
    ],
  },
];

export function SidebarContent({
  onNavigate,
  activePath,
}: {
  onNavigate?: () => void;
  activePath: string;
}) {
  function isActive(href: string) {
    if (href === '/') return activePath === '/';
    // chat/[id] should highlight "New Chat"? Keep dashboard in GENERAL clean: highlight parent group routes.
    return activePath === href || activePath.startsWith(href + '/');
  }

  return (
    <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4 scrollbar-thin">
      {NAV.map((group) => (
        <div key={group.section} className="space-y-1">
          <p className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-muted-foreground/70">
            {group.section}
          </p>
          {group.items.map((item) => {
            const active = isActive(item.href);
            return (
              <NavLink key={item.href} item={item} active={active} onNavigate={onNavigate} />
            );
          })}
        </div>
      ))}
    </nav>
  );
}

function NavLink({ item, active, onNavigate }: { item: NavItem; active: boolean; onNavigate?: () => void }) {
  return (
    <a
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'group relative flex h-9 items-center rounded-lg px-3 text-sm transition-colors',
        active
          ? 'bg-primary/10 font-medium text-primary'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      )}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-full bg-primary" />
      )}
      {item.label}
    </a>
  );
}

export default NAV;