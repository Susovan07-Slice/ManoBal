import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { RoleProvider } from '@/lib/RoleContext';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetBrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains-mono' });

export const metadata: Metadata = {
  title: 'Commander & Welfare Officer Dashboard',
  description: 'AI-Based Personnel Stress Monitoring System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${jetBrainsMono.variable} bg-background text-textPrimary h-screen flex flex-col`}>
        <RoleProvider>
          {children}
        </RoleProvider>
      </body>
    </html>
  );
}
