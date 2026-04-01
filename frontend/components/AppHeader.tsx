"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { AuthUser } from "@/lib/auth/types";
import { getCurrentUser, logoutUser } from "@/lib/auth/client";
import styles from "./app-header.module.css";

const NAV_ITEMS = [
  { href: "/search", label: "Поиск аптек" },
  { href: "/ai-consult", label: "ИИ-консультант" }
];

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let isMounted = true;
    void getCurrentUser().then((currentUser) => {
      if (isMounted) {
        setUser(currentUser);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [pathname]);

  return (
    <header className={styles.header}>
      <div className={styles.shell}>
        <Link href="/" className={styles.brand}>
          <span className={styles.brandBadge}>Др</span>
          <span className={styles.brandTextWrap}>
            <strong className={styles.brandTitle}>Драгз.рф</strong>
            <span className={styles.brandMeta}>Безрецептурный навигатор</span>
          </span>
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

        <div className={styles.utilityNav}>
          {!user ? (
            <Link href="/login" className={pathname === "/login" ? styles.linkActive : styles.link}>
              Войти
            </Link>
          ) : (
            <>
              <span className={styles.userChip}>{user.email}</span>
              <Link href="/account" className={pathname === "/account" ? styles.linkActive : styles.link}>
                Личный кабинет
              </Link>
              {user.role === "admin" ? (
                <Link href="/admin" className={pathname === "/admin" ? styles.linkActive : styles.link}>
                  Админка
                </Link>
              ) : null}
              <button
                className={styles.logoutButton}
                type="button"
                onClick={async () => {
                  await logoutUser();
                  setUser(null);
                  router.push("/");
                  router.refresh();
                }}
              >
                Выйти
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
