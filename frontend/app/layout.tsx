import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Study Guide Generation",
  description:
    "Teacher-facing workspace for generating curriculum-aligned study guides.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen bg-canvas text-ink antialiased`}
      >
        <div className="relative isolate min-h-screen overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-72 bg-[radial-gradient(circle_at_top,_rgba(14,116,144,0.18),_transparent_58%)]" />
          <div className="absolute inset-x-0 top-24 -z-10 h-80 bg-[radial-gradient(circle_at_top_right,_rgba(251,191,36,0.14),_transparent_48%)]" />
          <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4 sm:px-10 lg:px-16">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-800">
                  Teacher Workspace
                </p>
                <h1 className="mt-1 text-lg font-semibold tracking-tight text-slate-950">
                  Study Guide Generation
                </h1>
              </div>
              <p className="hidden max-w-sm text-sm leading-6 text-slate-600 md:block">
                Plan lessons, generate aligned materials, and review output in
                one focused workflow.
              </p>
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
