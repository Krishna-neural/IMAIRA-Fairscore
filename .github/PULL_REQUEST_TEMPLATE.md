## Description
Brief summary of the changes introduced in this PR and the motivation behind them.

Fixes #(issue)

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement / Refactoring

## Architectural Invariants Verification
Please confirm that your changes uphold the three core system invariants:
- [ ] **5-Point Regional Accent Fairness**: Verified that identical technical answers scored across different accents vary by $\le 5.0$ points.
- [ ] **Privacy & Zero Audio Retention**: Verified that no raw audio files are stored permanently or checked into git.
- [ ] **Turnaround & Budget**: Verified scoring and timestamped feedback finish in $< 20\text{ seconds}$ with inference cost $< \text{₹}2.00$ per interview minute.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] All 144 unit/integration tests pass locally (`pytest tests/`)
- [ ] Judge Lab evaluation suite passes (`python tests/judge_lab.py`)
- [ ] Any dependent changes have been merged and published in downstream modules
