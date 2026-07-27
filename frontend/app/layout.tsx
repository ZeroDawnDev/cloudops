import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CloudOps AI — Autonomous Cloud Operations Engineer",
  description:
    "Upload your infrastructure. CloudOps AI analyzes security, networking, cost, and reliability like a senior SRE.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
