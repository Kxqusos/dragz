import type { Metadata } from "next";
import { AppHeader } from "@/shared/ui/AppHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "Арагс Prototype",
  description: "Прототип сервиса поиска препаратов по цене и наличию"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>
        <AppHeader />
        {children}
      </body>
    </html>
  );
}
