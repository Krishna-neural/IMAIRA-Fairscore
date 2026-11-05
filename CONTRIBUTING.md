# Contributing to IMAIRA FairScore

Thank you for your interest in contributing to **IMAIRA FairScore**! We are building an interview evaluation pipeline that *"hears the answer, not the accent"*, ensuring that first-generation graduates and students schooled in Tamil, Kannada, Telugu, or Hindi medium are evaluated fairly on technical merit.

Please take a moment to review this document before submitting contributions, bug reports, or pull requests.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to [krishnagupta.neural@gmail.com](mailto:krishnagupta.neural@gmail.com).

---

## Core System Invariants

Every code contribution **must uphold these three non-negotiable architectural invariants**:

1. **5-Point Regional Fairness Guarantee**:
   The content score must vary by **no more than 5 points out of 100** when identical technical content is delivered across diverse Indian regional accents (Tamil, Telugu, Kannada, Hindi, and neutral standard). Accent features must carry a mathematical $0.0$ penalty on content scores.
2. **Strict Privacy & Zero Audio Retention**:
   Raw candidate voice recordings are processed strictly in-memory or via ephemeral audio buffers and **must be destroyed immediately after scoring**, unless the candidate explicitly opts in to save them. Never commit audio files (`.wav`, `.m4a`, `.mp3`, `.mp4`) to the repository.
3. **Turnaround & Cost Bounds**:
   Comprehensive 3-pillar scoring and timestamped, actionable feedback must return in **under 20 seconds** from answer completion, maintaining an inference cost **under ₹2.00 per interview minute**.

---

## Repository Structure

```
IMAIRA_WORKSPACE/IMAIRA_UNIFIED_INTEGRATION/
├── app/                  # FastAPI ASGI service, REST endpoints, WebSocket & SSE streaming
├── asr/                  # ASR post-processing, two-pass recovery, phoneme alignment
├── database/             # SQLite session models, turn history, and persistence
├── data/                 # Question bank (120 Qs), technical glossary (2,000 terms), rubrics
├── evaluation/           # Decoupled scoring pipeline (Content 60%, Structure 40%), feedback generator
├── frontend_prototype/   # React 18, Vite, Tailwind CSS, Lucide icons (Google Stitch Dark Tech UI)
│   ├── src/              # Application components, hooks, sound feedback
│   └── dist/             # Compiled production bundle served directly by FastAPI
├── scripts/              # Verification runners and deployment entrypoints
├── tests/                # 144 unit/integration tests & 18 Judge Lab validation scenarios
├── Dockerfile            # Production container configuration
├── LICENSE               # MIT Open Source License
└── README.md             # Project documentation & live deployment links
```

---

## Development Setup

### Prerequisites
- **Python**: 3.10 or 3.11 (Python 3.11 recommended)
- **Node.js**: v18.0.0 or higher (for frontend prototype development)
- **Git**: 2.30+
- **Hardware**: CPU (Intel/AMD) or NVIDIA GPU with CUDA 11.8/12.1+

### 1. Backend Setup
Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/Krishna-neural/IMAIRA-Fairscore.git
cd IMAIRA-Fairscore

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Frontend Setup (Optional for UI Changes)
The frontend production build is pre-compiled into `frontend_prototype/dist/`. If modifying UI components:

```bash
cd frontend_prototype
npm install
npm run build   # Compiles to dist/ for FastAPI static hosting
npm run dev     # Runs local Vite dev server on port 5173
```

### 3. Launching the Local Server
```bash
python run.py
```
Visit `http://localhost:8000` to interact with the unified interview simulator.

---

## Verification & Testing

Before submitting a Pull Request, all automated test suites must pass without regressions:

### Unit & Integration Suite (144 Tests)
```bash
pytest tests/ -v
```

### Judge Lab Validation Suite (18 Scenarios)
Verifies rubric alignment against dual human interviewer rubrics across 120 question rubrics:
```bash
python tests/judge_lab.py
```

### 5-Point Regional Accent Fairness Benchmark
Verifies the accent invariance constraint across all 120 technical questions:
```bash
python -c "from evaluation.fairness_audit import run_full_benchmark_audit; print(run_full_benchmark_audit())"
```

---

## Git Workflow & Branching Strategy

1. **Fork or Branch**:
   - Create a feature branch off `main`:
     ```bash
     git checkout -b feature/your-feature-name
     ```
   - For bug fixes:
     ```bash
     git checkout -b bugfix/issue-description
     ```
2. **Commit Guidelines**:
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(asr)`: Add dynamic confidence weighting for phoneme aligner
   - `fix(eval)`: Prevent division by zero on empty candidate utterances
   - `docs(readme)`: Update deployment URLs and API contracts
   - `test(fairness)`: Add additional code-mixing test cases
   - `chore(deps)`: Bump fastapi and pydantic versions
3. **Pull Request Process**:
   - Target the `main` branch.
   - Fill out the PR template completely.
   - Ensure CI / local test checks pass.
   - Maintainers will review your PR and provide constructive feedback.

---

## Questions and Support

- Join our discussions on [GitHub Issues](https://github.com/Krishna-neural/IMAIRA-Fairscore/issues).
- For privacy or security inquiries, see [SECURITY.md](SECURITY.md).
