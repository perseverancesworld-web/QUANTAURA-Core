# Releasing

1. Ensure CI is green on `main`.
2. Bump `version` in `pyproject.toml` if needed.
3. Update `CHANGELOG.md` and `RELEASE_NOTES_vX.Y.Z.md`.
4. GitHub → **Releases** → **Draft a new release**
   - Tag: `vX.Y.Z` (not free-text names)
   - Target: `main`
   - Body: paste from `RELEASE_NOTES_vX.Y.Z.md`
5. Optional: publish to PyPI via the existing `python-publish` workflow.
6. Update repo **About** description in Settings → General.
