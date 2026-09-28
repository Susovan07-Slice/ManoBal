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
      <body className="bg-sky-100 text-ink min-h-screen">
        {/* Fixed gradient background */}
        <div className="app-gradient-bg" aria-hidden="true" />
        
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
