# GitHub workflow preparation

November 3, 2026. Remote baseline b4f8324d84766d40a4b8104b47cf7716dd57c1b5.
Clone/test/build commands and Windows secret-directory guidance added.
README HTTP contradiction corrected; image build context includes LICENSE.
Fresh rerun: Ruff, formatting, pyrefly, 77 tests with 97.50% coverage,
structure PASS. Browser report gate attempted but blocked by absent Chromium.
No Docker build/startup, remote host, or Grafana visual pass claimed.
GitHub branch is a review candidate, not a deployed or merged release.

Normal isolated uv build PASS. Non-isolated build attempt failed because
hatchling was not installed in the development environment; no-isolation is
not the documented workflow. CI now builds image and runs installed CLI version
on Python 3.13 after full application gates; hosted run pending.

## First hosted CI run

Run 41714747102 passed all ten application validation gates on Python 3.12 and 3.13, including browser reports and wheel installation. Docker build caught LICENSE excluded from the allowlisted build context. Added LICENSE to .dockerignore inclusion list; the follow-up CI run will establish the container result.
