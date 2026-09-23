# Gate 48 — Streamlit Community Cloud Deployment

## Purpose

Deploy the additive EXPLORA Operator Console without replacing the existing
legacy/internal Streamlit surfaces.

## Deployment target

Workspace:

`https://share.streamlit.io/`

Repository:

`Go-ideas/Explora_Analitica`

Review branch:

`feature/gate48-streamlit-operator-console`

Entrypoint:

`explora_web_reporter/operator_console.py`

Dependency file:

`explora_web_reporter/requirements.txt`

Community Cloud supports an entrypoint in a subdirectory and looks for dependency
files next to the entrypoint or at repository root.

## Mandatory privacy control

The repository is public.

The Operator Console accepts customer SAV/questionnaire/datamap artifacts.
Therefore a real-customer deployment MUST be private before customer data is
uploaded.

After deployment:

1. Open App settings.
2. Open Sharing.
3. Set access to **Only specific people can view this app**.
4. Confirm the app is not public/searchable.
5. Only then upload real customer data.

A public deployment may be used only with synthetic/non-customer fixtures.

## Console boundaries

The console orchestrates accepted EXPLORA contracts. It does not calculate
official statistics independently.

Gate 48 V1:

- accepts SAV source upload;
- accepts questionnaire/datamap as evidence;
- validates an existing Project Spec;
- surfaces ambiguity/AI/B3 decisions;
- requires explicit B3 human approval;
- builds the deterministic Gate 47 RELEASED package;
- executes CANONICAL_V1 for WEB-only output intent;
- exposes release/QA/provenance files for download.

Gate 48 V1 does NOT:

- generate Project Spec automatically from questionnaire/datamap;
- silently approve AI decisions;
- execute EXCEL when an M7 QualifiedMaster has not been integrated;
- store customer raw data in Git.

## Deployment validation

Initial deployment should use synthetic data.

Before real-project use verify:

- app starts without import/build errors;
- Project Spec validation renders;
- B3 pending state blocks package creation;
- B3 approval validates the Execution Release;
- package download works;
- WEB-only CANONICAL execution works;
- EXCEL intent fails closed;
- session cleanup removes temporary workspace;
- app privacy is PRIVATE.
