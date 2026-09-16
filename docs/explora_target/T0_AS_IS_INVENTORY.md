# T0 AS-IS INVENTORY

Date: 2026-09-16

## Physical Source Root

`C:\Users\conta\Go ideas\Local Go ideas - Documentos\Desarrollo\Explora Analitica`

The executable physical project adopted for T0 is:

`explora_web_reporter/`

The workspace root also contains local historical folders, client data, checkpoints, evidence, and temporary inputs that are not part of the GitHub adoption payload.

## Git State Before Adoption

- Physical workspace root: not a Git repository.
- Local Git folder found before adoption: `explora_console_github/.git`, branch `master`, no commits, unrelated to the accepted physical baseline.
- Target repository: `https://github.com/Go-ideas/Explora_Analitica.git`
- Target branch: `migration/t0-canonical-baseline`
- PR #1 head before adoption: `80cd6032c4d8a29d54c4dcd870f484c745ee92ec`
- Main branch before adoption: `124384890b3fa048ca5c554ffb1e5ead1d68ee2a`

## Environment

- Python: `3.13.3`
- `py` launcher: not available in this environment.
- Test invocation requires `PYTHONPATH=.` from `explora_web_reporter/`.

## Dependency Files

- `explora_web_reporter/requirements.txt`

Dependencies listed:

- streamlit
- pandas
- numpy
- pyreadstat
- openpyxl
- xlsxwriter
- plotly
- scipy
- statsmodels
- python-dotenv

## Source Directories Adopted

- `explora_web_reporter/src/analytics_core/`
- `explora_web_reporter/src/builder/`
- `explora_web_reporter/src/contracts/`
- `explora_web_reporter/src/database/`
- `explora_web_reporter/src/export/`
- `explora_web_reporter/src/readers/`
- `explora_web_reporter/src/reporter/`
- `explora_web_reporter/src/structure/`
- `explora_web_reporter/src/ui/`
- `explora_web_reporter/src/utils/`
- `explora_web_reporter/src/web_canonical/`

## Test Directories Adopted

- `explora_web_reporter/tests/`

Current physical test file count: 59.

## Contracts And Canonical Policies Adopted

- `docs/explora_target/WEIGHT_POLICY_CANONICAL.md`
- `docs/explora_target/SIGNIFICANCE_POLICY_CANONICAL.md`
- `docs/explora_target/AI_RELEASE_POLICY_CANONICAL.md`
- `docs/explora_target/EXPLORA_GATE1_CANONICAL.md`
- `docs/explora_target/CANONICAL_PROJECT_MATERIALIZATION_CONTRACT.md`
- M1A, M2, M3, M4, M5, M6 implementation and remediation manifests present under `docs/explora_target/`.

## Checkpoint Candidates Found Locally

- `M5_CANONICAL_EXECUTION_ADAPTER_CORRECTIVE_REVIEW_CHECKPOINT_2026-09-15.zip`
  - SHA-256: `B273D859FB29FA01129B8DE622646A197D48472DCB3B0E568E42AFFD15A81159`
  - Matches historical expected SHA.
- `M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATED_V3_2026-09-15.zip`
  - SHA-256: `1BAE7A3D48A3A196E95957BAD27D506D36253C83C692C52A8FB1B066CC2AD3C7`
  - Contains M6 V3 docs/source/tests matching sampled physical hashes.

No single checkpoint ZIP was found that exactly represents the entire current physical source tree. The accepted physical baseline is therefore reconciled from current source plus area-specific accepted checkpoints and current regression evidence.

## Generated And Excluded Artifacts

Excluded from GitHub:

- `.sav`, `.zsav`, `.por`
- productive `.db`, `.sqlite`, `.sqlite3`
- `.env`, `.env.*` except safe examples
- Streamlit secrets
- `explora_web_reporter/data/`
- root `checkpoints/`
- root `evidence/`
- `_gate19_inputs/`
- pytest temp directories
- `__pycache__/`
- `.pyc`
- Streamlit logs
- client deliverables and local Excel/ZIP artifacts

## Client / Source Data Found And Excluded

Local workspace includes SAV and SQLite files under `GPT/`, `TEST/`, `_gate19_inputs/`, `explora_builder/data/`, and `explora_web_reporter/data/`. These were not copied into the migration branch.

## Materialization Package Status

`explora_web_reporter/src/canonical_materialization/` was not present in the physical source tree at T0 inspection time.

No `*materialization*.py` test files were present under `explora_web_reporter/tests/`.
