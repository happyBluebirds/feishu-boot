# Contributing

Contributions are welcome.

Please do not include real credentials, chat IDs, local project paths, logs, screenshots, state files, approval queues, or private workspace content in issues, pull requests, examples, or tests.

## Good First Contributions

- Improve setup documentation.
- Add tests for command parsing and state transitions.
- Add safer defaults for local execution.
- Add Codex workflow examples for triage, review, maintainer workflows, PR workflows, and release workflows.
- Improve log redaction and error messages.

## Pull Request Checklist

- Keep examples sanitized.
- Add or update tests when behavior changes.
- Update README or SECURITY notes when changing execution or permission behavior.
- Avoid broad refactors mixed with feature changes.
- Explain local execution impact clearly.

## Development

Run the focused Codex bridge tests:

```powershell
cd feishu-codex
python -m pip install -r requirements.txt
python -m pip install pytest
pytest -q
```
