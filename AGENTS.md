# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a clean root with no committed application code yet. Keep the top level minimal and introduce standard directories as the project grows:

- `src/` for application code
- `tests/` for automated tests
- `docs/` for design notes and contributor-facing documentation
- `assets/` for static files such as images or fixtures

Prefer small, focused modules. Group code by feature or domain instead of creating deep utility folders too early.

## Build, Test, and Development Commands
There are no build or test scripts checked in yet. When adding tooling, expose a small, consistent command surface and document it here. Recommended conventions:

- `make dev` or `npm run dev` for local development
- `make test` or `npm test` for the full test suite
- `make lint` or `npm run lint` for static checks
- `make format` or `npm run format` for code formatting

Contributors should avoid introducing one-off local commands that are not committed to the repository.

## Coding Style & Naming Conventions
Use 4 spaces for Python and 2 spaces for JavaScript, TypeScript, JSON, YAML, and Markdown. Use descriptive names:

- `snake_case` for Python files and functions
- `camelCase` for JavaScript and TypeScript variables/functions
- `PascalCase` for classes and UI components

Adopt an automatic formatter and linter with the first language/toolchain you add, then keep configuration in the repo root.

## Testing Guidelines
Place tests under `tests/` and mirror the source layout where practical. Use explicit names such as `test_auth.py` or `user.service.test.ts`. New features should include tests for expected behavior and edge cases. Do not merge code that cannot be exercised locally with a documented command.

## Commit & Pull Request Guidelines
No Git history is available in the current workspace, so follow Conventional Commits until the project establishes a house style, for example: `feat: add initial API scaffold` or `fix: validate empty config values`.

Pull requests should include a short summary, testing notes, and any setup changes. Add screenshots or sample requests/responses for UI or API changes.

## Security & Configuration Tips
Do not commit secrets, `.env` files, or machine-specific settings. Commit an `.env.example` when configuration is introduced, and document required variables in `docs/` or the project `README`.
