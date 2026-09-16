// frontend/app/layout.tsx
import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { ThemeScript } from '@/components/theme-script';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: {
    default: 'ChuoAI - Tanzania University & TCU AI Assistant',
    template: '%s | ChuoAI',
  },
  description:
    'Your AI Guide to Universities in Tanzania. Get information about universities, programmes, admission, TCU, fees, scholarships, and more.',
  keywords: [
    'ChuoAI',
    'Tanzania universities',
    'TCU',
    'university admission',
    'scholarships',
    'AI assistant',
  ],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f8fafc' },
    { media: '(prefers-color-scheme: dark)', color: '#0b1220' },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  );
}