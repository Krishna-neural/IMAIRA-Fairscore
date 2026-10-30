import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = BASE_DIR / "data" / "questions.json"

@dataclass
class RubricPoint:
    id: str
    text: str
    weight: float = 1.0
    description: str = ""

    @property
    def point_id(self) -> str:
        return self.id

DEFAULT_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q_db_01",
        "category": "Databases & Storage",
        "difficulty": "Medium",
        "display_title": "PostgreSQL B-Tree Indexing & Write Overhead",
        "spoken_question": "Hello and welcome to your technical interview. Let's begin with database internals. Can you explain how B-tree indexing works in PostgreSQL, and why secondary indexes might introduce significant write overhead during database operations?",
        "domain_terms": ["B-tree", "indexing", "write amplification", "heap", "tuples", "pointers", "vacuuming", "WAL"],
        "rubric": [
            {"id": "p1", "text": "Explains B-tree index structure and logarithmic read acceleration using sorted pointers to the table heap", "weight": 1.0, "description": "B-tree traversal and pointer resolution."},
            {"id": "p2", "text": "Details write amplification and secondary index maintenance cost during INSERT, UPDATE, and DELETE operations", "weight": 1.0, "description": "Explains why secondary index updates multiply disk writes."},
            {"id": "p3", "text": "Discusses MVCC dead tuple generation, HOT updates, and table bloat mitigation via vacuuming", "weight": 1.0, "description": "Heap-Only Tuples (HOT) and vacuum maintenance."}
        ]
    },
    {
        "id": "q_db_02",
        "category": "Databases & Concurrency",
        "difficulty": "Hard",
        "display_title": "ACID Properties & Multi-Version Concurrency Control (MVCC)",
        "spoken_question": "Great. Moving on to concurrency: how does relational database isolation work under high concurrency? Specifically, explain how MVCC avoids read-write blocking and what trade-offs exist with row-level versus table-level locks.",
        "domain_terms": ["MVCC", "ACID", "isolation level", "dirty read", "snapshot isolation", "deadlock", "row-level lock", "pessimistic locking"],
        "rubric": [
            {"id": "p1", "text": "Explains MVCC snapshot isolation mechanism where readers do not block writers and writers do not block readers", "weight": 1.0, "description": "Transaction visibility horizon and version snapshots."},
            {"id": "p2", "text": "Differentiates row-level and table-level locking trade-offs regarding granularity, lock contention, and overhead", "weight": 1.0, "description": "Fine-grained concurrency vs lock table memory."},
            {"id": "p3", "text": "Explains concurrency anomalies like deadlocks, write skew, or phantom reads under serializable isolation", "weight": 1.0, "description": "Anomaly prevention and detection."}
        ]
    },
    {
        "id": "q_ds_01",
        "category": "Data Structures",
        "difficulty": "Medium",
        "display_title": "Hash Table Collision Resolution & Dynamic Resizing",
        "spoken_question": "Let's test fundamental data structures. Could you explain how hash tables resolve collisions using separate chaining versus open addressing, and what happens to time complexity during dynamic resizing?",
        "domain_terms": ["hash map", "collision", "separate chaining", "open addressing", "linear probing", "load factor", "amortized O(1)"],
        "rubric": [
            {"id": "p1", "text": "Explains hash functions and separates separate chaining using linked buckets from open addressing probing techniques", "weight": 1.0, "description": "Mechanisms of handling key hash clashes."},
            {"id": "p2", "text": "Defines load factor thresholds and explains how exceeding the threshold degrades lookups to linear time", "weight": 1.0, "description": "Cluster formation and performance degradation."},
            {"id": "p3", "text": "Details dynamic rehashing and explains why table resize achieves amortized constant time complexity", "weight": 1.0, "description": "Doubling capacity and re-inserting elements."}
        ]
    },
    {
        "id": "q_sd_01",
        "category": "System Design",
        "difficulty": "Hard",
        "display_title": "Distributed Caching & Invalidation Strategies",
        "spoken_question": "In system design, distributed caching is vital for low-latency systems. Walk me through the trade-offs between Cache-Aside and Write-Through caching patterns, and how you prevent cache stampedes and stale data under high read traffic.",
        "domain_terms": ["cache aside", "write through", "cache stampede", "redis", "ttl", "stale data", "thundering herd", "mutex lock"],
        "rubric": [
            {"id": "p1", "text": "Contrasts Cache-Aside lazy loading with Write-Through synchronous cache-database writes", "weight": 1.0, "description": "Read and write path differences."},
            {"id": "p2", "text": "Explains cache invalidation techniques using TTL expiration, probabilistic early expiration, or explicit eviction", "weight": 1.0, "description": "Data consistency between cache and origin database."},
            {"id": "p3", "text": "Mitigates cache stampede and thundering herd problems using distributed locks or mutex-protected cache warming", "weight": 1.0, "description": "Preventing database overload upon key expiration."}
        ]
    },
    {
        "id": "q_os_01",
        "category": "Operating Systems",
        "difficulty": "Medium",
        "display_title": "Process vs Thread Architecture & Context Switching",
        "spoken_question": "Now consider operating systems. What is the fundamental architectural difference between a process and a thread in terms of memory isolation, and what specific CPU operations occur during a context switch?",
        "domain_terms": ["process", "thread", "virtual memory", "context switch", "TLB", "page table", "CPU registers", "IPC"],
        "rubric": [
            {"id": "p1", "text": "Distinguishes process independent address space and page tables from threads sharing virtual memory heap and code segments", "weight": 1.0, "description": "Memory boundaries and stack vs heap isolation."},
            {"id": "p2", "text": "Details the context switch lifecycle including saving and restoring CPU registers, program counter, and stack pointer", "weight": 1.0, "description": "Hardware state persistence in kernel PCB/TCB."},
            {"id": "p3", "text": "Explains the performance overhead of TLB invalidation and cache misses during process context switches compared to thread switches", "weight": 1.0, "description": "Memory management unit and translation lookaside buffer flushing."}
        ]
    }
]

_QUESTIONS_CACHE: Optional[List[Dict[str, Any]]] = None

def load_questions() -> List[Dict[str, Any]]:
    global _QUESTIONS_CACHE
    if _QUESTIONS_CACHE is not None:
        return _QUESTIONS_CACHE

    if QUESTIONS_PATH.exists():
        try:
            with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
                _QUESTIONS_CACHE = json.load(f)
                return _QUESTIONS_CACHE
        except Exception:
            pass

    _QUESTIONS_CACHE = list(DEFAULT_QUESTIONS)
    return _QUESTIONS_CACHE

def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    questions = load_questions()
    for q in questions:
        if q.get("id") == question_id:
            return q
    return None

def get_categories() -> List[str]:
    questions = load_questions()
    categories = sorted(list({q.get("category", "General") for q in questions}))
    return categories

def get_rubric_points(question_id: str) -> List[RubricPoint]:
    q = get_question_by_id(question_id)
    if not q:
        return []
    return [
        RubricPoint(
            id=str(r.get("id", f"p{idx+1}")),
            text=str(r.get("text", "")),
            weight=float(r.get("weight", 1.0)),
            description=str(r.get("description", ""))
        )
        for idx, r in enumerate(q.get("rubric", []))
    ]
