# Pharmacy Price Map Chat Prototype Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Next.js prototype that matches the provided pharmacy search design with hero search, price summary, availability table, map-style panel, and AI advice panel.

**Architecture:** Use a single App Router page with static sample data and CSS modules for layout fidelity. Verify the page structure with a focused render test before implementing the production page and styles.

**Tech Stack:** Next.js, React, TypeScript, Vitest, Testing Library, CSS Modules

### Task 1: Bootstrap the Next.js workspace

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `next-env.d.ts`
- Create: `next.config.ts`
- Create: `.gitignore`
- Create: `app/layout.tsx`
- Create: `app/page.tsx`
- Create: `app/globals.css`
- Create: `public/.gitkeep`

**Step 1:** Add the package manifest with Next.js, React, TypeScript, Vitest, and Testing Library dependencies.

**Step 2:** Add TypeScript and Next.js config files for an App Router project.

**Step 3:** Create the root layout and global stylesheet entrypoint.

### Task 2: Add the first failing UI test

**Files:**
- Create: `tests/home-page.test.tsx`
- Create: `tests/setup.ts`
- Modify: `package.json`
- Modify: `tsconfig.json`

**Step 1:** Write a render test that expects the main pharmacy search heading plus sections for the availability table, map panel, and AI consultation panel.

**Step 2:** Run the test to confirm it fails for the expected missing-content reason.

### Task 3: Implement the page structure and sample data

**Files:**
- Modify: `app/page.tsx`
- Create: `app/page.module.css`

**Step 1:** Build the page with static sample content matching the design: header, hero/search block, selected medicine card, metric cards, availability table, map panel, and AI advice card.

**Step 2:** Add supporting arrays for pharmacies, filters, metrics, and prompt chips directly in the page module to keep the prototype self-contained.

**Step 3:** Run the test again and confirm it passes.

### Task 4: Polish styling to match the design language

**Files:**
- Modify: `app/globals.css`
- Modify: `app/page.module.css`

**Step 1:** Define the palette, spacing, border radius, and typography to match the pale clinical dashboard look from the design.

**Step 2:** Add responsive behavior so the layout collapses cleanly on narrow screens.

**Step 3:** Re-run tests and a production build to verify the prototype is stable.
