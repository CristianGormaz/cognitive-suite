# Cognitive Suite
### Formerly Greys-v3

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

## Getting Started

### Prerequisites
- Python 3.12+
- Local LLM server (Ollama recommended)
- DeepSeek-r1:8b or similar model for reasoning

### Installation
```bash
git clone https://github.com/CristianGormaz/greys-v3.git
cd greys-v3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage
```bash
export PYTHONPATH=src
python src/main.py --text "hello"
```

For a technical overview, check the `docs/` folder.
