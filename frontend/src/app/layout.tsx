import type { Metadata } from "next";
import "./public.css";

export const metadata: Metadata = {
  title: "NetSentinel · Make sense of your connection",
  description: "Check your connection, work through simple internet fixes, and save useful results. No account or installation needed.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
