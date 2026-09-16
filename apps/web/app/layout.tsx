import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "文档问答助手",
  description: "Vertical document question answering workspace"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

