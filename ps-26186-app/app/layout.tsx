import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";
import MobileWrapper from "@/components/layout/MobileWrapper";
import SosButton from "@/components/layout/SosButton";
import { AuthProvider } from "@/lib/AuthContext";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "ManoBal Jawan Portal",
  description: "AI-Based Personnel Stress & Welfare Monitoring System",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} antialiased`}
    >
      <body className="bg-slate-950 text-ink min-h-screen flex justify-center">
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').then(function(registration) {
                    console.log('ServiceWorker registration successful with scope: ', registration.scope);
                  }, function(err) {
                    console.log('ServiceWorker registration failed: ', err);
                  });
                });
              }
            `,
          }}
        />
        <AuthProvider>
          <MobileWrapper>
            <SosButton />
            {children}
          </MobileWrapper>
        </AuthProvider>
      </body>
    </html>
  );
}
