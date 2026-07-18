import type { Metadata } from "next";
import { Fraunces, DM_Sans } from "next/font/google";
import { Sidebar } from "@/components/layout/sidebar";
import { TopHeader } from "@/components/layout/top-header";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
});

const sans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Blinkit Feedback Intelligence",
  description:
    "AI-powered Play Store review insights for Blinkit Product Managers",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${sans.variable} font-sans antialiased bg-blinkit-light text-blinkit-ink`}>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex flex-1 flex-col overflow-hidden">
            <TopHeader />
            <main className="flex-1 overflow-y-auto">
              <div className="mx-auto max-w-[1600px] p-6">{children}</div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
