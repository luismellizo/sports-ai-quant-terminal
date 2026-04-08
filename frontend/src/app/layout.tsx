import type { Metadata } from "next";
import { JetBrains_Mono, Space_Grotesk, Space_Mono, Doto } from "next/font/google";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});
const spaceMono = Space_Mono({
  weight: ['400', '700'],
  subsets: ["latin"],
  variable: "--font-space-mono",
});
const doto = Doto({
  subsets: ["latin"],
  variable: "--font-doto",
});

export const metadata: Metadata = {
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
      <body className={`scanline-overlay noise-bg ${jetbrainsMono.className} ${spaceGrotesk.variable} ${spaceMono.variable} ${doto.variable}`}>
        {children}
      </body>
    </html>
  );
}
