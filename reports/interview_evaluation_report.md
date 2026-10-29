# IMAIRA FairScore — Candidate Interview Evaluation Report

**Date:** 2026-10-29 23:23:09

## 1. Executive Summary Table

| File | Matched Question | Completeness | Correctness | Structure | **Overall FairScore** |
|:---|:---|:---:|:---:|:---:|:---:|
| `test_voice_v3.wav` | **Q084**: Compare a Process and a Thread, and expl... | 3.67 | 5.0 | 4.1 | **3.53 / 5.0** |

---

## Candidate Evaluation: `test_voice_v3.wav`

- **Question [Q084]:** Compare a Process and a Thread, and explain common Inter-Process Communication (IPC) mechanisms.
- **Domain:** Databases & OS
- **Audio Duration:** 40.59s
- **Spoken Transcript:** "A process is a running program with its own memory space. So process cannot directly change another process's data. A thread is a unit of execution inside a process all threads in that process share the same heap memory. Because of this, creating a thread and doing a context switch between threads is cheaper than doing it for processes. The risk is that shared memory can cause a risk condition. So we protect it with a mutex or a semaphore. For example, a web browser can run each tab as a separate process for isolation while one tab uses several threads for rendering and network calls."

### Scores
- **Content Completeness Score:** 3.67 / 5.0
- **Content Correctness Score:** 5.0 / 5.0
- **Answer Structure Score:** 4.1 / 5.0
- **Calibrated Content Score:** 2.97 / 5.0
- **Calibrated Structure Score:** 4.37 / 5.0
- **OVERALL FAIRSCORE:** **3.53 / 5.0**

### ASR & Accent Corrections Applied
- `[4.66s - 5.28s]` Spoken `one process` $\rightarrow$ Corrected `process`
- `[10.70s - 11.32s]` Spoken `process and` $\rightarrow$ Corrected `process`
- `[28.60s - 29.02s]` Spoken `mutex` $\rightarrow$ Corrected `mutex`

### Rubric Idea Breakdown
- **[DEMONSTRATED] (1.0 pts) Q084_IDEA_1:** A process is an isolated execution instance with its own virtual address space, memory descriptors, file handles, and security context.
  - *Quote at [0.52s - 3.52s]:* "a process is a running program with its own memory"
- **[PARTIALLY_DEMONSTRATED] (0.5 pts) Q084_IDEA_2:** Threads are lightweight execution units within a process sharing the same address space, code segment, and heap, but retaining independent stacks and registers.
  - *Quote at [0.52s - 2.48s]:* "a process is a running program"
- **[PARTIALLY_DEMONSTRATED] (0.5 pts) Q084_IDEA_3:** IPC mechanisms enable processes to exchange data across isolated address spaces via pipes, shared memory, message queues, signals, and UNIX domain sockets.
  - *Quote at [0.52s - 2.48s]:* "a process is a running program"

---

