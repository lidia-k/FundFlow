# Repository Guidelines

## Project Structure & Module Organization
- FastAPI code lives in `backend/src/` (`api/`, `services/`, `database/`) with runtime config and entrypoints under `backend/app/`.
- Vite + React files reside in `frontend/src/`; static assets ship from `public/`, and cross-cutting TypeScript utilities belong in `shared/`.
- Operational resources: `data/` for local inputs/outputs, `docs/` for product notes, `scripts/` for automation, and `docker/` for compose assets.

## Build, Test, and Development Commands
- `make dev` starts the full Docker stack; prefer `make dev-local` for hot-reload `uvicorn` + `vite` during feature work.
- Run `make setup` after dependency changes; use `make build` or `make docker-build` when preparing release artifacts.
- Quality gates: `make test`, `make lint`, `make type-check`. Targeted runs include `npm run test:backend`, `cd frontend && npx playwright test`, and `npm run lint:backend`.

## Coding Style & Naming Conventions
- Backend Python follows `black` (88 cols), `isort`, `flake8`, and `mypy`; keep modules snake_case and type every public interface.
- Frontend relies on ESLint + Prettier + Tailwind plugin; components use PascalCase, hooks camelCase, and class names stay formatter-driven.
- Alembic revisions take concise snake_case messages (e.g., `add_tax_index`). Skip committing generated artifacts unless release engineering requests them.

## Testing Guidelines
- Place pytest suites in `backend/tests/{unit,integration,e2e}` with `test_*.py` names; use `pytest-asyncio` for async flows.
- E2E coverage uses Playwright in `frontend/tests/e2e`; run `cd frontend && npx playwright test` and inspect artifacts under `frontend/test-results/`.
- Run `make check` before every PR and add automated assertions for new endpoints or UI paths at the most appropriate test layer.

## Commit & Pull Request Guidelines
- Use Conventional Commits (`feat(scope): message`) under ~72 characters and written in the imperative mood.
- Branch from `main`, reference issues as `[#123]`, and squash fixups before requesting review.
- PRs supply a brief summary, test notes, UX media when relevant, and call out doc, migration, or env updates.

## Security & Configuration Tips
- Keep secrets out of git; update `.env.example` or `docs/` instead of committing `.env` files.
- Treat `data/uploads/` as transient storage—purge sensitive spreadsheets after debugging sessions.
- Route new configuration through `backend/app/core/config.py`, sourcing values from environment variables with safe defaults.
