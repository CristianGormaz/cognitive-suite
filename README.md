# Cognitive Suite
### Formerly Greys-v3

> **Historical sanitized snapshot — June 2026**
>
> This repository preserves a public, sanitized snapshot of Cognitive Suite as it existed in June 2026. It is **not** the current implementation mirror and should not be read as the authoritative current state of the private development line. The project architecture, evidence standards, and Greys/Cognitive Suite responsibility split evolved after this snapshot.

**At the time of this snapshot, Cognitive Suite was described as an experimental local cognitive runtime designed to reduce unnecessary dependence on large language models.**

It was framed as a supervised decision exosuit: observing failures, classifying risks, learning from bottlenecks, and converting known tasks into faster, safer local capabilities.

**The historical goal was not to replace a giant LLM, but to stop needing one for everything.**

---

## What this June 2026 snapshot reported
- **Safe Multimodal Ingestion**: Processing text and files (`docx`, `txt`, `md`, `pdf`) locally.
- **Local Decision Kernel**: `LocalIntentRouter` and `LocalMicroClassifier` paths intended to solve selected tasks without external API calls.
- **Bio-inspired Architecture**: Dendrites, Myelin, and Quorum metaphors used to structure supervised evolution and promotion logic.
- **Ledger Memory**: Append-oriented audit records designed for traceability.
- **Dream Mode**: Asynchronous analysis of operational data to propose development plans.

## Historical safety boundaries
- **No Auto-modification**: The snapshot did not authorize self-modification of core code without human approval.
- **No Silent Internet Access**: Local operation was the default design intent.
- **No Black-box Execution**: Decisions were intended to remain auditable through the internal control surfaces.

⚠️ **Historical / experimental status**: this repository is preserved for technical inspection and project history. It is not intended for critical production environments and is not maintained as the current implementation distribution.

---

## Using this repository

The previous quickstart referenced the private `greys-v3` repository. That is no longer an appropriate public installation path, so it has been removed.

The source, tests, prompts, and documentation in this repository should be interpreted as artifacts of the June 2026 sanitized snapshot. For technical inspection, browse `src/`, `tests/`, and `docs/` directly.

`docs/CURRENT_STATE.md` is likewise preserved as a historical state record from that snapshot period, not as a statement of the project’s present implementation state.
