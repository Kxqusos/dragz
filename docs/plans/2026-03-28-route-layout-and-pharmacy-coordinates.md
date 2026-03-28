# Route Layout And Pharmacy Coordinates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the "Построить маршрут по корзине" button alignment and persist pharmacy coordinates in Postgres with manual Alembic migrations.

**Architecture:** The frontend route action will get its own layout wrapper so spacing stays consistent with the cart block above and the route summary below. The backend geocoding flow will read and write a Postgres-backed pharmacy coordinate store, while Redis remains an optional short-term cache. Alembic will own schema creation through explicit hand-written revisions.

**Tech Stack:** Next.js 15, React 19, FastAPI, SQLAlchemy asyncio, PostgreSQL, Redis, Alembic, Node test runner, pytest.

### Task 1: Document Current Root Causes

**Files:**
- Inspect: `frontend/components/mvp/SearchExperience.tsx`
- Inspect: `frontend/components/mvp/search-experience.module.css`
- Inspect: `backend/app/services/geocoding.py`
- Inspect: `backend/app/jobs/refresh_geocodes.py`

**Step 1: Confirm the button layout bug**

Root cause to verify:
- The route button is rendered as a bare sibling after `CartPanel` with no route-action wrapper.
- `primaryButton` has no section-specific spacing rules.
- The blocks around it use card spacing (`margin-top: 16px`) but the button does not.

**Step 2: Confirm the coordinate persistence gap**

Root cause to verify:
- Pharmacy coordinates are currently resolved via geocoding and Redis cache only.
- Postgres models do not contain a pharmacy coordinate table.
- Refresh jobs iterate over Redis geocode records instead of persisted database rows.

### Task 2: Add Failing Frontend Regression Tests

**Files:**
- Create: `frontend/components/mvp/search-experience-layout.test.mjs`
- Modify: `frontend/package.json`
- Inspect: `frontend/components/mvp/SearchExperience.tsx`

**Step 1: Write the failing test**

Add a node test that reads `SearchExperience.tsx` and asserts:
- the route action button is wrapped in a dedicated layout container class
- the wrapper class name is present in JSX near the button

**Step 2: Run test to verify it fails**

Run: `node --test frontend/components/mvp/search-experience-layout.test.mjs`
Expected: FAIL because no dedicated wrapper exists yet.

### Task 3: Add Failing Backend Persistence Tests

**Files:**
- Create: `backend/tests/test_pharmacy_coordinates_store.py`
- Create: `backend/tests/test_refresh_geocodes.py`
- Modify: `backend/requirements.txt`

**Step 1: Write failing tests for the store**

Add tests for:
- upserting a resolved pharmacy coordinate row by normalized address
- reusing persisted coordinates before external geocoding
- storing unresolved or rate-limited statuses with timestamps

**Step 2: Write failing tests for refresh job selection**

Add tests for:
- selecting due records from Postgres instead of Redis scan iteration
- refreshing only rows that are due by status and timestamp

**Step 3: Run tests to verify they fail**

Run: `pytest backend/tests/test_pharmacy_coordinates_store.py backend/tests/test_refresh_geocodes.py -q`
Expected: FAIL because the repository, DB session wiring, and refresh integration do not exist yet.

### Task 4: Implement Postgres Coordinate Persistence

**Files:**
- Modify: `backend/app/db/models.py`
- Create: `backend/app/db/dependencies.py`
- Create: `backend/app/services/pharmacy_coordinates.py`
- Modify: `backend/app/services/geocoding.py`
- Modify: `backend/app/services/offer_enrichment.py`
- Modify: `backend/app/api/routes/search.py`
- Modify: `backend/app/api/routes/route.py`
- Modify: `backend/app/jobs/refresh_geocodes.py`
- Modify: `backend/app/main.py`

**Step 1: Add SQLAlchemy model**

Create a persisted table with fields for:
- normalized address
- original address
- lat/lon
- status
- provider
- query text
- updated timestamp

Use a unique constraint on normalized address.

**Step 2: Add async session dependency**

Create shared engine/session factory wiring from `Settings.database_url`, then expose a FastAPI dependency and job helper for opening sessions.

**Step 3: Add repository/service helpers**

Implement helpers to:
- normalize lookup keys
- get a persisted record by address
- upsert records after geocoding
- list due records for passive refresh

**Step 4: Integrate geocoding flow**

Change `geocode_address` so it:
- checks Postgres first unless forced refresh
- falls back to Redis cache and providers as needed
- writes provider results to Postgres and Redis

**Step 5: Integrate API and job callers**

Pass database session into search, route, and refresh flows so they can use the store consistently.

### Task 5: Add Alembic With Manual Revisions

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/20260328_01_create_search_and_pharmacy_coordinate_tables.py`
- Modify: `backend/Dockerfile`
- Modify: `docker-compose.yml`

**Step 1: Add Alembic configuration**

Point Alembic at backend metadata and reuse `DATABASE_URL`.

**Step 2: Write manual revision**

Create explicit SQLAlchemy operations for:
- `search_sessions`
- `pharmacy_coordinates`

If `search_sessions` already exists in model metadata, bring it under migration control inside the first revision.

**Step 3: Wire migrations into runtime**

Ensure containers can run Alembic and document or automate migration execution before app start.

### Task 6: Implement Frontend Layout Fix

**Files:**
- Modify: `frontend/components/mvp/SearchExperience.tsx`
- Modify: `frontend/components/mvp/search-experience.module.css`

**Step 1: Add a dedicated route action wrapper**

Wrap the route button in a layout container with top spacing aligned to the card rhythm.

**Step 2: Refine button sizing/alignment**

Make the wrapper and button stretch cleanly within the panel so the action sits evenly between the cart block and the route summary card.

### Task 7: Verify End To End

**Files:**
- Verify: `frontend/components/mvp/search-experience-layout.test.mjs`
- Verify: `backend/tests/test_pharmacy_coordinates_store.py`
- Verify: `backend/tests/test_refresh_geocodes.py`

**Step 1: Run frontend test**

Run: `node --test frontend/components/mvp/route-stop-presentation.test.mjs frontend/components/mvp/search-experience-layout.test.mjs`
Expected: PASS

**Step 2: Run backend tests**

Run: `pytest backend/tests/test_pharmacy_coordinates_store.py backend/tests/test_refresh_geocodes.py -q`
Expected: PASS

**Step 3: Run migration sanity check**

Run: `alembic -c backend/alembic.ini upgrade head`
Expected: Revision applies cleanly against Postgres.
