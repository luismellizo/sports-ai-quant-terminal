import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
}); export const metadata: Metadata = {
  title: "SPORTS AI TERMINAL",
  description: "Multi-agent predictive analysis for sports betting — Quantitative terminal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`scanline-overlay noise-bg ${jetbrainsMono.className}`}>
        {children}
      </body>
    </html>
  );
}
