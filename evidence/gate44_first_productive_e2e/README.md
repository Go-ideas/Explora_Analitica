# Gate 44 — First Productive Project End-to-End Evidence

This directory is the controlled evidence boundary for Gate 44.

Target release structure:

```text
gate44_first_productive_e2e/
  input/
  config/
  canonical/
  web/
  excel/
  qa/
  provenance/
  release_manifest.json
```

Rules:

- Do not commit confidential customer raw data unless explicitly authorized.
- Do not fabricate missing productive inputs.
- Canonical Results are the analytical authority.
- Web and Excel must consume the same released Canonical Results.
- Any unsupported or unresolved material configuration must fail closed.
- Gate 44 evidence is not authorization to generalize Benchmark A behavior into Core.
