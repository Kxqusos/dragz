"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./app-header.module.css";

const NAV_ITEMS = [
  { href: "/search", label: "Поиск аптек" },
  { href: "/ai-consult", label: "ИИ-консультант" }
];

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className={styles.header}>
      <div className={styles.shell}>
        <Link href="/" className={styles.brand}>
          Драгз.рф
        </Link>

        <nav className={styles.nav} aria-label="Навигация по страницам">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={isActive ? styles.linkActive : styles.link}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
