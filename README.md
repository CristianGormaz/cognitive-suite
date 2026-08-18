# Cognitive Suite
### Formerly Greys-v3

> **Historical sanitized snapshot — June 2026**
>
> This repository preserves a public, sanitized snapshot of Cognitive Suite as it existed in June 2026. It is **not** the current implementation mirror and should not be read as the authoritative current state of the private development line. The project architecture, evidence standards, and Greys/Cognitive Suite responsibility split evolved after this snapshot.
>
> The historical claims below are preserved as they were stated in the June snapshot. Their presence records what the project claimed at that time; it does not promote those claims to current verified properties.

**Cognitive Suite is an experimental local cognitive runtime designed to reduce unnecessary dependence on large language models.**

It works as a supervised decision exosuit: it observes failures, classifies risks, learns from bottlenecks, and converts known tasks into faster, safer local capabilities.

**It does not aim to replace a giant LLM; it aims to stop needing one for everything.**

---

## What it does
-   **Safe Multimodal Ingestion**: Processes text and files (`docx`, `txt`, `md`, `pdf`) locally.
-   **Local Decision Kernel**: Uses a `LocalIntentRouter` and a `LocalMicroClassifier` to solve tasks without external API calls.
-   **Bio-inspired Architecture**: Follows organic patterns (Dendrites, Myelin, Quorum) to manage autonomous evolution.
-   **Ledger Memory**: Records all activity in append-only, cryptographically signable ledgers for auditability and transparency.
-   **Dream Mode**: An asynchronous mode where the system analyzes its own operational data (experience mining) to propose development plans.

## What it DOES NOT do
-   **No Auto-modification**: Cognitive Suite never modifies its own core code without human approval.
-   **No Silent Internet Access**: Operates 100% locally by default.
-   **No Black-box Execution**: Every decision is auditable via its internal IAFA engine.

⚠️ **Experimental Status**: Cognitive Suite is a research project. It is not intended for critical production environments. Please review dependencies and security policies before granting permissions over sensitive files.

---

## Historical usage context

The June snapshot recorded the following prerequisites:

### Prerequisites
- Python 3.12+
- Local LLM server (Ollama recommended)
- DeepSeek-r1:8b or similar model for reasoning

The original installation block referenced the private `CristianGormaz/greys-v3` repository. That reference was never a valid public installation path for this sanitized snapshot, so it is not presented here as a current public installation instruction.

The snapshot also recorded this local usage command:

### Usage
```bash
export PYTHONPATH=src
python src/main.py --text "hello"
```

The source, tests, prompts, and documentation in this repository should be interpreted as artifacts of the June 2026 sanitized snapshot. For technical inspection, browse `src/`, `tests/`, and `docs/` directly.

`docs/CURRENT_STATE.md` is likewise preserved as a historical state record from that snapshot period, not as a statement of the project’s present implementation state.
