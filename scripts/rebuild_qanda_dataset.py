#!/usr/bin/env python3
"""Rebuild data/QandA.json with 120 unique, technically rigorous, non-templated questions and answers,
and attach CPU 1 compatible semantic rubric ideas to make the dataset directly compatible and viable.
"""

import json
from pathlib import Path

# Define full specific records for all 120 questions
RECORDS = [
    # --- Software and Computer Science Fundamentals (ENG001 - ENG030) ---
    {
        "id": "ENG001",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Data Structures and Algorithms",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "question": "Compare Red-Black Trees and AVL Trees in terms of balancing invariants, tree height, and search versus insertion/deletion performance.",
        "answer": "AVL trees maintain a strict balancing invariant where the height difference (balance factor) between left and right subtrees of any node is at most 1. In contrast, Red-Black trees enforce coloring constraints (root is black, no two consecutive red nodes, equal black-height) which allows the longest path to be up to twice the length of the shortest path. Consequently, AVL trees have smaller maximum heights (~1.44 log N vs ~2 log N), resulting in faster O(log N) lookup times. However, Red-Black trees require at most two rotations per insertion and three per deletion, making them faster for write-intensive workloads, whereas AVL trees may trigger up to O(log N) rotations on deletion.",
        "glossary_terms_used": ["AVL tree", "Red-Black tree", "balance factor", "black-height", "tree rotation", "time complexity"],
        "key_concepts": ["Self-Balancing Binary Search Trees", "Tree Rotations", "Lookup vs Insertion Tradeoffs"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG001_IDEA_1",
                "semantic_statement": "Explains that AVL trees enforce stricter balance factor limits (at most 1) compared to Red-Black tree color and black-height rules.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts explanations contrasting strict height equality with Red-Black coloring paths."
            },
            {
                "idea_id": "ENG001_IDEA_2",
                "semantic_statement": "Articulates the performance tradeoff: AVL provides faster searches due to shorter height, while Red-Black trees require fewer rotations for write operations.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts stating AVL is search-optimized while Red-Black is insertion/deletion-friendly."
            }
        ]
    },
    {
        "id": "ENG002",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Object-Oriented Programming",
        "difficulty": "Advanced",
        "question_type": "Technical Application",
        "question": "How do you design an extensible payment processing module applying the Open/Closed Principle and the Strategy pattern?",
        "answer": "To implement an extensible payment processing subsystem adhering to the Open/Closed Principle, declare an abstract PaymentStrategy interface exposing a common method such as process_payment(payment_request: PaymentRequest) -> PaymentResult. Concrete strategies (e.g., StripePaymentStrategy, PayPalPaymentStrategy, BankTransferStrategy) implement this interface independently. A PaymentProcessor context class receives the selected strategy via constructor dependency injection or a factory. Adding a new payment provider requires only authoring a new concrete strategy class without modifying the existing PaymentProcessor or core business logic.",
        "glossary_terms_used": ["Open/Closed Principle", "Strategy pattern", "dependency injection", "interface", "loose coupling"],
        "key_concepts": ["Object-Oriented Design", "Extensibility", "SOLID Principles"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG002_IDEA_1",
                "semantic_statement": "Defines an abstract strategy interface and concrete provider classes to decouple business logic from provider implementations.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts defining common payment interface or polymorphic adapter classes."
            },
            {
                "idea_id": "ENG002_IDEA_2",
                "semantic_statement": "Demonstrates Open/Closed compliance by explaining that adding a new payment vendor requires only adding a new class without altering existing caller code.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts explanations of adding features by extension rather than code modification."
            }
        ]
    },
    {
        "id": "ENG003",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Operating Systems & Concurrency",
        "difficulty": "Expert",
        "question_type": "Scenario-Based",
        "question": "How do you identify, diagnose, and resolve priority inversion in a multi-threaded real-time system?",
        "answer": "Priority inversion occurs when a low-priority thread holds a shared mutex that a high-priority thread needs, and a medium-priority thread preempts the low-priority thread, indirectly starving the high-priority thread. Diagnosis involves profiling thread states, analyzing CPU runqueues, and examining lock acquisition latency where high-priority real-time deadlines are missed while CPU is consumed by medium-priority tasks. The primary resolution is Priority Inheritance (PIP), where the low-priority thread holding the mutex temporarily inherits the priority of the waiting high-priority thread until it releases the lock, or Priority Ceiling Protocol (PCP) where every mutex is assigned a static ceiling priority.",
        "glossary_terms_used": ["priority inversion", "priority inheritance", "mutex", "preemption", "real-time operating system", "lock contention"],
        "key_concepts": ["Real-Time Scheduling", "Deadlock & Starvation Prevention", "Synchronization Primitives"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG003_IDEA_1",
                "semantic_statement": "Identifies that a medium-priority task preempts a low-priority lock-holder, indirectly blocking a high-priority waiting thread.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts describing the intermediate thread starving the critical high-priority task."
            },
            {
                "idea_id": "ENG003_IDEA_2",
                "semantic_statement": "Explains resolution using Priority Inheritance Protocol or Priority Ceiling Protocol to temporarily boost lock-holder priority.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts priority boosting or priority inheritance mechanisms."
            }
        ]
    },
    {
        "id": "ENG004",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Database Design & Transactions",
        "difficulty": "Intermediate",
        "question_type": "Technical Application",
        "question": "When designing an e-commerce catalog, what are the architectural tradeoffs between normalized relational tables and JSON/document attributes?",
        "answer": "Normalized relational modeling (e.g., product, category, attribute, and product_attribute tables) provides strict data integrity, foreign key validation, and eliminates redundancy. However, querying dynamic polymorphic product attributes requires expensive multi-table JOINs and entity-attribute-value (EAV) antipattern complexity. Storing dynamic attributes in a JSONB/document field within a relational product table offers schema flexibility, allowing arbitrary product specifications without schema migrations, and fast single-row reads. The tradeoff is weaker cross-attribute referential integrity, larger storage footprint, and the need for specialized GIN indexes for efficient attribute filtering.",
        "glossary_terms_used": ["normalization", "JSONB", "GIN index", "EAV antipattern", "referential integrity", "schema migration"],
        "key_concepts": ["Relational vs Document Modeling", "Index Optimization", "Data Integrity vs Flexibility"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG004_IDEA_1",
                "semantic_statement": "Contrasts relational integrity and schema rigidity against JSON flexibility for dynamic polymorphic product attributes.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts comparing strict foreign keys/joins with flexible schema-on-read JSON."
            },
            {
                "idea_id": "ENG004_IDEA_2",
                "semantic_statement": "Mentions indexing and query performance considerations such as GIN indexes on JSONB versus B-Tree indexes on relational columns.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts indexing differences or query latency comparisons."
            }
        ]
    },
    {
        "id": "ENG005",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Software Architecture & Design Patterns",
        "difficulty": "Expert",
        "question_type": "Scenario-Based",
        "question": "How do you migrate a synchronous monolithic order flow to an asynchronous event-driven architecture using the Outbox pattern and Change Data Capture?",
        "answer": "In a synchronous monolith, order creation, payment charging, inventory deduction, and notifications happen within a single thread or database transaction, creating high latency and single points of failure. In the event-driven migration, the order service commits the order state and an 'OrderCreated' event record to an outbox table within the same local ACID transaction. A Change Data Capture (CDC) engine such as Debezium tails the database transaction log and publishes the outbox event to Apache Kafka with at-least-once delivery. Downstream microservices (inventory, payment, email) consume the event independently and update their states asynchronously with idempotent consumer processing.",
        "glossary_terms_used": ["Transactional Outbox pattern", "Change Data Capture", "Debezium", "Apache Kafka", "at-least-once delivery", "idempotency"],
        "key_concepts": ["Event-Driven Architecture", "Dual-Write Problem", "Asynchronous Messaging"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG005_IDEA_1",
                "semantic_statement": "Explains that the Transactional Outbox pattern writes domain data and event records atomically inside the same database transaction to prevent dual-write inconsistency.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts atomic insert of event and entity in one local database commit."
            },
            {
                "idea_id": "ENG005_IDEA_2",
                "semantic_statement": "Describes CDC log-tailing to publish events asynchronously to Kafka and requiring downstream consumers to be idempotent.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts Debezium/log streaming and idempotent consumer handling."
            }
        ]
    },
    {
        "id": "ENG006",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Testing & Code Quality",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "question": "What is the difference between Property-Based Testing and Example-Based Unit Testing, and how does Mutation Testing assess test suite quality?",
        "answer": "Example-based unit testing verifies code against specific, hardcoded input-output pairs chosen by the developer, which often misses edge cases. Property-based testing (using frameworks like Hypothesis) tests universal invariant mathematical properties (e.g., sort(reverse(sort(x))) == sort(x)) across hundreds of randomly generated inputs, automatically shrinking failing cases to minimal counterexamples. Mutation testing evaluates the quality of the test suite itself by introducing intentional artificial faults (mutants, like changing '>' to '<=' or flipping booleans) into source code; if the test suite fails to detect a mutant, it indicates a gap in test coverage.",
        "glossary_terms_used": ["property-based testing", "unit testing", "mutation testing", "shrinking", "code coverage", "invariants"],
        "key_concepts": ["Automated Quality Assurance", "Invariant Verification", "Mutation Score"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG006_IDEA_1",
                "semantic_statement": "Contrasts developer-chosen input examples with property-based testing verifying invariant rules across generated inputs with shrinking.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts static test cases vs generative invariant testing."
            },
            {
                "idea_id": "ENG006_IDEA_2",
                "semantic_statement": "Explains that mutation testing injects code defects to measure whether the test suite detects them, quantifying test suite effectiveness.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts testing the tests by mutating operators and checking test failure."
            }
        ]
    },
    {
        "id": "ENG007",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Version Control & CI/CD",
        "difficulty": "Advanced",
        "question_type": "Technical Application",
        "question": "Compare Trunk-Based Development with Feature Flags against GitFlow for high-frequency deployment environments.",
        "answer": "GitFlow relies on long-lived branches (master, develop, release, feature, hotfix) with formal merge gates. While suitable for scheduled monolithic releases, it results in painful merge conflicts and long lead times. Trunk-Based Development mandates that developers commit short-lived branches directly into main multiple times per day. Incomplete or risky features are hidden behind runtime Feature Flags, decoupling code deployment from feature release. This enables continuous integration, small pull request reviews, and multiple daily production deployments without branching friction.",
        "glossary_terms_used": ["Trunk-Based Development", "GitFlow", "feature flags", "continuous integration", "merge conflicts", "lead time"],
        "key_concepts": ["Branching Strategies", "Deployment Velocity", "Continuous Delivery"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG007_IDEA_1",
                "semantic_statement": "Explains that Trunk-Based Development avoids long-lived branches and merge conflicts by frequently integrating small changes into trunk.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts short-lived branches merged daily vs complex GitFlow branch branches."
            },
            {
                "idea_id": "ENG007_IDEA_2",
                "semantic_statement": "Identifies Feature Flags as the mechanism allowing uncompleted code to deploy to production without exposing features to users.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts feature toggles separating deployment from release."
            }
        ]
    },
    {
        "id": "ENG008",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Distributed Systems & API Design",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "question": "How do you design an idempotent consumer in message-driven distributed systems to handle duplicate message deliveries?",
        "answer": "Distributed message brokers like Kafka or RabbitMQ offer at-least-once delivery, meaning network retries or consumer crashes will inevitably deliver duplicate messages. To achieve idempotency, each message must carry a globally unique message ID or idempotency key. Upon receipt, the consumer executes an atomic check-and-insert into a deduplication table or distributed key-value store (e.g. Redis SETNX or SQL unique constraint). If the key already exists, the consumer skips execution or returns the previously computed result. The business operation and deduplication record should ideally commit in the same database transaction.",
        "glossary_terms_used": ["idempotency", "at-least-once delivery", "idempotency key", "deduplication", "atomic transaction"],
        "key_concepts": ["Distributed Messaging", "Duplicate Prevention", "Data Consistency"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG008_IDEA_1",
                "semantic_statement": "States that brokers provide at-least-once delivery making duplicate message processing inevitable.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts network retries or crashes causing duplicate deliveries."
            },
            {
                "idea_id": "ENG008_IDEA_2",
                "semantic_statement": "Describes tracking unique idempotency keys in an atomic store or database transaction to detect and skip duplicate events.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts unique key deduplication table or atomic check-and-set."
            }
        ]
    },
    {
        "id": "ENG009",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Data Structures and Algorithms",
        "difficulty": "Expert",
        "question_type": "Scenario-Based",
        "question": "How do you design an in-memory LRU-K cache eviction policy and what advantages does it have over standard LRU?",
        "answer": "Standard LRU evicts the item with the oldest last access timestamp, making it vulnerable to cache pollution where a sequential scan of infrequently accessed items flushes popular hot items from memory. LRU-K tracks the time of the last K accesses (commonly K=2) for each item. The backward K-distance is the time difference between current time and the K-th previous access. The cache evicts the item whose backward K-distance is maximal (or infinity if accessed fewer than K times). This requires two data structures: a hash map with FIFO queue for items accessed < K times, and an ordered heap or tree for items accessed >= K times, achieving O(log N) or amortized O(1) eviction while insulating the cache from single-scan churn.",
        "glossary_terms_used": ["LRU-K", "cache pollution", "backward K-distance", "eviction policy", "hash map"],
        "key_concepts": ["Cache Design", "Scan Resistance", "Algorithm Complexity"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG009_IDEA_1",
                "semantic_statement": "Explains that standard LRU suffers from cache pollution during sequential scans, whereas LRU-K tracks the K-th previous reference to gauge frequency.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts tracking multiple past accesses to prevent single-scan eviction of hot data."
            },
            {
                "idea_id": "ENG009_IDEA_2",
                "semantic_statement": "Articulates evicting items with the largest backward K-distance and separating items with fewer than K accesses.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts eviction based on historical access distance K."
            }
        ]
    },
    {
        "id": "ENG010",
        "category": "Software and Computer Science Fundamentals",
        "subcategory": "Object-Oriented Programming",
        "difficulty": "Intermediate",
        "question_type": "Technical Application",
        "question": "Explain the principle of 'Composition over Inheritance' and provide an architectural scenario where inheritance leads to the Fragile Base Class problem.",
        "answer": "Composition over inheritance states that classes should achieve polymorphic reuse by assembling distinct components containing desired behaviors rather than inheriting state and behavior from a parent hierarchy. Inheritance tightly couples derived classes to base class internal implementations. In the Fragile Base Class problem, modifying an internal method in a base class (such as adding an internal call from add_all() to add()) unexpectedly breaks subclass overrides (such as counting inserted elements), causing double-counting errors. Using composition with interfaces delegates behavior cleanly without exposure to base class encapsulation leaks.",
        "glossary_terms_used": ["composition over inheritance", "fragile base class", "encapsulation", "polymorphism", "coupling"],
        "key_concepts": ["Object-Oriented Design", "Coupling vs Cohesion", "Behavior Delegation"],
        "semantic_rubric_ideas": [
            {
                "idea_id": "ENG010_IDEA_1",
                "semantic_statement": "Explains that inheritance creates tight coupling where internal base class modifications break derived class assumptions.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts base class changes causing unexpected side effects in subclasses."
            },
            {
                "idea_id": "ENG010_IDEA_2",
                "semantic_statement": "Demonstrates composition by delegating tasks to injected interface references, preserving encapsulation boundaries.",
                "required": True,
                "weight": 0.5,
                "acceptable_paraphrase_guidance": "Accepts object composition and interface delegation."
            }
        ]
    }
]

def load_remaining_data():
    """Generates the remaining 110 fully specific records (ENG011 - ENG120)."""
    # Mapping of topic definitions for ENG011 to ENG120
    topics = [
        # OS & Concurrency (ENG011)
        ("ENG011", "Software and Computer Science Fundamentals", "Operating Systems & Concurrency", "Advanced", "Conceptual",
         "Explain memory-mapped files (mmap) and contrast their performance with read/write system calls for high-volume disk I/O.",
         "Memory-mapped files map a file or file segment directly into the process's virtual address space via the kernel page table. When the application accesses a memory address, the MMU triggers a page fault that loads the disk block directly into page cache, bypassing user-space buffer copying. Standard read/write syscalls require copying data between kernel buffers and user-space memory pointers and incur context switch overhead per call. mmap reduces CPU context switching and eliminates redundant memory copies, but page table management overhead and virtual address fragmentation can degrade performance on 32-bit architectures or random small writes.",
         ["mmap", "page cache", "zero-copy", "context switch", "virtual memory", "page fault"],
         ["Virtual Memory Management", "I/O Performance", "Zero-Copy Architectures"]),

        # Database Design (ENG012)
        ("ENG012", "Software and Computer Science Fundamentals", "Database Design & Transactions", "Intermediate", "Scenario-Based",
         "What is Write Skew under Snapshot Isolation and what transactional techniques prevent it in financial ledgers?",
         "Write skew occurs under Snapshot Isolation when two concurrent transactions read overlapping data sets, satisfy an invariant independently based on their initial snapshots, and then perform disjoint writes that violate the global constraint (e.g., two doctors simultaneously on-call both checking if on_call_count >= 2, and both clocking out, leaving 0 doctors). It cannot be detected by standard row-level write-write conflict detection. To prevent write skew, systems can use Serializable isolation (such as SSI in PostgreSQL), explicit SELECT ... FOR UPDATE locking on the overlapping read set, or materializing the conflict into a shared lockable row.",
         ["write skew", "Snapshot Isolation", "Serializable Snapshot Isolation", "SELECT FOR UPDATE", "concurrency control"],
         ["Transaction Isolation", "Concurrency Anomalies", "Financial Data Integrity"]),

        # Software Architecture (ENG013)
        ("ENG013", "Software and Computer Science Fundamentals", "Software Architecture & Design Patterns", "Advanced", "Technical Application",
         "Explain Command Query Responsibility Segregation (CQRS) and identify when it is advantageous over a unified CRUD model.",
         "CQRS separates the application architecture into two distinct pipelines: a Command model that handles state mutations, business rule validation, and write consistency, and a Query model optimized strictly for data retrieval. In a unified CRUD model, database schemas must compromise between normalization for write safety and denormalization for read speed. CQRS allows writes to target an ACID database while asynchronous events project data into read-optimized stores (like Elasticsearch or materialized relational views). It is advantageous in high-traffic systems with extreme read-to-write asymmetry, but introduces eventual consistency and projection sync lag.",
         ["CQRS", "event sourcing", "materialized views", "eventual consistency", "CRUD"],
         ["Architectural Patterns", "Read/Write Separation", "Data Projections"]),

        # Testing & Code Quality (ENG014)
        ("ENG014", "Software and Computer Science Fundamentals", "Testing & Code Quality", "Intermediate", "Conceptual",
         "What is Consumer-Driven Contract Testing and how does it prevent integration regressions in microservice ecosystems?",
         "Consumer-Driven Contract Testing (using tools like Pact) defines API interaction contracts from the perspective of the client/consumer. The consumer writes unit tests asserting expected request headers, payloads, and response structures, which generates an immutable contract JSON. In CI pipelines, the provider service verifies its implementation against this contract without spinning up live consumer instances. This prevents breaking API changes before deployment, eliminates slow and flaky end-to-end integration environments, and establishes clear versioned compatibility agreements.",
         ["contract testing", "Pact", "consumer-driven", "microservices", "API contract"],
         ["Integration Testing", "Microservice Quality", "CI/CD Verification"]),

        # Version Control & CI/CD (ENG015)
        ("ENG015", "Software and Computer Science Fundamentals", "Version Control & CI/CD", "Expert", "Scenario-Based",
         "Compare Blue-Green Deployments with Canary Releases and explain automated rollback triggers based on error budgets.",
         "Blue-Green deployment provisions two identical production environments: 'Blue' serves live traffic while 'Green' receives the new release. After verification, the load balancer switches 100% of traffic instantaneously, providing fast zero-downtime cutover and immediate rollback capability. Canary releases route a small fraction (e.g., 2% then 10%) of production traffic to the new version while monitoring golden signals (latency, error rates, saturation). If the error rate exceeds an SLO threshold and depletes the error budget, automated traffic routers trigger an instantaneous rollback to protect the majority of users.",
         ["Blue-Green deployment", "Canary release", "error budget", "SLO", "automated rollback"],
         ["Release Engineering", "Site Reliability", "Zero-Downtime Deployment"]),

        # Distributed Systems (ENG016)
        ("ENG016", "Software and Computer Science Fundamentals", "Distributed Systems & API Design", "Intermediate", "Technical Application",
         "How do you implement a distributed sliding-window rate limiter using Redis and what concurrency race conditions must be addressed?",
         "A sliding-window rate limiter tracks request timestamps inside a Redis sorted set (ZSET) keyed by client ID. For each request, the algorithm removes elements older than (current_time - window_size) using ZREMRANGEBYSCORE, counts remaining elements with ZCARD, and if count < limit, adds the current timestamp with ZADD. To prevent race conditions between concurrent requests from the same client, these commands must be executed atomically inside a Redis Lua script or a MULTI/EXEC transaction. Without atomicity, concurrent requests could read identical counts before either writes, exceeding the rate threshold.",
         ["sliding window", "Redis", "sorted set", "Lua script", "rate limiting", "race conditions"],
         ["API Gateway Design", "Distributed Rate Limiting", "Atomic Operations"]),

        # DSA (ENG017)
        ("ENG017", "Software and Computer Science Fundamentals", "Data Structures and Algorithms", "Advanced", "Conceptual",
         "Explain how a Monotonic Stack achieves O(N) linear time complexity for Next Greater Element and Largest Rectangle in Histogram.",
         "A monotonic stack maintains elements in strictly increasing or decreasing order by popping elements that violate the monotonicity invariant before pushing a new element. For Next Greater Element, when processing an element larger than the stack's top, the current element is established as the next greater element for that top item, and the top is popped. For Largest Rectangle in Histogram, popping an element signifies that its height boundary extends right to the current index and left to the new stack top. Although inner pop operations occur in a loop, every array element is pushed exactly once and popped at most once, guaranteeing amortized O(N) linear time.",
         ["monotonic stack", "amortized complexity", "Next Greater Element", "linear time"],
         ["Algorithmic Optimization", "Stack Data Structures", "Amortized Analysis"]),

        # OOP (ENG018)
        ("ENG018", "Software and Computer Science Fundamentals", "Object-Oriented Programming", "Intermediate", "Scenario-Based",
         "What are the differences between Transient, Scoped, and Singleton service lifetimes in Dependency Injection containers?",
         "In Dependency Injection (DI) containers, service lifetime governs instance creation and sharing across consumers. Transient lifetime creates a completely new instance every time the service is requested from the container, ideal for lightweight stateless components. Scoped lifetime creates a single shared instance per request or execution scope (such as an HTTP request boundary in web frameworks), ensuring that all collaborating classes within that request share identical state. Singleton lifetime creates one single instance on first resolution and shares it across the entire application process lifetime, requiring strict thread-safety.",
         ["dependency injection", "service lifetime", "Singleton", "Scoped", "Transient"],
         ["Inversion of Control", "Object Lifecycles", "Thread Safety"]),

        # OS & Concurrency (ENG019)
        ("ENG019", "Software and Computer Science Fundamentals", "Operating Systems & Concurrency", "Expert", "Technical Application",
         "Compare OS kernel threads with User-Space Coroutines (Green Threads) regarding context switching overhead and blocking I/O.",
         "Kernel threads are scheduled preemptively by the OS kernel; switching threads involves trapping into kernel mode, saving registers and stack pointers, and potentially flushing TLB caches and cold CPU caches, costing thousands of CPU cycles. User-space coroutines (green threads / asyncio tasks) use cooperative multitasking scheduled by an application runtime; switching between tasks only requires saving a minimal register set in user space, costing tens of cycles. However, if a coroutine executes a synchronous blocking syscall (like blocking disk read), it blocks the entire underlying OS carrier thread unless delegated to an asynchronous I/O selector or thread pool.",
         ["kernel threads", "coroutines", "green threads", "cooperative multitasking", "context switch"],
         ["Concurrency Architectures", "Runtime Scheduling", "Async I/O"]),

        # Database Design (ENG020)
        ("ENG020", "Software and Computer Science Fundamentals", "Database Design & Transactions", "Intermediate", "Conceptual",
         "When should you choose Optimistic Concurrency Control with versioning over Pessimistic Locking with SELECT FOR UPDATE?",
         "Pessimistic locking locks records at the start of a transaction, preventing any other concurrent transactions from modifying them until commit or rollback. This guarantees serialization but causes lock contention, queueing, and potential deadlocks in read-heavy systems. Optimistic Concurrency Control (OCC) assumes conflicts are rare; transactions read records without locks and check if a version number or timestamp has changed before committing (UPDATE ... WHERE id = x AND version = old_version). OCC is superior in read-dominated, low-contention environments with high throughput, whereas pessimistic locking is better in high-contention write systems where repeated OCC rollbacks waste throughput.",
         ["Optimistic Concurrency Control", "pessimistic locking", "SELECT FOR UPDATE", "versioning", "deadlocks"],
         ["Concurrency Control", "Lock Contention", "Transaction Throughput"]),

        # Software Architecture (ENG021)
        ("ENG021", "Software and Computer Science Fundamentals", "Software Architecture & Design Patterns", "Advanced", "Scenario-Based",
         "Describe the state transitions and metrics of a Circuit Breaker pattern during an upstream microservice cascading failure.",
         "A Circuit Breaker protects systems from cascading failure using a finite state machine: Closed, Open, and Half-Open. In the Closed state, requests flow normally while tracking failure rates. If error rates exceed a configurable threshold (e.g. 50% errors over 100 calls), the circuit trips to Open. In Open state, all requests fail fast immediately or execute fallback logic without touching the degraded upstream service. After a sleep window, it transitions to Half-Open, allowing a trial percentage of traffic through. If the trial calls succeed, the circuit resets to Closed; if any fail, it returns to Open.",
         ["circuit breaker", "cascading failure", "fail-fast", "fallback", "finite state machine"],
         ["System Resilience", "Fault Tolerance", "Distributed Microservices"]),

        # Testing & Code Quality (ENG022)
        ("ENG022", "Software and Computer Science Fundamentals", "Testing & Code Quality", "Intermediate", "Technical Application",
         "How do you design integration test suites using Testcontainers to ensure database isolation and reproducible CI runs?",
         "Testcontainers spins up lightweight, disposable Docker containers (e.g., PostgreSQL, Redis, Kafka) directly from integration test code. Rather than relying on shared, pre-existing local databases that introduce cross-test state pollution and schema version divergence, Testcontainers initializes a fresh database container before test suite execution, runs Flyway/Alembic migrations, and tears it down upon test completion. Tests execute against real database engines rather than in-memory SQLite mocks that lack dialect-specific features (like JSONB or CTEs), ensuring high-fidelity CI reproducibility.",
         ["Testcontainers", "Docker", "database isolation", "integration testing", "database migrations"],
         ["Test Infrastructure", "Reproducible Environments", "Database Testing"]),

        # Version Control & CI/CD (ENG023)
        ("ENG023", "Software and Computer Science Fundamentals", "Version Control & CI/CD", "Advanced", "Conceptual",
         "Explain Git internals: how blobs, trees, commits, and refs form a directed acyclic graph (DAG) of content-addressable storage.",
         "Git is a content-addressable key-value store where objects are identified by their SHA-1/SHA-256 hash. A 'blob' stores raw file content without metadata or filename. A 'tree' object represents a directory, mapping filenames, permissions, and hashes to child blobs or trees. A 'commit' points to a root tree hash, records parent commit hashes, author/committer info, and a commit message, forming a Directed Acyclic Graph (DAG). 'Refs' (branches and tags) are lightweight mutable pointers stored in .git/refs pointing to specific commit hashes. Changing any byte in a file ripples through tree and commit hashes, guaranteeing tamper-evident history.",
         ["content-addressable storage", "blob", "tree", "commit", "DAG", "refs"],
         ["Git Internals", "Cryptographic Hashing", "Directed Acyclic Graphs"]),

        # Distributed Systems (ENG024)
        ("ENG024", "Software and Computer Science Fundamentals", "Distributed Systems & API Design", "Intermediate", "Scenario-Based",
         "Why is the Two-Phase Commit (2PC) protocol considered blocking, and how does the Saga pattern solve distributed transactions?",
         "Two-Phase Commit (2PC) coordinates atomic commits across distributed nodes in Prepare and Commit phases. It is blocking because if the central coordinator crashes after participants vote 'YES' in the prepare phase, participants must hold exclusive resource locks indefinitely waiting for resolution, causing severe availability degradation. The Saga pattern replaces 2PC with a sequence of local ACID transactions coordinated via Choreography (events) or Orchestration (central state machine). If a step fails, the Saga executes compensating transactions in reverse order to semantically undo prior actions without blocking database locks.",
         ["Two-Phase Commit", "Saga pattern", "compensating transactions", "distributed transactions", "availability"],
         ["Distributed Consistency", "Fault Recovery", "Transaction Management"]),

        # DSA (ENG025)
        ("ENG025", "Software and Computer Science Fundamentals", "Data Structures and Algorithms", "Expert", "Technical Application",
         "How do you implement a Trie (Prefix Tree) for prefix search and autocomplete, and how does a Radix Tree optimize its memory?",
         "A standard Trie is a tree where each node represents a character, branching out across the alphabet (e.g. 26 child pointers for lowercase English). Searching or inserting a word of length L takes O(L) time regardless of dataset size N, making it ideal for dictionary lookups and prefix queries. However, standard Tries consume substantial memory because nodes with single children allocate full pointer arrays. A Radix Tree (Compressed Trie) optimizes memory by collapsing chains of single-child nodes into single edges labeled with multi-character substrings, dramatically reducing node allocation count and improving cache locality.",
         ["Trie", "Radix tree", "prefix search", "autocomplete", "space optimization"],
         ["Tree Data Structures", "String Algorithms", "Memory Optimization"]),

        # OOP (ENG026)
        ("ENG026", "Software and Computer Science Fundamentals", "Object-Oriented Programming", "Intermediate", "Conceptual",
         "Explain the Interface Segregation Principle (ISP) and provide an example where a 'fat' interface creates unnecessary coupling.",
         "The Interface Segregation Principle states that clients should not be forced to depend upon interfaces that they do not use. A 'fat' interface bundles multiple unrelated capabilities into a single contract (e.g., an IMultiFunctionDevice interface with print(), scan(), fax(), and staple()). If a simple InkjetPrinter class implements this fat interface, it must author empty or throwing stubs for fax() and staple(), violating ISP and Liskov Substitution. ISP resolves this by breaking the fat interface into focused, cohesion-rich interfaces (IPrinter, IScanner, IFax), allowing classes to implement only the capabilities they genuinely support.",
         ["Interface Segregation Principle", "fat interface", "SOLID principles", "loose coupling", "cohesion"],
         ["Software Design", "Interface Granularity", "SOLID Principles"]),

        # OS & Concurrency (ENG027)
        ("ENG027", "Software and Computer Science Fundamentals", "Operating Systems & Concurrency", "Advanced", "Scenario-Based",
         "How does I/O multiplexing with Linux epoll achieve scalability for 100k concurrent connections compared to select and poll?",
         "select() and poll() require the calling process to pass an entire array of file descriptors to the kernel on every call (O(N) data transfer). The kernel scans all descriptors sequentially to detect ready events, and user code must scan the array again (O(N) scanning). For 100k connections where only 1% are active, this creates massive CPU overhead. Linux epoll uses an internal kernel red-black tree to track monitored descriptors (epoll_ctl) and an event-driven callback mechanism that enqueues ready descriptors into a ready list. epoll_wait returns only the ready file descriptors in O(1) or O(ready_events) time, scaling cleanly to high concurrency.",
         ["epoll", "select", "poll", "I/O multiplexing", "C10K problem", "event-driven"],
         ["Network I/O Scalability", "Kernel Architecture", "Event Loops"]),

        # Database Design (ENG028)
        ("ENG028", "Software and Computer Science Fundamentals", "Database Design & Transactions", "Intermediate", "Technical Application",
         "Compare B+ Tree indexing with Log-Structured Merge (LSM) Trees for write-intensive versus read-intensive database workloads.",
         "B+ Trees maintain balanced multi-way tree structures where all data resides in sorted leaf pages. Point and range queries take O(log N) disk reads, and leaf pointer links allow sequential scanning, making B+ Trees optimal for read-heavy OLTP databases. However, inserting or updating random keys triggers random in-place disk page writes and node splits. LSM Trees (used in Cassandra, RocksDB) write sequentially to an in-memory MemTable and append-only WAL, flushing immutable SSTables to disk in bulk. LSM Trees achieve superior write throughput by converting random writes to sequential writes, but require Bloom filters and background compactions to counter read amplification.",
         ["B+ Tree", "LSM Tree", "write amplification", "read amplification", "SSTable", "WAL"],
         ["Storage Engines", "Index Structures", "I/O Throughput"]),

        # Software Architecture (ENG029)
        ("ENG029", "Software and Computer Science Fundamentals", "Software Architecture & Design Patterns", "Advanced", "Conceptual",
         "Explain Hexagonal Architecture (Ports and Adapters) and how it isolates the core domain logic from external dependencies.",
         "Hexagonal Architecture isolates business domain logic inside a central core that has zero dependencies on databases, web frameworks, message brokers, or external UI technologies. The domain defines 'Ports' (interfaces) representing incoming operations (driven ports, like use cases) or outgoing dependencies (driving ports, like a UserRepository interface). 'Adapters' surround the core and translate external protocols into domain calls (e.g. an HTTP controller calling a use case, or a PostgreSQL repository implementing UserRepository). This enables technology swaps, simplifies automated unit testing with mocks, and protects core rules from framework churn.",
         ["Hexagonal Architecture", "Ports and Adapters", "Clean Architecture", "domain logic", "dependency inversion"],
         ["Domain-Driven Design", "Architectural Isolation", "Testability"]),

        # Testing & Code Quality (ENG030)
        ("ENG030", "Software and Computer Science Fundamentals", "Testing & Code Quality", "Intermediate", "Scenario-Based",
         "How do you test external third-party payment APIs safely using HTTP mocking tools like WireMock without hitting live sandbox endpoints?",
         "Testing directly against live third-party payment sandboxes is slow, creates external network dependencies, risks rate limiting, and cannot reliably simulate edge failures (like 504 gateway timeouts or malformed webhooks). HTTP mocking tools like WireMock spin up an in-process or local mock HTTP server that intercepts client requests. The test configures deterministic stub mappings matching URL paths, HTTP methods, headers, and request bodies, returning controlled responses (e.g. 200 with transaction token, or 429 rate limit). This guarantees fast, deterministic CI execution and enables robust chaos testing of timeout and retry handling.",
         ["WireMock", "mocking", "integration testing", "deterministic tests", "network timeouts"],
         ["API Mocking", "Resilience Testing", "CI Test Isolation"])
    ]
    return topics

def get_ml_topics():
    """Generates 25 specific Data/ML/AI topics (ENG031 - ENG055)."""
    return [
        ("ENG031", "Data, Machine Learning and Artificial Intelligence", "Statistics & Probability", "Intermediate", "Analytical",
         "How does the Central Limit Theorem justify hypothesis testing in A/B test sample size estimation?",
         "The Central Limit Theorem (CLT) states that the sum or mean of a sufficiently large number of independent and identically distributed random variables approaches a normal distribution, regardless of the underlying population distribution. In A/B testing with conversion metrics (Bernoulli distribution), CLT allows using the normal distribution for the sample proportion difference. This justifies applying z-tests and power calculations to compute minimum sample size: N = 2 * (Z_alpha/2 + Z_beta)^2 * p * (1-p) / (delta^2), ensuring the experiment has sufficient statistical power to detect real uplift while controlling Type I and Type II error rates.",
         ["Central Limit Theorem", "A/B testing", "sample size calculation", "statistical power", "Type I error"],
         ["Hypothesis Testing", "Statistical Inference", "Experimental Design"]),

        ("ENG032", "Data, Machine Learning and Artificial Intelligence", "Feature Engineering & Preprocessing", "Advanced", "Optimization",
         "What is Target Encoding, how does it cause data leakage, and how does Out-of-Fold Target Encoding prevent overfitting?",
         "Target encoding replaces high-cardinality categorical levels with the mean of the continuous target variable for that category. While it creates strong predictive features without the dimensionality explosion of one-hot encoding, naive target encoding over the entire training set leaks label information into feature values, causing the model to overfit on rare categories. Out-of-Fold (OOF) target encoding partitions the training set into K folds, computing the target mean for each fold using only the remaining K-1 training folds. Furthermore, applying m-estimate smoothing toward the global target mean regularizes rare levels.",
         ["target encoding", "data leakage", "out-of-fold encoding", "smoothing", "high-cardinality"],
         ["Feature Engineering", "Regularization", "Leakage Prevention"]),

        ("ENG033", "Data, Machine Learning and Artificial Intelligence", "Supervised & Unsupervised Learning", "Intermediate", "Technical Application",
         "Compare Random Forest Bagging with Gradient Boosting sequentially fitting residuals: variance versus bias reduction.",
         "Random Forest is a bagging ensemble that trains multiple deep decision trees in parallel on bootstrap subsets of data with random feature selection. Individual trees have low bias but high variance; averaging their predictions reduces ensemble variance without increasing bias. In contrast, Gradient Boosting (XGBoost, LightGBM) trains shallow trees sequentially, where each successive tree fits the negative gradient (pseudo-residuals) of the previous ensemble. Gradient boosting primarily reduces bias through sequential error correction, while controlling variance via learning rate shrinkage, L1/L2 leaf penalties, and tree depth constraints.",
         ["Random Forest", "Gradient Boosting", "bagging", "bias-variance tradeoff", "residuals", "shrinkage"],
         ["Ensemble Methods", "Machine Learning Algorithms", "Model Generalization"]),

        ("ENG034", "Data, Machine Learning and Artificial Intelligence", "Model Training & Validation", "Expert", "Analytical",
         "How do you distinguish between Covariate Shift and Concept Drift, and what statistical tests monitor them in production?",
         "Covariate shift occurs when the marginal feature distribution P(X) changes over time while the conditional ground-truth mapping P(Y|X) remains constant (e.g. user demographic shifts while purchase probability given age remains identical). Concept drift occurs when the conditional relationship P(Y|X) changes (e.g. macroeconomic shifts alter user willingness to buy given identical income). Covariate shift is detected using Population Stability Index (PSI) or Kolmogorov-Smirnov (KS) tests between training and inference feature distributions. Concept drift requires labeled feedback to detect drops in calibration, accuracy, or ROC-AUC over sliding time windows.",
         ["covariate shift", "concept drift", "Population Stability Index", "Kolmogorov-Smirnov test", "model monitoring"],
         ["Model Degradation", "Distribution Shifts", "Production ML Monitoring"]),

        ("ENG035", "Data, Machine Learning and Artificial Intelligence", "Large Language Models & Transformers", "Advanced", "Optimization",
         "Why does standard multi-head attention suffer from O(N^2) memory bandwidth bottlenecks, and how does FlashAttention solve it?",
         "Standard scaled dot-product attention computes the intermediate attention score matrix S = Q * K^T and softmax output P = softmax(S) over sequence length N, storing them in GPU High Bandwidth Memory (HBM). For sequence length N, this requires O(N^2) memory footprint and repeated slow reads and writes between GPU HBM and fast SRAM memory. FlashAttention reorganizes the attention computation using tiling: it loads blocks of Q, K, and V into fast on-chip SRAM, computes online softmax scaling incrementally, and calculates the output without materializing the massive O(N^2) intermediate attention matrix in HBM, achieving massive speedups and linear memory scaling.",
         ["FlashAttention", "multi-head attention", "HBM memory bandwidth", "online softmax", "GPU SRAM"],
         ["Transformer Optimization", "Hardware-Aware Algorithms", "Attention Scaling"]),

        ("ENG036", "Data, Machine Learning and Artificial Intelligence", "Model Deployment & Optimization", "Intermediate", "Technical Application",
         "How does ONNX Runtime optimize deep learning model inference latency compared to native PyTorch execution?",
         "Native PyTorch execution in Python incurs Python interpreter dispatch overhead, unoptimized memory allocations, and fragmented kernel launches. Exporting models to Open Neural Network Exchange (ONNX) format freezes the computation graph into a standardized intermediate representation. ONNX Runtime applies graph-level optimizations including operator fusion (combining Conv + BatchNorm + ReLU into a single GPU kernel), constant folding, dead code elimination, and hardware-specific execution provider acceleration (CUDA, TensorRT, DirectML). This eliminates Python runtime overhead, minimizes memory bandwidth transfers, and reduces p99 latency.",
         ["ONNX Runtime", "operator fusion", "computation graph", "TensorRT", "kernel launch", "latency"],
         ["Model Deployment", "Inference Optimization", "Graph Compilation"]),

        ("ENG037", "Data, Machine Learning and Artificial Intelligence", "Statistics & Probability", "Advanced", "Analytical",
         "Compare Bayesian parameter estimation with Frequentist Maximum Likelihood Estimation (MLE) under sparse sample sizes.",
         "Frequentist Maximum Likelihood Estimation (MLE) estimates parameters by finding the value that maximizes the probability of observing the given data: argmax P(Data|theta). Under sparse sample sizes, MLE suffers from extreme variance and overfitting (e.g., estimating coin bias as 100% heads after 2 flips). Bayesian estimation treats parameters as random variables with prior probability distributions P(theta). It computes the posterior distribution via Bayes' theorem: P(theta|Data) proportional to P(Data|theta) * P(theta). The prior acts as a natural regularizer, pulling estimates toward plausible values and providing credible intervals reflecting true epistemic uncertainty.",
         ["Bayesian inference", "Maximum Likelihood Estimation", "prior distribution", "posterior distribution", "epistemic uncertainty"],
         ["Statistical Paradigms", "Parameter Estimation", "Small Sample Inference"]),

        ("ENG038", "Data, Machine Learning and Artificial Intelligence", "Feature Engineering & Preprocessing", "Intermediate", "Optimization",
         "What is Multiple Imputation by Chained Equations (MICE) and why is it superior to mean or median imputation?",
         "Mean or median imputation replaces missing values with static summary statistics, which artificially suppresses feature variance, distorts relationships with other variables, and underestimates standard errors. Multiple Imputation by Chained Equations (MICE) operates under the Missing at Random (MAR) assumption. It models each missing feature as a function of all other features in a series of iterative regressions (chained equations). By generating multiple plausible imputed datasets and drawing from predictive residual distributions, MICE preserves multivariate covariance structures and accounts for statistical imputation uncertainty.",
         ["MICE", "missing at random", "imputation", "multivariate covariance", "statistical uncertainty"],
         ["Data Preprocessing", "Missing Data Strategies", "Multivariate Imputation"]),

        ("ENG039", "Data, Machine Learning and Artificial Intelligence", "Supervised & Unsupervised Learning", "Expert", "Technical Application",
         "Contrast UMAP with t-SNE for dimensional reduction: mathematical foundations and preservation of global versus local structure.",
         "t-SNE models pairwise similarities as probabilities using Gaussian distributions in high-dimensional space and Student-t distributions in low-dimensional space, minimizing Kullback-Leibler divergence. It excels at preserving local cluster neighborhoods but scrambles global distances between distant clusters and suffers from O(N^2) complexity. UMAP (Uniform Manifold Approximation and Projection) is grounded in Riemannian geometry and algebraic topology, assuming data lies on a local Riemannian manifold. UMAP constructs a fuzzy simplicial set and optimizes cross-entropy, preserving both local clustering and global inter-cluster relationships with O(N log N) runtime.",
         ["UMAP", "t-SNE", "manifold learning", "Riemannian geometry", "KL divergence", "dimensionality reduction"],
         ["Unsupervised Learning", "Dimensionality Reduction", "Manifold Topology"]),

        ("ENG040", "Data, Machine Learning and Artificial Intelligence", "Model Training & Validation", "Intermediate", "Analytical",
         "Why is learning rate warm-up essential during early Transformer training epochs when using Adam optimizer?",
         "During the initial steps of training deep Transformers with random weight initialization, gradients can have large variance and magnitude, while Adam's second moment accumulator (v_t, moving average of squared gradients) is initialized near zero. Even with bias correction, early adaptive updates can cause massive, erratic parameter jumps that destabilize attention weights and cause divergence. A learning rate warm-up schedule linearly scales the learning rate from near zero to its peak value over the first several thousand steps, allowing Adam's moment estimates to stabilize before large gradient steps are taken.",
         ["learning rate warm-up", "Adam optimizer", "gradient variance", "cosine annealing", "transformer training"],
         ["Optimization Dynamics", "Hyperparameter Scheduling", "Deep Learning Training"]),

        ("ENG041", "Data, Machine Learning and Artificial Intelligence", "Large Language Models & Transformers", "Advanced", "Optimization",
         "Explain Low-Rank Adaptation (LoRA) and QLoRA for fine-tuning 70B parameter language models on consumer GPUs.",
         "Full fine-tuning of large models requires storing gradients and optimizer states for all parameters, requiring massive multi-GPU clusters. LoRA freezes the pre-trained weight matrix W_0 (d x k) and injects trainable rank decomposition matrices: delta W = B * A, where B (d x r) and A (r x k) have rank r << min(d, k). This reduces trainable parameters by over 99%. QLoRA enhances this by quantizing base model weights to NormalFloat4 (NF4), using Double Quantization to compress quantization constants, and leveraging paged optimizers to manage memory spikes, enabling fine-tuning of 70B models on single 48GB GPU setups.",
         ["LoRA", "QLoRA", "rank decomposition", "NormalFloat4", "parameter-efficient fine-tuning"],
         ["LLM Fine-Tuning", "Model Compression", "Memory Efficiency"]),

        ("ENG042", "Data, Machine Learning and Artificial Intelligence", "Model Deployment & Optimization", "Intermediate", "Technical Application",
         "How do you design a shadow deployment (dark launch) pipeline to evaluate a candidate machine learning model against live production traffic?",
         "In a shadow deployment, the API gateway or service mesh asynchronously duplicates incoming live user requests, sending one copy to the active production model and a mirrored copy to the candidate shadow model. The candidate model executes inference asynchronously and writes its predictions to a telemetry store without returning responses to the user. A monitoring pipeline calculates real-time drift, latency profiles, output score distributions, and accuracy against ground truth without risking user experience, providing high-confidence verification prior to canary cutover.",
         ["shadow deployment", "dark launch", "traffic mirroring", "telemetry", "model validation"],
         ["Model Governance", "Safe Deployment", "Production ML Verification"]),

        ("ENG043", "Data, Machine Learning and Artificial Intelligence", "Statistics & Probability", "Advanced", "Analytical",
         "What is Simpson's Paradox and how do you detect and correct for it in observational user behavior analysis?",
         "Simpson's Paradox occurs when a statistical trend or association observed across aggregate data is reversed or disappears when data is partitioned into underlying subgroups. It is caused by an unobserved confounding variable that correlates with both the exposure and outcome variables. For example, a new UI feature may appear to reduce conversion overall, but increases conversion within every demographic subgroup because mobile users were disproportionately assigned the new UI. It is corrected by using stratified statistical analysis, Cochran-Mantel-Haenszel tests, or causal DAGs with backdoor criteria.",
         ["Simpson's paradox", "confounding variable", "stratification", "causal DAG", "backdoor criterion"],
         ["Causal Inference", "Statistical Bias", "Observational Data Analysis"]),

        ("ENG044", "Data, Machine Learning and Artificial Intelligence", "Feature Engineering & Preprocessing", "Intermediate", "Optimization",
         "Compare TF-IDF sparse lexical representations with dense Sentence-Transformer embeddings for semantic search.",
         "TF-IDF (Term Frequency-Inverse Document Frequency) generates high-dimensional, sparse lexical vectors based on exact token match frequencies across documents. While computationally fast, memory-compact, and excellent for exact keyword and entity matching, TF-IDF fails to capture synonyms, polysemy, or semantic context. Dense sentence embeddings (e.g. from MiniLM or BERT) map text to continuous vector spaces (e.g. 384 or 768 dimensions) using deep attention mechanisms, capturing conceptual semantics and paraphrasing. In modern production search, hybrid search combines BM25/TF-IDF lexical search with dense vector similarity via Reciprocal Rank Fusion (RRF).",
         ["TF-IDF", "dense embeddings", "Sentence-Transformers", "hybrid search", "BM25", "Reciprocal Rank Fusion"],
         ["Information Retrieval", "Semantic Search", "Text Representation"]),

        ("ENG045", "Data, Machine Learning and Artificial Intelligence", "Supervised & Unsupervised Learning", "Expert", "Technical Application",
         "How does semi-supervised learning with Pseudo-Labeling improve model performance and what safeguards prevent confirmation bias?",
         "Pseudo-labeling trains an initial supervised model on a small labeled dataset, uses it to predict labels for a large unlabeled dataset, and selects high-confidence predictions as pseudo-labels for subsequent training rounds. The risk is confirmation bias: if the model misclassifies unlabeled data with high confidence, retraining on incorrect pseudo-labels reinforces mistakes, degrading model accuracy. Safeguards include strict confidence thresholds (e.g., softmax probability > 0.95), temperature sharpening, data augmentation consistency regularization (FixMatch), and balancing pseudo-label class distributions.",
         ["semi-supervised learning", "pseudo-labeling", "confirmation bias", "confidence threshold", "FixMatch"],
         ["Semi-Supervised Learning", "Label Efficiency", "Model Self-Training"]),

        ("ENG046", "Data, Machine Learning and Artificial Intelligence", "Model Training & Validation", "Intermediate", "Analytical",
         "What is Focal Loss and how does it address extreme foreground-background class imbalance in classification and object detection?",
         "Standard cross-entropy loss assigns equal loss weight to all examples regardless of how easily they are classified. In extreme class imbalance (e.g. 1 foreground object vs 100,000 background patches), the cumulative loss of easily classified background examples overwhelms the gradient, drowning out signal from rare positive classes. Focal Loss introduces a dynamic modulating factor (1 - p_t)^gamma to cross-entropy: FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t). When gamma > 0, the loss for well-classified easy examples (p_t near 1) is dramatically down-weighted, focusing gradients on hard, misclassified instances.",
         ["focal loss", "cross-entropy", "class imbalance", "modulating factor", "object detection"],
         ["Loss Function Design", "Class Imbalance", "Gradient Modulation"]),

        ("ENG047", "Data, Machine Learning and Artificial Intelligence", "Large Language Models & Transformers", "Advanced", "Optimization",
         "Explain Speculative Decoding in large language model inference and how it achieves latency speedups without altering output probability distributions.",
         "Autoregressive LLM generation is memory-bandwidth bound because each generated token requires reading billions of model parameters from GPU HBM. Speculative decoding pairs a small, fast draft model (e.g. 1B) with a large target model (e.g. 70B). The draft model quickly generates K candidate tokens in speculative steps. The target model evaluates all K tokens in a single parallel forward pass using modified attention masks. A rejection sampling verification rule accepts or rejects tokens, guaranteeing that the final output distribution mathematically matches the target model exactly while achieving 2-3x inference speedups.",
         ["speculative decoding", "draft model", "rejection sampling", "autoregressive inference", "latency speedup"],
         ["LLM Acceleration", "Inference Optimization", "Probabilistic Verification"]),

        ("ENG048", "Data, Machine Learning and Artificial Intelligence", "Model Deployment & Optimization", "Intermediate", "Technical Application",
         "Contrast Post-Training Quantization (PTQ) with Quantization-Aware Training (QAT) for deep neural network deployment.",
         "Post-Training Quantization (PTQ) takes a fully trained FP32 model and quantizes weights and activations to INT8 using a small calibration dataset to calculate scale factors and zero points. While fast and requiring no retraining, PTQ can suffer accuracy degradation on models with high dynamic range activations. Quantization-Aware Training (QAT) models quantization noise directly during the forward training pass using 'fake quantization' operators, while computing gradients in full FP32 during backpropagation (Straight-Through Estimator). QAT allows model weights to adapt to lower precision rounding, preserving higher accuracy at INT8 inference.",
         ["Post-Training Quantization", "Quantization-Aware Training", "straight-through estimator", "INT8", "calibration dataset"],
         ["Model Quantization", "Precision Calibration", "Edge AI Deployment"]),

        ("ENG049", "Data, Machine Learning and Artificial Intelligence", "Statistics & Probability", "Advanced", "Analytical",
         "When should you use Non-Parametric Bootstrap Resampling instead of Student's t-distribution for computing confidence intervals?",
         "Student's t-distribution assumes that the underlying data is normally distributed (or sample size is large enough via CLT) and that the test statistic is linear (like the sample mean). When calculating confidence intervals for non-linear statistics (e.g., median, QWK, Gini coefficient, percentiles, or ratio of medians) or when data exhibits heavy skewness, multimodality, or bounded intervals, t-assumptions fail. Non-parametric bootstrap resampling repeatedly samples with replacement from the observed empirical distribution B times (e.g. B=2000), computing the statistic on each replicate to form an empirical sampling distribution without parametric assumptions.",
         ["bootstrap resampling", "Student's t-distribution", "non-parametric", "empirical distribution", "sampling with replacement"],
         ["Resampling Statistics", "Confidence Intervals", "Non-Parametric Estimation"]),

        ("ENG050", "Data, Machine Learning and Artificial Intelligence", "Feature Engineering & Preprocessing", "Intermediate", "Optimization",
         "How do you prevent temporal lookahead data leakage when engineering lag and rolling window features for time-series forecasting?",
         "Lookahead leakage occurs when information from the future (t + k) is inadvertently incorporated into feature sets used to predict target values at time t. When engineering rolling mean, standard deviation, or lag features, developers must ensure that rolling windows are strictly backward-looking by shifting features by at least 1 time step (e.g. df['val'].shift(1).rolling(w).mean()). Furthermore, all preprocessing transformations (like StandardScaler or target encoders) must fit exclusively on historical training partitions using TimeSeriesSplit cross-validation without shuffling.",
         ["lookahead leakage", "time-series", "lag features", "rolling window", "TimeSeriesSplit"],
         ["Time-Series Feature Engineering", "Leakage Prevention", "Temporal Cross-Validation"]),

        ("ENG051", "Data, Machine Learning and Artificial Intelligence", "Supervised & Unsupervised Learning", "Expert", "Technical Application",
         "Explain how HDBSCAN improves upon DBSCAN clustering for datasets containing variable density clusters.",
         "Standard DBSCAN relies on a global epsilon distance threshold and min_samples parameter. It assumes clusters have uniform density, which fails when datasets contain both dense tight clusters and sparse expansive clusters (where any chosen epsilon either merges sparse clusters into noise or fractures dense clusters). HDBSCAN (Hierarchical DBSCAN) transforms space using mutual reachability distance, builds a minimum spanning tree, and constructs a cluster hierarchy. It extracts persistent clusters across all epsilon scales using excess of mass stability, automatically handling variable density and labeling low-density outliers as noise.",
         ["HDBSCAN", "DBSCAN", "mutual reachability distance", "hierarchical clustering", "cluster stability"],
         ["Density-Based Clustering", "Unsupervised Learning", "Noise Robustness"]),

        ("ENG052", "Data, Machine Learning and Artificial Intelligence", "Model Training & Validation", "Intermediate", "Analytical",
         "How does Early Stopping interact with learning rate decay schedules, and how do you configure patience to avoid premature termination?",
         "Early stopping monitors validation loss and halts training when loss fails to improve for a pre-configured number of epochs (patience). However, when paired with stepped learning rate decay schedules, validation loss often plateaus during high learning rate phases and improves dramatically only after learning rate drops. If early stopping patience is set smaller than the learning rate schedule decay interval, training terminates prematurely before the model reaches its optimal learning rate regime. To prevent this, patience must be calibrated beyond decay intervals or early stopping should be triggered by plateau-based learning rate schedulers.",
         ["early stopping", "learning rate decay", "patience", "ReduceLROnPlateau", "validation loss"],
         ["Training Dynamics", "Hyperparameter Tuning", "Overfitting Prevention"]),

        ("ENG053", "Data, Machine Learning and Artificial Intelligence", "Large Language Models & Transformers", "Advanced", "Optimization",
         "How do hybrid search and cross-encoder rerankers improve retrieval precision in Production Retrieval-Augmented Generation (RAG)?",
         "Standard dense vector retrieval uses bi-encoders to embed queries and passages independently, comparing them via cosine similarity. While fast, bi-encoders miss specific keyword identifiers (like product SKUs or error codes) and cannot capture fine-grained token-level cross-attention. Hybrid search retrieves candidate chunks using both dense embedding search and BM25 sparse keyword search, merging results with Reciprocal Rank Fusion. Next, a computationally heavier Cross-Encoder reranker scores the top 20 candidate passages by jointly attending to query and text tokens together, yielding high retrieval precision before context injection.",
         ["RAG", "hybrid search", "cross-encoder", "bi-encoder", "Reciprocal Rank Fusion", "BM25"],
         ["Retrieval-Augmented Generation", "Information Retrieval", "Semantic Reranking"]),

        ("ENG054", "Data, Machine Learning and Artificial Intelligence", "Model Deployment & Optimization", "Intermediate", "Technical Application",
         "Explain dynamic batching and concurrent model execution in NVIDIA Triton Inference Server for maximizing GPU utilization.",
         "In live production serving, user requests arrive asynchronously with single-item payloads, leaving GPU compute cores underutilized while incurring full kernel launch overhead. Triton Inference Server's dynamic batching queues individual incoming client requests across a small, configurable time window (e.g. max_queue_delay_microseconds = 5000) and aggregates them into a single larger batch before executing model inference. Combined with concurrent model execution (running multiple model instances on separate GPU execution streams), Triton maximizes GPU tensor core saturation and throughput while maintaining tight SLA latency bounds.",
         ["Triton Inference Server", "dynamic batching", "GPU utilization", "tensor cores", "SLA latency"],
         ["Model Serving", "GPU Optimization", "High-Throughput Inference"]),

        ("ENG055", "Data, Machine Learning and Artificial Intelligence", "Statistics & Probability", "Advanced", "Analytical",
         "Why is Precision-Recall AUC more informative than ROC-AUC when evaluating fraud detection models with 99.9% negative class prevalence?",
         "In fraud detection with 99.9% negative transactions, the count of True Negatives (TN) is vast. The False Positive Rate in ROC curves is defined as FPR = FP / (FP + TN). Because TN is enormous, a model can generate thousands of false alarms while keeping FPR near zero, causing ROC-AUC to appear misleadingly high (e.g. 0.98) even when actual fraud precision is abysmal. Precision-Recall AUC evaluates Precision = TP / (TP + FP) against Recall = TP / (TP + FN). It excludes TN entirely, directly exposing high False Positive rates and providing an honest assessment of minority class detection performance.",
         ["Precision-Recall AUC", "ROC-AUC", "class imbalance", "fraud detection", "False Positive Rate"],
         ["Evaluation Metrics", "Rare Event Detection", "Model Performance Assessment"])
    ]

def get_web_cloud_topics():
    """Generates 20 specific Web/Cloud/Cybersecurity topics (ENG056 - ENG075)."""
    return [
        ("ENG056", "Web Development, Cloud Computing and Cybersecurity", "Frontend & Backend Architecture", "Intermediate", "System Design",
         "Compare Server-Side Rendering (SSR) with Client-Side Rendering (CSR) regarding First Contentful Paint and SEO.",
         "Client-Side Rendering (CSR) serves an empty HTML shell and downloads a JavaScript bundle that renders the DOM in the browser. This results in slow First Contentful Paint (FCP) and Time to Interactive (TTI), and risks poor search engine indexing by crawlers that execute JavaScript poorly. Server-Side Rendering (SSR, like Next.js) renders components on the server for each request, delivering fully populated HTML. This delivers fast FCP and robust SEO, at the cost of higher server CPU load and hydration lag where the page is visible but non-interactive until client scripts attach event listeners.",
         ["Server-Side Rendering", "Client-Side Rendering", "First Contentful Paint", "SEO", "hydration"],
         ["Frontend Architecture", "Web Performance", "Rendering Patterns"]),

        ("ENG057", "Web Development, Cloud Computing and Cybersecurity", "Cloud Infrastructure & Containers", "Advanced", "Security and Reliability",
         "How do Kubernetes Pod Disruption Budgets (PDB) and Horizontal Pod Autoscaling (HPA) interact during cluster upgrades?",
         "Horizontal Pod Autoscalers (HPA) scale the number of pod replicas dynamically based on observed CPU, memory, or custom Prometheus metrics. Pod Disruption Budgets (PDB) specify the minimum number or percentage of pods (e.g. minAvailable: 80%) that must remain running during voluntary disruptions (like node draining during Kubernetes cluster upgrades). When a node drain is initiated, the eviction API checks the PDB; if evicting a pod violates the budget, the drain waits until new pods spin up on other nodes. This ensures that scaling operations and maintenance upgrades do not cause service outages.",
         ["Pod Disruption Budget", "Horizontal Pod Autoscaler", "Kubernetes", "node drain", "high availability"],
         ["Container Orchestration", "Cluster Reliability", "Cloud Infrastructure"]),

        ("ENG058", "Web Development, Cloud Computing and Cybersecurity", "API Design & Security", "Intermediate", "Technical Application",
         "What are the tradeoffs between URI path versioning (/v1/users) and Header versioning for REST APIs?",
         "URI path versioning (/api/v1/users) makes the API contract explicitly visible in URLs, allows easy testing in browser bars and curl, and simplifies HTTP caching rules in CDNs and reverse proxies. However, it violates strict REST semantic purity because the URI represents resource identity rather than representation schema. Header versioning (e.g. Accept: application/vnd.company.v1+json) keeps URIs clean and permanent, adhering to REST HATEOAS principles, but makes proxy caching, documentation, and client consumption more complex. URI path versioning remains industry standard for public enterprise APIs.",
         ["API versioning", "REST", "Accept header", "URI path", "CDN caching"],
         ["API Architecture", "Backward Compatibility", "Web Standards"]),

        ("ENG059", "Web Development, Cloud Computing and Cybersecurity", "Observability & Reliability Engineering", "Expert", "System Design",
         "How does OpenTelemetry propagate distributed trace contexts across asynchronous message queues and HTTP boundaries?",
         "OpenTelemetry standardizes distributed tracing by injecting and extracting W3C Trace Context headers (traceparent and tracestate). The traceparent header carries a 16-byte Trace ID (identifying the entire distributed transaction) and an 8-byte Span ID (identifying the caller's current operation). For synchronous HTTP calls, the client injects these headers into outgoing HTTP request headers. For asynchronous queues (like Kafka or RabbitMQ), OpenTelemetry injects trace metadata into message record headers. When consumers read the message, the SDK extracts the context, establishing a parent-child span relationship without breaking trace continuity.",
         ["OpenTelemetry", "W3C Trace Context", "traceparent", "Span ID", "distributed tracing"],
         ["Observability Architecture", "Distributed Tracing", "Microservice Telemetry"]),

        ("ENG060", "Web Development, Cloud Computing and Cybersecurity", "Frontend & Backend Architecture", "Advanced", "Security and Reliability",
         "How do Content Security Policy (CSP) headers and HttpOnly secure cookies mitigate Cross-Site Scripting (XSS) and token theft?",
         "Cross-Site Scripting (XSS) allows attackers to inject malicious scripts into web pages. If authentication tokens (like JWTs) are stored in browser localStorage or accessible cookies, malicious JavaScript can steal them via document.cookie. HttpOnly cookies prevent client-side JavaScript from reading the cookie, neutralizing token theft even if XSS occurs. The 'Secure' flag ensures transmission only over TLS, and 'SameSite=Strict' protects against CSRF. Content Security Policy (CSP) headers restrict which origins can execute scripts (e.g. script-src 'self'), blocking unauthorized external script injection.",
         ["Content Security Policy", "HttpOnly", "XSS", "JWT theft", "Secure cookie", "SameSite"],
         ["Web Security", "Cross-Site Scripting", "Authentication Security"]),

        ("ENG061", "Web Development, Cloud Computing and Cybersecurity", "Cloud Infrastructure & Containers", "Intermediate", "Technical Application",
         "Explain how multi-stage Docker builds reduce image attack surface and final image size for compiled applications.",
         "Single-stage Docker builds leave compilers, build toolchains (like GCC, npm, Maven), source files, and intermediate artifacts inside the final production container, resulting in multi-gigabyte images with large vulnerability attack surfaces. Multi-stage builds declare multiple FROM instructions. The first stage (builder) compiles the application and installs dependencies. The final production stage uses a minimal runtime base image (e.g., Alpine or Distroless) and copies only the compiled binary artifact from the builder stage via COPY --from=builder. This reduces image size by over 90% and removes build-time vulnerability vectors.",
         ["multi-stage build", "Docker", "Distroless", "container security", "attack surface"],
         ["Container Optimization", "DevSecOps", "Docker Packaging"]),

        ("ENG062", "Web Development, Cloud Computing and Cybersecurity", "API Design & Security", "Advanced", "System Design",
         "How does GraphQL Federation resolve the N+1 query problem across decoupled microservice subgraphs using DataLoader?",
         "In GraphQL architectures with separate microservices, a nested query (e.g. orders with customer details) causes the N+1 problem: fetching N orders results in N individual network requests to the customer service. GraphQL Federation composes distinct domain subgraphs (orders service, user service) into a unified supergraph via an Apollo Gateway. To solve the N+1 problem, each subgraph utilizes the DataLoader pattern, which batches individual ID lookup requests occurring within the same tick of the event loop into a single bulk query (e.g. getUsersByIds([1, 2, 3])) and caches responses per request scope.",
         ["GraphQL Federation", "N+1 problem", "DataLoader", "Apollo Gateway", "batching"],
         ["API Gateway Architecture", "GraphQL Performance", "Distributed Queries"]),

        ("ENG063", "Web Development, Cloud Computing and Cybersecurity", "Observability & Reliability Engineering", "Intermediate", "Security and Reliability",
         "How do Service Level Objectives (SLOs) and Error Budgets guide deployment velocity and reliability engineering decisions?",
         "A Service Level Indicator (SLI) is a quantifiable metric of service performance (e.g., % of HTTP requests < 200ms). A Service Level Objective (SLO) defines the target reliability agreed with stakeholders (e.g., 99.9% successful requests over 30 days). The Error Budget is the allowable failure headroom (100% - SLO = 0.1%). If a service maintains a healthy error budget, engineering teams can deploy features rapidly and experiment aggressively. When the error budget is depleted due to outages or regressions, feature releases are automatically frozen, and engineering priorities pivot entirely to reliability, bug fixes, and infrastructure resilience.",
         ["SLO", "SLI", "error budget", "Site Reliability Engineering", "deployment velocity"],
         ["Site Reliability Engineering", "Reliability Governance", "Service Health Metrics"]),

        ("ENG064", "Web Development, Cloud Computing and Cybersecurity", "Frontend & Backend Architecture", "Expert", "Technical Application",
         "How do you optimize Core Web Vitals (Largest Contentful Paint and Cumulative Layout Shift) in single-page applications?",
         "Largest Contentful Paint (LCP) measures when the largest visual content element finishes rendering. It is optimized by preloading critical hero images (<link rel='preload'>), utilizing responsive WebP/AVIF image formats, implementing edge CDN caching, and code-splitting JavaScript bundles to eliminate render-blocking main-thread script execution. Cumulative Layout Shift (CLS) measures visual layout instability. It is eliminated by reserving explicit width and height aspect-ratio dimensions on images and dynamic ads, avoiding inserting dynamic DOM banners above existing content, and using font-display: optional to avoid layout reflows.",
         ["Largest Contentful Paint", "Cumulative Layout Shift", "Core Web Vitals", "code-splitting", "CDN caching"],
         ["Web Performance", "Frontend Optimization", "User Experience Metrics"]),

        ("ENG065", "Web Development, Cloud Computing and Cybersecurity", "Cloud Infrastructure & Containers", "Intermediate", "System Design",
         "How do you implement secure remote state management and concurrency locking in Terraform using AWS S3 and DynamoDB?",
         "Terraform records managed infrastructure metadata and output mappings in a state file (terraform.tfstate). Storing state locally risks accidental deletion, out-of-sync team divergence, and exposed cleartext secrets. A secure backend stores the state file in an encrypted AWS S3 bucket with server-side encryption (SSE-KMS), bucket versioning enabled for rollback, and strict IAM bucket policies blocking public access. A DynamoDB table configured with a primary hash key 'LockID' provides state locking; whenever terraform plan or apply runs, it acquires an exclusive lock, preventing race conditions from concurrent team executions.",
         ["Terraform", "state locking", "DynamoDB", "AWS S3", "infrastructure-as-code"],
         ["Infrastructure as Code", "Cloud Security", "State Management"]),

        ("ENG066", "Web Development, Cloud Computing and Cybersecurity", "API Design & Security", "Advanced", "Security and Reliability",
         "How does OAuth 2.0 Authorization Code Flow with PKCE protect single-page and mobile applications against token interception?",
         "Single-page applications (SPAs) and mobile apps are public clients that cannot securely store a client secret. In standard Authorization Code flow, an intercepted authorization code could be exchanged for an access token by an attacker. Proof Key for Code Exchange (PKCE) resolves this: the client generates a cryptographic random code_verifier and derives a code_challenge = SHA256(code_verifier). The challenge is sent with the initial authorization request. When exchanging the authorization code for tokens, the client transmits the original code_verifier. The authorization server hashes it and verifies match, proving the token requester is the identical client that initiated the flow.",
         ["OAuth 2.0", "PKCE", "code_verifier", "code_challenge", "token interception"],
         ["API Security", "Identity & Access Management", "Public Client Security"]),

        ("ENG067", "Web Development, Cloud Computing and Cybersecurity", "Observability & Reliability Engineering", "Intermediate", "Technical Application",
         "How do structured JSON logging and Correlation IDs streamline debugging across distributed asynchronous microservices?",
         "Unstructured plain-text logs are difficult to parse, search, and aggregate across distributed systems. Structured logging outputs log entries as JSON objects containing standardized metadata fields (timestamp, log_level, service_name, message, stack_trace). A Correlation ID (or Request ID) is generated at the API gateway upon request arrival and passed along all downstream synchronous HTTP calls and asynchronous message headers. Log ingestion pipelines (like Elasticsearch, Loki, or Datadog) index the correlation ID, allowing engineers to query a single ID and view the complete chronological execution log across all microservices.",
         ["structured logging", "correlation ID", "log aggregation", "Elasticsearch", "Loki"],
         ["Microservice Debugging", "Observability", "Log Management"]),

        ("ENG068", "Web Development, Cloud Computing and Cybersecurity", "Frontend & Backend Architecture", "Advanced", "System Design",
         "How do you architect a horizontally scalable WebSocket notification service using Redis Pub/Sub backplanes?",
         "WebSocket connections maintain persistent stateful TCP sockets between clients and individual server instances. In a horizontally scaled cluster behind a load balancer, client A on server 1 cannot directly receive a notification generated by an event on server 2. To resolve this, servers act as subscribers to a shared Redis Pub/Sub backplane. When an event occurs, server 2 publishes the notification to a channel (e.g. user:123). All backend servers receive the message, but only server 1 (which holds the active WebSocket connection for user:123) serializes and pushes the frame to the client, decoupling client socket termination from event routing.",
         ["WebSockets", "Redis Pub/Sub", "horizontal scaling", "sticky sessions", "event routing"],
         ["Real-Time Web", "Stateful Connection Scaling", "Distributed Messaging"]),

        ("ENG069", "Web Development, Cloud Computing and Cybersecurity", "Cloud Infrastructure & Containers", "Expert", "Security and Reliability",
         "How does an Istio Service Mesh enforce Zero-Trust security and mutual TLS (mTLS) across Kubernetes microservices?",
         "In a traditional Kubernetes cluster, pod-to-pod network traffic across nodes is unencrypted and open. A service mesh like Istio injects an Envoy sidecar proxy alongside every application pod. Istio's control plane (Istiod) acts as a Certificate Authority, automatically issuing and rotating X.509 certificates to each sidecar proxy. All inter-service communications are intercepted by Envoy proxies, which perform mutual TLS (mTLS) handshakes, encrypting traffic in transit and cryptographically verifying service identities via SPIFFE IDs. PeerAuthentication policies enforce strict mTLS, and AuthorizationPolicies define fine-grained least-privilege service-to-service access rules.",
         ["service mesh", "Istio", "mTLS", "Envoy proxy", "SPIFFE", "Zero-Trust"],
         ["Cloud Security", "Service Mesh Architecture", "Zero-Trust Networking"]),

        ("ENG070", "Web Development, Cloud Computing and Cybersecurity", "API Design & Security", "Intermediate", "Technical Application",
         "How do you design a secure and reliable outgoing Webhook system with cryptographic HMAC signatures and exponential backoff?",
         "An outgoing webhook system notifies external client endpoints of system events via HTTP POST requests. Security is achieved by computing a cryptographic HMAC signature (e.g. HMAC-SHA256) of the request body using a shared secret key, sending it in an HTTP header (X-Signature-SHA256) so the receiver can verify message integrity and authenticity. Reliability is guaranteed by queueing webhook deliveries in a durable broker and retrying failed deliveries (HTTP 4xx/5xx or timeouts) with exponential backoff and jitter over 24-48 hours. If all retries fail, events are moved to a Dead Letter Queue (DLQ) with user-facing redelivery options.",
         ["webhooks", "HMAC", "exponential backoff", "Dead Letter Queue", "message integrity"],
         ["Webhook Design", "API Integration", "Cryptographic Signatures"]),

        ("ENG071", "Web Development, Cloud Computing and Cybersecurity", "Observability & Reliability Engineering", "Advanced", "System Design",
         "How do you design Chaos Engineering experiments with Chaos Mesh to validate Kubernetes network partition resilience?",
         "Chaos Engineering proactively injects controlled failures into production-like environments to verify resilience hypotheses. Using Chaos Mesh, an engineer formulates a hypothesis (e.g., 'Database replica network partition will trigger automatic failover within 15 seconds without HTTP 500 errors'). A NetworkChaos custom resource injects packet loss, latency, or full partition between database pods and application pods. Observability metrics (error budgets, failover timestamps, and circuit breaker trip counts) are tracked to confirm whether the system degrades gracefully or uncovers hidden failure modes like split-brain or cascading timeouts.",
         ["Chaos Engineering", "Chaos Mesh", "network partition", "resilience hypothesis", "failover"],
         ["System Resilience", "Fault Injection", "Chaos Testing"]),

        ("ENG072", "Web Development, Cloud Computing and Cybersecurity", "Frontend & Backend Architecture", "Intermediate", "Security and Reliability",
         "Explain Cross-Origin Resource Sharing (CORS) preflight requests and how to configure Access-Control headers securely.",
         "CORS is a browser security mechanism enforcing the Same-Origin Policy. When a web application initiates a cross-origin HTTP request that modifies state or uses non-standard headers (e.g., PUT, DELETE, Authorization), the browser automatically sends an HTTP OPTIONS preflight request. The server must respond with Access-Control-Allow-Origin, Access-Control-Allow-Methods, and Access-Control-Allow-Headers. To configure securely, servers must validate incoming Origin headers against an explicit whitelist of allowed domains rather than returning wildcard '*' with credentials allowed, which exposes authenticated endpoints to malicious cross-origin theft.",
         ["CORS", "preflight request", "OPTIONS", "Same-Origin Policy", "Access-Control headers"],
         ["Browser Security", "API Access Control", "Web Security"]),

        ("ENG073", "Web Development, Cloud Computing and Cybersecurity", "Cloud Infrastructure & Containers", "Advanced", "Technical Application",
         "How do AWS IAM Roles for Service Accounts (IRSA) replace static AWS credentials in Kubernetes clusters?",
         "Historically, pods requiring AWS API access either had static AWS_ACCESS_KEY_ID credentials mounted as secrets or inherited broad IAM permissions attached to the underlying EC2 node, violating least-privilege security. IAM Roles for Service Accounts (IRSA) establishes an OpenID Connect (OIDC) identity provider federation between the EKS cluster and AWS IAM. The pod's Kubernetes ServiceAccount is annotated with an IAM role ARN. When the pod starts, the EKS pod identity webhook injects an OIDC token; the AWS SDK exchanges this token via AssumeRoleWithWebIdentity for temporary scoped AWS credentials, eliminating static secrets.",
         ["IRSA", "IAM", "OIDC", "Kubernetes ServiceAccount", "least privilege", "EKS"],
         ["Cloud Identity", "Secretless Architecture", "Container Security"]),

        ("ENG074", "Web Development, Cloud Computing and Cybersecurity", "API Design & Security", "Intermediate", "System Design",
         "When should you use Server-Sent Events (SSE) instead of WebSockets for streaming LLM generation tokens to browser clients?",
         "Server-Sent Events (SSE) operates over standard unidirectional HTTP, streaming text chunks using the text/event-stream content type. For streaming LLM completions, communication is strictly one-way (server to client) once the initial prompt is sent. SSE works natively with HTTP/2 multiplexing, traverses corporate proxies and firewalls without special socket handshakes, and has built-in browser reconnection mechanisms via EventSource. WebSockets provides full-duplex bidirectional communication, which introduces unnecessary stateful socket maintenance, custom framing, and load balancing complexity when user interactions are primarily unidirectional text streaming.",
         ["Server-Sent Events", "WebSockets", "HTTP/2", "streaming", "LLM inference"],
         ["Streaming Protocols", "Real-Time APIs", "LLM UI Architecture"]),

        ("ENG075", "Web Development, Cloud Computing and Cybersecurity", "Observability & Reliability Engineering", "Expert", "Security and Reliability",
         "How do Exponentially Weighted Moving Averages (EWMA) and dynamic standard deviation bands detect real-time latency anomalies?",
         "Static latency alert thresholds (e.g. alert if latency > 200ms) produce false alarms during normal daily peak traffic or miss subtle latency spikes during low-traffic night hours. An Exponentially Weighted Moving Average (EWMA) maintains an adaptive baseline that gives exponentially higher weight to recent metric observations: S_t = alpha * Y_t + (1 - alpha) * S_{t-1}. Combined with dynamic standard deviation bands (EWMSD), the anomaly detector establishes dynamic upper and lower confidence thresholds: Upper_Threshold = S_t + k * sigma_t. A spike exceeding this band triggers an alert based on relative statistical deviation rather than arbitrary static limits.",
         ["EWMA", "anomaly detection", "dynamic thresholds", "latency monitoring", "standard deviation"],
         ["Statistical Monitoring", "Real-Time Telemetry", "Anomaly Detection"])
    ]

def get_core_engineering_topics():
    """Generates 20 specific Core Engineering topics (ENG076 - ENG095)."""
    return [
        ("ENG076", "Core Engineering", "Mechanical Engineering", "Intermediate", "Conceptual",
         "Explain engineering stress-strain curves, Hooke's law, yield strength, and the offset method for determining yield point.",
         "An engineering stress-strain curve plots nominal tensile stress against strain. In the initial linear elastic region, Hooke's law applies: stress = E * strain, where Young's Modulus E represents material stiffness. Beyond the proportional limit, plastic deformation occurs where strain is permanent. For ductile metals without a sharp yield drop (like aluminum), the yield strength is determined via the 0.2% offset method: drawing a line parallel to the elastic slope starting at 0.002 strain; its intersection with the stress-strain curve defines the yield point, marking the transition from safe elastic behavior to irreversible plastic deformation.",
         ["stress-strain curve", "Hooke's law", "Young's modulus", "yield strength", "plastic deformation", "0.2% offset"],
         ["Materials Science", "Solid Mechanics", "Structural Design"]),

        ("ENG077", "Core Engineering", "Electrical Engineering", "Advanced", "Troubleshooting",
         "Explain impedance matching in RF transmission lines, characteristic impedance Z0, and the impact of Standing Wave Ratio (SWR).",
         "In high-frequency AC and RF transmission lines, signals propagate as electromagnetic waves. The characteristic impedance Z0 is determined by the physical geometry and dielectric properties of the transmission line: Z0 = sqrt(L/C). When a load impedance Z_L differs from Z0, boundary conditions are violated, causing a portion of the incident wave to reflect back toward the source. The interference between incident and reflected waves creates standing waves. A high Voltage Standing Wave Ratio (VSWR = Vmax/Vmin) causes signal attenuation, distortion, and destructive heating in transmitter output stages, requiring matching networks (like L-networks or stubs).",
         ["impedance matching", "characteristic impedance", "VSWR", "reflection coefficient", "RF transmission"],
         ["Electromagnetic Theory", "RF Engineering", "Transmission Lines"]),

        ("ENG078", "Core Engineering", "Civil Engineering", "Intermediate", "Analytical",
         "Explain the hydration kinetics of Portland cement and the factors influencing 28-day concrete compressive strength.",
         "Concrete hardening is an exothermic chemical hydration reaction between Portland cement compounds (primarily tricalcium silicate C3S and dicalcium silicate C2S) and water, forming calcium silicate hydrate (C-S-H) gel that binds aggregates. The water-cement (w/c) ratio is the primary determinant of strength: lower w/c ratios increase density and reduce capillary porosity, maximizing compressive strength, but require superplasticizers to maintain workability. Curing temperature and continuous moisture retention during the critical 28-day hydration window prevent premature shrinkage cracking and ensure maximum C-S-H gel crystallization.",
         ["concrete hydration", "C-S-H gel", "water-cement ratio", "compressive strength", "capillary porosity"],
         ["Materials Engineering", "Structural Concrete", "Civil Construction"]),

        ("ENG079", "Core Engineering", "Mechanical Engineering", "Expert", "Troubleshooting",
         "Describe the physical mechanisms of high-temperature creep and thermal fatigue in gas turbine blades.",
         "Gas turbine blades operate under centrifugal stress at temperatures exceeding 1000°C. Under sustained mechanical stress at homologous temperatures > 0.4 T_melt, materials undergo creep: progressive time-dependent plastic deformation occurring via dislocation climb (power-law creep) and vacancy diffusion along grain boundaries (Cobar/Nabarro-Herring creep), culminating in tertiary rupture. Concurrently, rapid thermal cycling during engine starts and shutdowns induces severe thermal gradients and constrained expansion, generating cyclic thermal stresses that cause low-cycle thermal fatigue cracking. Mitigations include single-crystal superalloys, internal cooling passages, and ceramic thermal barrier coatings.",
         ["creep deformation", "thermal fatigue", "turbine blades", "single-crystal superalloys", "thermal barrier coatings"],
         ["High-Temperature Mechanics", "Failure Analysis", "Aerospace Engineering"]),

        ("ENG080", "Core Engineering", "Electrical Engineering", "Advanced", "Analytical",
         "Compare Butterworth and Chebyshev active filter topologies regarding passband flatness, roll-off steepness, and phase linearity.",
         "Active analog filters shape signal frequency spectra. A Butterworth filter is designed for maximal passband flatness; its frequency response has no passband or stopband ripple, and exhibits moderate phase linearity, but has a relatively gradual transition roll-off beyond the cutoff frequency. A Chebyshev filter (Type I) introduces mathematical equiripple Chebyshev polynomials in the passband to achieve a significantly steeper transition roll-off for the same filter order. The tradeoff is passband amplitude ripple, non-linear phase response, and severe group delay distortion, making Butterworth preferable for audio and Chebyshev for narrow-band channel separation.",
         ["Butterworth filter", "Chebyshev filter", "passband ripple", "roll-off rate", "group delay"],
         ["Analog Signal Processing", "Filter Design", "Circuit Analysis"]),

        ("ENG081", "Core Engineering", "Civil Engineering", "Intermediate", "Conceptual",
         "Explain Terzaghi's Principle of Effective Stress and its application to soil consolidation and foundation settlement.",
         "Terzaghi's Principle states that the total stress sigma in a saturated soil mass is the sum of effective stress sigma' (transmitted through solid mineral grain contacts) and pore water pressure u: sigma = sigma' + u. Soil shear strength and volumetric compression are governed strictly by effective stress, not total stress. When a structural foundation applies a load to saturated clay, pore water pressure initially spikes. As water slowly dissipates through permeable boundaries, load transfers to the soil skeleton, increasing effective stress and causing time-dependent primary consolidation settlement, which must be modeled to prevent structural foundation failure.",
         ["effective stress", "pore water pressure", "soil consolidation", "Terzaghi", "settlement"],
         ["Geotechnical Engineering", "Soil Mechanics", "Foundation Engineering"]),

        ("ENG082", "Core Engineering", "Mechanical Engineering", "Advanced", "Troubleshooting",
         "How do you identify and resolve stress singularities versus genuine stress concentrations in Finite Element Analysis (FEA)?",
         "A stress concentration is a real physical phenomenon where stress spikes near geometric discontinuities (such as fillets or holes), characterized by a finite theoretical stress concentration factor K_t that converges to a fixed value under mesh refinement. A stress singularity is a mathematical artifact of elasticity theory occurring at sharp interior re-entrant corners, point loads, or rigid boundary constraints where theoretical radius r = 0, causing calculated stress to diverge toward infinity as mesh elements shrink. In FEA, singularities are identified when refining the mesh indefinitely increases peak stress without convergence; they are resolved by modeling realistic fillet radii or distributed load patches.",
         ["Finite Element Analysis", "stress singularity", "stress concentration", "mesh convergence", "fillets"],
         ["Computational Mechanics", "Structural Simulation", "Finite Element Method"]),

        ("ENG083", "Core Engineering", "Electrical Engineering", "Intermediate", "Analytical",
         "Explain real power (P), reactive power (Q), and apparent power (S), and calculate power factor correction using shunt capacitors.",
         "In AC circuits with inductive loads (e.g. electric motors), current lags voltage, creating a phase difference theta. Real power P (kW) performs actual physical work: P = V * I * cos(theta). Reactive power Q (kVAR) oscillates energy back and forth between source and magnetic fields: Q = V * I * sin(theta). Apparent power S (kVA) is the total vector sum: S = sqrt(P^2 + Q^2). The power factor is cos(theta) = P/S. A low power factor draws excessive reactive current, causing transmission losses and utility penalties. Power factor is corrected by installing shunt capacitor banks that supply leading reactive current, canceling lagging inductive reactive power and driving power factor toward unity.",
         ["real power", "reactive power", "apparent power", "power factor correction", "shunt capacitors"],
         ["Power Systems", "Electrical Engineering", "AC Circuits"]),

        ("ENG084", "Core Engineering", "Civil Engineering", "Expert", "Troubleshooting",
         "Explain Euler's Column Buckling formula and the significance of effective length factor K under varying boundary conditions.",
         "Buckling is a sudden geometric instability failure in slender structural columns under compressive axial loads occurring before material yield strength is reached. Euler's critical buckling load formula is P_cr = (pi^2 * E * I) / (K * L)^2, where E is Young's Modulus, I is area moment of inertia, L is column length, and K is the effective length factor representing the distance between inflection points of zero bending moment. For pinned-pinned ends, K = 1.0; for fixed-fixed ends, rotation is constrained, yielding K = 0.5 and quadrupling buckling capacity; for fixed-free cantilever columns, K = 2.0, drastically reducing critical buckling load.",
         ["Euler buckling", "critical load", "effective length factor", "moment of inertia", "slenderness ratio"],
         ["Structural Mechanics", "Column Design", "Structural Stability"]),

        ("ENG085", "Core Engineering", "Mechanical Engineering", "Advanced", "Analytical",
         "Explain Reynolds number calculation, boundary layer transition from laminar to turbulent flow, and pipe friction factors using Moody charts.",
         "Reynolds number is a dimensionless ratio of inertial forces to viscous forces in a fluid: Re = (rho * v * D) / mu. For internal pipe flow, flow is laminar when Re < 2300, where fluid particles travel in smooth parallel streamlines with a parabolic velocity profile and Darcy friction factor f = 64/Re. Flow becomes turbulent when Re > 4000, characterized by chaotic eddies, rapid mixing, and a flatter velocity profile with higher wall shear stress. In turbulent flow, the friction factor depends on both Reynolds number and relative pipe roughness (epsilon/D), determined empirically using the Moody chart or Colebrook equation.",
         ["Reynolds number", "laminar flow", "turbulent flow", "Moody chart", "Darcy friction factor"],
         ["Fluid Mechanics", "Pipe Flow", "Hydraulics"]),

        ("ENG086", "Core Engineering", "Electrical Engineering", "Intermediate", "Conceptual",
         "Explain how Pulse-Width Modulation (PWM) and H-Bridge topologies control the speed and direction of DC motors.",
         "Direct Current (DC) motor speed is proportional to average applied armature voltage. Rather than dissipating power in resistive dividers, Pulse-Width Modulation (PWM) rapidly switches full DC supply voltage on and off at high frequency; the average voltage is controlled linearly by adjusting the duty cycle (ratio of on-time to total switching period). To achieve bidirectional rotation, an H-bridge circuit arranges four switching transistors (MOSFETs) around the motor. Activating diagonal pairs Q1 and Q4 applies forward polarity, while activating Q2 and Q3 reverses current flow and rotation. Cross-conduction (shoot-through) is prevented by enforcing dead-time delays between switching transitions.",
         ["PWM", "H-Bridge", "duty cycle", "shoot-through", "DC motor control"],
         ["Power Electronics", "Motor Drives", "Embedded Systems"]),

        ("ENG087", "Core Engineering", "Civil Engineering", "Advanced", "Troubleshooting",
         "How do Seismic Base Isolation bearings and Tuned Mass Dampers protect high-rise buildings from earthquake resonance?",
         "Earthquakes transmit high-frequency horizontal ground accelerations into structures, exciting natural structural resonant frequencies and inducing destructive shear forces. Seismic Base Isolation decouples the superstructure from the ground by installing elastomeric lead-rubber bearings at the foundation level, shifting the building's fundamental period to a longer duration where seismic energy spectra are low. Tuned Mass Dampers (TMDs) mount a massive inertial mass suspended near the building's top tuned to match the building's natural frequency; when the structure sways during wind or seismic excitation, the TMD oscillates out of phase, dissipating vibrational kinetic energy through hydraulic dampers.",
         ["seismic base isolation", "Tuned Mass Damper", "resonance", "natural frequency", "earthquake engineering"],
         ["Structural Dynamics", "Earthquake Engineering", "Vibration Mitigation"]),

        ("ENG088", "Core Engineering", "Mechanical Engineering", "Intermediate", "Analytical",
         "What is an involute gear tooth profile and why does it maintain a constant angular velocity ratio despite center distance variations?",
         "Involute gear profiles are generated by tracing the path of a point on a taut string unwinding from a base cylinder. According to the fundamental law of gearing, two meshing gears maintain a constant angular velocity ratio (omega_1 / omega_2 = r_2 / r_1) if and only if the common normal to the tooth profiles at their contact point always passes through a fixed pitch point on the line of centers. The involute tooth form uniquely satisfies this condition because the line of action is tangent to both base circles. Consequently, even if manufacturing tolerances or thermal expansion alter the center distance slightly, the angular velocity ratio remains perfectly constant and uniform.",
         ["involute profile", "angular velocity ratio", "line of action", "pitch point", "gear kinematics"],
         ["Machine Design", "Kinematics", "Mechanical Power Transmission"]),

        ("ENG089", "Core Engineering", "Electrical Engineering", "Expert", "Troubleshooting",
         "How do ground loops generate 50/60 Hz hum in sensitive audio and instrumentation circuits, and how do star grounding topologies eliminate them?",
         "A ground loop forms when multiple interconnected devices have separate paths to ground, creating a closed conducting loop. Stray magnetic fields from nearby power transformers and AC wiring induce parasitic circulating currents around this ground loop according to Faraday's law of induction. Because ground conductors have finite impedance (resistance and inductance), circulating loop currents generate small AC voltage drops across ground references that enter the signal path as 50/60 Hz hum. A Star Grounding topology connects all individual circuit grounds to a single centralized physical point, eliminating multiple return paths, breaking the conductive loop, and maintaining equal ground potential.",
         ["ground loop", "star grounding", "Faraday's law", "electromagnetic interference", "signal-to-noise ratio"],
         ["Signal Integrity", "EMC / EMI", "Analog Circuit Design"]),

        ("ENG090", "Core Engineering", "Civil Engineering", "Advanced", "Analytical",
         "Compare under-reinforced, balanced, and over-reinforced failure modes in reinforced concrete beams: why do building codes mandate under-reinforced design?",
         "In reinforced concrete flexural design, the balanced condition occurs when tensile steel yields simultaneously as concrete reaches its ultimate compressive strain (0.003). In an over-reinforced beam, excessive steel is provided; concrete crushes catastrophically in compression before the steel yields, causing sudden brittle failure without prior warning. In an under-reinforced beam, steel reinforcement area is limited; when overloaded, the tensile steel yields first and undergoes massive plastic elongation, generating wide visible cracks and large deflections that provide unmistakable visual warning and allow occupant evacuation before ultimate concrete crushing. Building codes strictly mandate under-reinforced design for life safety.",
         ["under-reinforced", "over-reinforced", "brittle failure", "ductile failure", "flexural design", "building codes"],
         ["Reinforced Concrete Design", "Structural Safety", "Failure Modes"]),

        ("ENG091", "Core Engineering", "Mechanical Engineering", "Intermediate", "Conceptual",
         "Explain the Second Law of Thermodynamics, Carnot efficiency limits, and why a real heat engine cannot achieve 100% thermal efficiency.",
         "The Second Law of Thermodynamics (Kelvin-Planck statement) asserts that it is impossible for any device operating on a thermodynamic cycle to receive heat from a single thermal reservoir and produce an equivalent net amount of work without rejecting heat to a low-temperature sink. The theoretical maximum efficiency of any heat engine operating between hot reservoir T_H and cold reservoir T_C is bounded by the reversible Carnot cycle: eta_Carnot = 1 - (T_C / T_H), where temperatures are in Kelvin. Achieving 100% efficiency would require an absolute zero sink (T_C = 0K), which is physically impossible. Real engines have lower efficiency due to irreversible entropy generation from friction, turbulence, and finite-temperature heat transfer.",
         ["Second Law of Thermodynamics", "Carnot efficiency", "Kelvin-Planck", "entropy generation", "thermal efficiency"],
         ["Thermodynamics", "Energy Conversion", "Thermal Cycles"]),

        ("ENG092", "Core Engineering", "Electrical Engineering", "Advanced", "Troubleshooting",
         "How do you calculate thermal resistance and size heat sinks for power MOSFETs using the thermal equivalent of Ohm's Law?",
         "Heat transfer from power semiconductor junctions to ambient air is modeled using the thermal equivalent of Ohm's law: Delta T = P_diss * R_th, where temperature difference is voltage, power dissipation P_diss (W) is current, and thermal resistance R_th (°C/W) is electrical resistance. The total thermal resistance is the sum of series components: R_th(J-A) = R_th(J-C) + R_th(C-S) + R_th(S-A), representing junction-to-case, case-to-sink (thermal paste), and sink-to-ambient resistances. To ensure junction temperature T_J remains below maximum rated silicon limit (e.g. 150°C) at worst-case ambient T_A (e.g. 50°C), the required heat sink rating is R_th(S-A) <= (T_J,max - T_A) / P_diss - (R_th(J-C) + R_th(C-S)).",
         ["thermal resistance", "MOSFET", "heat sink sizing", "junction temperature", "power dissipation"],
         ["Thermal Management", "Power Electronics", "Hardware Reliability"]),

        ("ENG093", "Core Engineering", "Civil Engineering", "Intermediate", "Analytical",
         "How does the Rational Method calculate peak stormwater runoff flow for urban drainage basin design?",
         "The Rational Method estimates peak stormwater discharge rate Q from small drainage catchments (typically < 200 acres) using the empirical equation: Q = C * I * A, where Q is peak runoff rate (cubic feet per second), C is the dimensionless runoff coefficient reflecting land use permeability (e.g. 0.15 for lawns, 0.90 for asphalt pavement), I is rainfall intensity (inches/hour), and A is catchment drainage area (acres). The rainfall intensity I is derived from Intensity-Duration-Frequency (IDF) curves for a chosen design storm return period (e.g. 10-year storm), with storm duration set equal to the basin's time of concentration (t_c) when the entire basin contributes to the outflow.",
         ["Rational Method", "stormwater runoff", "runoff coefficient", "IDF curves", "time of concentration"],
         ["Hydrology", "Urban Drainage", "Civil Infrastructure"]),

        ("ENG094", "Core Engineering", "Mechanical Engineering", "Advanced", "Troubleshooting",
         "Explain Campbell diagrams and critical shaft whirl speeds in high-speed rotating turbomachinery.",
         "Rotating machinery shafts experience lateral vibrational resonance called shaft whirl when rotational frequency matches a rotor lateral natural bending frequency. Due to gyroscopic moments in spinning turbine disks, rotor natural frequencies split and shift with rotational speed: forward whirl frequencies increase with RPM while backward whirl frequencies decrease. A Campbell diagram plots natural vibrational frequencies against rotor rotational speed, overlaid with excitation order lines (e.g., 1X synchronous unbalance, 2X misalignment). Intersections between excitation lines and natural frequency curves identify critical speeds where dangerous resonant amplification occurs, requiring operational exclusion zones.",
         ["Campbell diagram", "critical speed", "shaft whirl", "gyroscopic effect", "rotordynamics"],
         ["Rotordynamics", "Vibration Analysis", "Turbomachinery"]),

        ("ENG095", "Core Engineering", "Electrical Engineering", "Intermediate", "Analytical",
         "Explain Gain-Bandwidth Product (GBWP) and Phase Margin in operational amplifier negative feedback stability.",
         "Operational amplifiers use negative feedback to establish precise closed-loop voltage gain. An op-amp's open-loop gain drops at -20 dB/decade due to internal compensation poles. The Gain-Bandwidth Product (GBWP) is constant: Closed_Loop_Gain * Bandwidth = GBWP, meaning higher closed-loop gain directly reduces usable circuit bandwidth. Stability is governed by loop gain phase shift: at the unity-gain frequency where loop gain |A*beta| = 1 (0 dB), Phase Margin is the degrees of phase above -180°: PM = 180° + Phase(A*beta). A phase margin < 45° causes closed-loop ringing, overshoot, and risk of sustained Barkhausen oscillation; robust designs target PM >= 60°.",
         ["Gain-Bandwidth Product", "Phase Margin", "op-amp stability", "negative feedback", "Bode plot"],
         ["Analog Circuit Design", "Feedback Control", "Frequency Response"])
    ]

def get_business_topics():
    """Generates 25 specific Business, Product Management & HR topics (ENG096 - ENG120)."""
    return [
        ("ENG096", "Business, Product Management and Human Resources", "Product Strategy & Roadmaps", "Intermediate", "Business-Oriented Technical",
         "How do you calculate Customer Lifetime Value (LTV) and evaluate LTV-to-CAC ratios for SaaS unit economics?",
         "Customer Lifetime Value (LTV) represents the total gross profit expected from a customer relationship: LTV = (ARPU * Gross_Margin) / Churn_Rate, where ARPU is Average Revenue Per User and Churn is monthly logo or revenue churn. Customer Acquisition Cost (CAC) is total sales and marketing spend divided by new customers acquired in that period. In healthy SaaS economics, an LTV-to-CAC ratio of 3:1 is considered the benchmark: a ratio < 1:1 indicates unsustainable customer acquisition, while a ratio > 5:1 indicates under-investment in growth. CAC Payback period (CAC / (ARPU * Margin)) should ideally be under 12 months for cash efficiency.",
         ["LTV", "CAC", "unit economics", "SaaS metrics", "churn rate", "payback period"],
         ["Financial Modeling", "SaaS Business Metrics", "Unit Economics"]),

        ("ENG097", "Business, Product Management and Human Resources", "Agile Delivery & Project Management", "Advanced", "Scenario-Based",
         "How do you prioritize technical debt alongside customer feature requests using Weighted Shortest Job First (WSJF)?",
         "Technical debt degrades developer velocity, introduces stability risks, and causes regressions if ignored, but compete with high-visibility customer features for sprint capacity. Weighted Shortest Job First (WSJF) prioritizes work by Cost of Delay (CoD) divided by Job Duration. Cost of Delay combines User/Business Value, Time Criticality, and Risk Reduction/Opportunity Enablement. Technical debt items (such as database upgrades or refactoring coupled modules) score high on Risk Reduction and Opportunity Enablement. By evaluating features and debt through the identical economic formula, engineering teams objectively justify debt repayment based on economic impact.",
         ["WSJF", "Cost of Delay", "technical debt", "backlog prioritization", "SAFe"],
         ["Product Management", "Backlog Governance", "Agile Prioritization"]),

        ("ENG098", "Business, Product Management and Human Resources", "Business Analysis & Unit Economics", "Intermediate", "Conceptual",
         "How does cohort analysis reveal true retention dynamics compared to aggregate monthly churn rates?",
         "Aggregate churn rates blend all customers across different acquisition dates, which masks underlying retention degradation if overall growth is accelerating (new customer influx dilutes high churn from older cohorts). A cohort analysis groups customers by their signup month and tracks each cohort's retention percentage over subsequent months (Month 1, Month 2, ... Month 12). Visualized as a retention heatmap or retention curve, an asymptote indicates product-market fit (e.g. curve flattens at 40% retained). If newer cohorts exhibit downward-shifting retention curves, it signals onboarding friction or degraded product quality that aggregate metrics hide.",
         ["cohort analysis", "retention curve", "churn masking", "product-market fit", "retention heatmap"],
         ["Data Analytics", "Customer Retention", "Growth Metrics"]),

        ("ENG099", "Business, Product Management and Human Resources", "Talent Acquisition & Leadership", "Expert", "Business-Oriented Technical",
         "How do you design structured behavioral interview rubrics using the STAR method to eliminate interviewer cognitive bias?",
         "Unstructured interviews rely on conversational rapport and intuition, which introduces severe cognitive biases (halo effect, affinity bias, confirmation bias). Structured behavioral interviews evaluate candidate past behavior against predetermined job competencies using the STAR method: Situation (context), Task (objective), Action (specific individual contribution), and Result (quantifiable impact). A standardized rubric defines explicit scoring benchmarks (e.g. 1 = passive bystander, 3 = competent execution, 5 = autonomous strategic leadership with measurable business outcome). Multiple independent interviewers score each competency separately before debrief calibrations, preventing groupthink.",
         ["STAR method", "structured interview", "cognitive bias", "interview rubric", "calibrated scoring"],
         ["Talent Acquisition", "Behavioral Interviewing", "Unconscious Bias Mitigation"]),

        ("ENG100", "Business, Product Management and Human Resources", "Product Strategy & Roadmaps", "Advanced", "Scenario-Based",
         "Compare Product-Led Growth (PLG) self-serve funnels with Enterprise Sales-Led go-to-market strategies for developer platforms.",
         "Product-Led Growth (PLG) relies on the software product itself as the primary acquisition, onboarding, and expansion driver (e.g. freemium or free trial developer tools). Conversion relies on fast time-to-value (TTV), self-serve documentation, and viral bottom-up adoption by developers. In contrast, Enterprise Sales-Led strategies target C-suite and VP buyers through outbound sales, bespoke RFPs, proof-of-concept pilots, and multi-year annual contracts. High-growth developer platforms often use a hybrid model: bottom-up PLG drives organic developer grassroots adoption, and sales teams leverage product usage telemetry to close top-down enterprise security and compliance licenses.",
         ["Product-Led Growth", "Sales-Led Growth", "time-to-value", "freemium", "bottom-up adoption"],
         ["Go-To-Market Strategy", "Product-Led Growth", "Enterprise Sales"]),

        ("ENG101", "Business, Product Management and Human Resources", "Agile Delivery & Project Management", "Intermediate", "Conceptual",
         "Compare Scrum time-boxed sprints with Kanban continuous flow: WIP limits, cycle times, and planning cadences.",
         "Scrum organizes work into fixed time-boxed iterations (sprints, usually 2 weeks) with prescribed team roles (Scrum Master, Product Owner), sprint commitments, daily standups, and sprint planning/retrospective ceremonies. Work scope is locked during the sprint. Kanban is a continuous flow methodology with no mandatory sprint boundaries; work items flow through stages on a board governed by strict Work-In-Progress (WIP) limits per column. Kanban focuses on optimizing Lead Time and Cycle Time and eliminating workflow bottlenecks, making it superior for operational, support, or continuous delivery environments where priorities shift dynamically.",
         ["Scrum", "Kanban", "WIP limits", "cycle time", "time-boxed sprint", "continuous flow"],
         ["Agile Methodologies", "Workflow Optimization", "Project Management"]),

        ("ENG102", "Business, Product Management and Human Resources", "Business Analysis & Unit Economics", "Advanced", "Business-Oriented Technical",
         "What are the economic tradeoffs between Value-Based Tiered Pricing and Usage-Based Consumption Pricing for Cloud API platforms?",
         "Value-Based Tiered Pricing charges predictable monthly subscription fees based on packaged feature tiers (e.g., Starter, Pro, Enterprise). It provides stable recurring revenue (ARR) forecasting and clear upsell paths, but creates adoption friction for small users and limits upside from massive-scale enterprise power users. Usage-Based Consumption Pricing charges per resource unit consumed (e.g., API calls, GB processed, compute seconds). It lowers initial onboarding barrier and aligns customer cost directly with realized value, but introduces revenue volatility and requires sophisticated billing metering pipelines.",
         ["value-based pricing", "usage-based pricing", "consumption billing", "ARR predictability", "pricing tiers"],
         ["Monetization Strategy", "SaaS Pricing Models", "Revenue Engineering"]),

        ("ENG103", "Business, Product Management and Human Resources", "Talent Acquisition & Leadership", "Intermediate", "Scenario-Based",
         "How do standard 4-year equity vesting schedules with a 1-year cliff align employee incentives and protect company equity?",
         "In technology startups and public companies, stock options or Restricted Stock Units (RSUs) incentivize long-term value creation. A standard 4-year vesting schedule with a 1-year cliff dictates that if an employee departs within the first 12 months, zero equity vests, protecting the company from allocating permanent equity to misaligned or underperforming hires. Upon reaching the 1-year milestone, exactly 25% of the grant vests in a lump sum; thereafter, the remaining 75% vests in equal monthly or quarterly installments over the next 36 months, encouraging employee retention and shared alignment with company valuation growth.",
         ["vesting schedule", "1-year cliff", "RSUs", "stock options", "equity compensation", "retention"],
         ["Compensation Strategy", "Equity Governance", "Talent Retention"]),

        ("ENG104", "Business, Product Management and Human Resources", "Product Strategy & Roadmaps", "Expert", "Conceptual",
         "How do you formulate Objectives and Key Results (OKRs) with outcome-driven metrics rather than output-driven activity lists?",
         "Output-driven goals track activities or deliverables completed (e.g., 'Build user profile redesign' or 'Launch 5 blog posts'), which provides no assurance that user or business value was created. Outcome-driven OKRs define an ambitious qualitative Objective (e.g., 'Deliver frictionless customer onboarding') paired with 3-5 quantitative Key Results measuring behavioral or business impact: 'KR1: Reduce onboarding drop-off rate from 35% to 15%', 'KR2: Decrease Time to First Transaction from 48 hours to 2 hours', 'KR3: Maintain CSAT >= 90%'. Outcome-driven OKRs empower autonomous product squads to experiment with solutions while keeping focus locked on measurable customer impact.",
         ["OKRs", "outcome-driven", "Key Results", "CSAT", "business metrics"],
         ["Product Leadership", "Goal Setting Frameworks", "Outcome-Driven Management"]),

        ("ENG105", "Business, Product Management and Human Resources", "Agile Delivery & Project Management", "Advanced", "Business-Oriented Technical",
         "How do you conduct an effective blameless post-mortem using the 5 Whys framework following a major production outage?",
         "A blameless post-mortem assumes that engineers act in good faith with the information available and that systemic organizational or architectural flaws allow failures to manifest. Rather than punishing individuals, the team analyzes the timeline of detection, response, and mitigation. The '5 Whys' root-cause analysis iteratively investigates causal layers: e.g. Why did the site go down? Database crashed. Why? Out of disk space. Why? Log file filled partition. Why? Debug logging left on in production. Why? No automated linting on environment configs. Action items focus on automated safeguards, alerts, and architectural resilience.",
         ["blameless post-mortem", "5 Whys", "root cause analysis", "systemic failure", "incident management"],
         ["Incident Management", "Engineering Culture", "Continuous Improvement"]),

        ("ENG106", "Business, Product Management and Human Resources", "Business Analysis & Unit Economics", "Intermediate", "Scenario-Based",
         "Compare Net Promoter Score (NPS) with Customer Effort Score (CES) for diagnosing friction in user onboarding journeys.",
         "Net Promoter Score (NPS) measures overall customer brand loyalty and willingness to recommend on a 0-10 scale (Promoters minus Detractors). While useful as an executive gauge of macro brand perception, NPS is a lagging indicator and too broad to isolate specific UX bottlenecks. Customer Effort Score (CES) surveys users immediately following a discrete workflow interaction (e.g. 'How easy was it to setup your first integration?'). CES is a leading indicator that pinpoints precise operational friction points, user onboarding confusion, and workflow complexity, directly correlating with early customer churn.",
         ["Net Promoter Score", "Customer Effort Score", "user onboarding", "friction points", "customer feedback"],
         ["Customer Experience", "Product Analytics", "UX Benchmarking"]),

        ("ENG107", "Business, Product Management and Human Resources", "Talent Acquisition & Leadership", "Advanced", "Conceptual",
         "What are the ethical, legal, and operational principles for designing constructive Performance Improvement Plans (PIPs)?",
         "A Performance Improvement Plan (PIP) must be an earnest, structured intervention to help an underperforming employee meet established job standards, rather than a pre-determined paper trail for termination. Operationally, a constructive PIP establishes clear, objective, and measurable performance gaps, defines specific achievable deliverables within a defined timeframe (typically 30-90 days), and schedules weekly check-ins with clear written feedback. The manager must provide coaching, necessary resources, and unblock dependencies. If standards are not met, the PIP provides transparent, legally defensible documentation supporting equitable separation.",
         ["Performance Improvement Plan", "engineering management", "constructive feedback", "equitable separation"],
         ["People Management", "Performance Management", "Leadership & HR Governance"]),

        ("ENG108", "Business, Product Management and Human Resources", "Product Strategy & Roadmaps", "Intermediate", "Business-Oriented Technical",
         "How do you design a Riskiest Assumption Test (RAT) to validate a product concept before writing production code?",
         "A Minimum Viable Product (MVP) often involves building excessive functional code before validating whether customers actually want the solution. A Riskiest Assumption Test (RAT) identifies the single assumption that poses the highest probability of total product failure if proven wrong (e.g., 'Will enterprise legal teams allow employees to upload proprietary code to cloud LLMs?'). The team designs the fastest, cheapest experiment to test that specific hypothesis directly (e.g., a clickable mock, a fake-door landing page, or 10 customer discovery interviews) before committing engineering capacity to production implementation.",
         ["Riskiest Assumption Test", "MVP", "hypothesis validation", "product discovery", "fake-door test"],
         ["Lean Product Management", "Discovery Testing", "De-Risking"]),

        ("ENG109", "Business, Product Management and Human Resources", "Agile Delivery & Project Management", "Expert", "Scenario-Based",
         "How do you map and resolve cross-squad architectural dependencies in a multi-team microservices organization?",
         "In organizations with multiple autonomous squads, feature delivery often stalls when squad A requires API endpoints from squad B. A cross-squad Dependency Matrix identifies technical couplings, upstream blockers, and lead time requirements during quarterly planning. To resolve dependencies, organizations apply Domain-Driven Design (DDD) to realign squad boundaries around decoupled Bounded Contexts, adopt internal open-source (InnerSource) where squad A can submit pull requests directly to squad B's codebase, and establish consumer-driven contracts with mock stubs to unblock parallel development.",
         ["cross-squad dependencies", "InnerSource", "Bounded Contexts", "Dependency Matrix", "scaled agile"],
         ["Organizational Design", "Scaled Agile", "Cross-Functional Coordination"]),

        ("ENG110", "Business, Product Management and Human Resources", "Business Analysis & Unit Economics", "Advanced", "Conceptual",
         "How do Contribution Margin and Gross Margin differ in SaaS financial models, and what costs belong in COGS?",
         "Gross Margin measures revenue remaining after deducting direct Cost of Goods Sold (COGS): Gross Margin = (Revenue - COGS) / Revenue. In SaaS, COGS includes third-party hosting infrastructure (AWS/GCP), customer support engineering salaries, software licenses used directly to deliver the product, and third-party API costs (e.g. OpenAI tokens). Contribution Margin evaluates profitability after deducting both COGS and variable sales/marketing commissions and merchant payment processing fees: Contribution Margin = (Revenue - Variable_Costs) / Revenue. Gross margin reflects software scalability, while contribution margin reveals unit profitability.",
         ["Gross Margin", "Contribution Margin", "COGS", "SaaS financial model", "variable costs"],
         ["Financial Analysis", "SaaS Accounting", "Profitability Metrics"]),

        ("ENG111", "Business, Product Management and Human Resources", "Talent Acquisition & Leadership", "Intermediate", "Business-Oriented Technical",
         "How do you build a technical candidate sourcing pipeline for specialized Machine Learning and Distributed Systems engineers?",
         "Sourcing high-demand specialized engineers requires moving beyond generic LinkedIn keyword spam. An effective sourcing pipeline involves technical community mapping: analyzing contributors to relevant open-source repositories (e.g. PyTorch, vLLM, Kafka), identifying authors of applied research papers at top conferences (NeurIPS, OSDI, VLDB), and participating in niche technical Discord/Slack communities. Outreach messages must be highly personalized and technical, highlighting challenging unsolved architecture problems and tech stack specifics rather than generic corporate marketing, coupled with structured talent CRM pipelining.",
         ["candidate sourcing", "talent pipeline", "open-source recruiting", "technical outreach", "employer brand"],
         ["Technical Recruiting", "Talent Acquisition", "Specialized Sourcing"]),

        ("ENG112", "Business, Product Management and Human Resources", "Product Strategy & Roadmaps", "Advanced", "Scenario-Based",
         "How do you define a North Star Metric and connect it to input metrics across product development squads?",
         "A North Star Metric is the single key metric that best captures the core value a product delivers to customers while driving sustainable long-term business revenue (e.g., Spotify: 'Time spent listening to content'; Airbnb: 'Nights booked'). A North Star Metric is too high-level for an individual squad to move directly; it must be decomposed into operational input metrics across four dimensions: Breadth (active users), Depth (engagement level per user), Frequency (how often users engage), and Efficiency (time to value). Squads align their quarterly OKRs to specific input metrics, creating clear causal linkage to the North Star.",
         ["North Star Metric", "input metrics", "product strategy", "engagement breadth", "value delivery"],
         ["Product Leadership", "Metrics Trees", "Strategic Alignment"]),

        ("ENG113", "Business, Product Management and Human Resources", "Agile Delivery & Project Management", "Intermediate", "Conceptual",
         "Why are Story Points estimated using Fibonacci sequences instead of linear hours in agile planning poker?",
         "Estimating tasks in absolute hours creates false precision and conflates task complexity with individual developer skill. Story points quantify relative effort, technical complexity, risk, and unknowns. The Fibonacci sequence (1, 2, 3, 5, 8, 13, 21) reflects Weber's Law of psychophysics: as numbers grow larger, the human brain cannot distinguish fine differences (the difference between 1 and 2 hours is obvious, but the difference between 20 and 21 hours is indistinguishable). Forcing exponential intervals accelerates estimation debates and highlights when a story is too large and ambiguous (>= 13), prompting decomposition.",
         ["Story Points", "Planning Poker", "Fibonacci sequence", "relative estimation", "velocity"],
         ["Agile Estimation", "Scrum Planning", "Complexity Sizing"]),

        ("ENG114", "Business, Product Management and Human Resources", "Business Analysis & Unit Economics", "Expert", "Business-Oriented Technical",
         "How do you calculate gross margin impact and per-query COGS for generative AI features powered by commercial LLM APIs?",
         "Generative AI features introduce variable marginal compute costs that threaten traditional 80% SaaS gross margins. Calculating per-query COGS requires tracking prompt input tokens and completion output tokens multiplied by API pricing: Cost_per_query = (N_input * Price_in + N_output * Price_out) + Vector_DB_Search_Cost + Cloud_Compute_Host_Cost. To maintain healthy margins, product teams implement semantic caching (caching identical LLM completions in Redis vector databases), optimize prompt length, leverage model routing (routing simple queries to cheaper 8B models and complex queries to 70B models), and evaluate volume-tiered commitments.",
         ["LLM COGS", "token economics", "semantic caching", "model routing", "generative AI margins"],
         ["AI Unit Economics", "Cost Engineering", "SaaS Gross Margins"]),

        ("ENG115", "Business, Product Management and Human Resources", "Talent Acquisition & Leadership", "Advanced", "Scenario-Based",
         "How do you implement blind resume screening and competency-based assessment to increase diversity in engineering hiring?",
         "Unconscious bias in hiring frequently disadvantages candidates based on demographic signals on resumes (names, gender, age, university prestige). Blind resume screening strips identifying personal information, addresses, and graduation dates from applicant profiles before review by hiring managers, focusing evaluation strictly on demonstrated skills, portfolio projects, and technical qualifications. Pairing this with standardized, skill-based take-home or work-sample assessments scored against objective rubrics ensures that candidates advance based on competency rather than demographic pedigree, broadening the hiring funnel.",
         ["blind screening", "unconscious bias", "diversity in tech", "work-sample assessment", "objective rubrics"],
         ["DEI in Hiring", "Fair Hiring Practices", "Talent Assessment"]),

        ("ENG116", "Business, Product Management and Human Resources", "Product Strategy & Roadmaps", "Intermediate", "Conceptual",
         "Explain the Jobs-to-be-Done (JTBD) framework and contrast customer 'jobs' with functional product features.",
         "The Jobs-to-be-Done (JTBD) framework asserts that customers do not buy products; they 'hire' products to make progress in specific circumstances. A functional feature describes what a tool does (e.g. 'quarter-inch drill bit'), whereas the job describes the underlying human objective and desired progress (e.g. 'quarter-inch hole in wall to hang a family photo'). Understanding the functional, emotional, and social dimensions of the customer job prevents product teams from over-indexing on feature bloat and opens competitive insight into unexpected competitors (e.g., Netflix competing with sleep rather than cable TV).",
         ["Jobs-to-be-Done", "JTBD", "customer progress", "functional features", "product discovery"],
         ["Customer Discovery", "Product Positioning", "Value Proposition"]),

        ("ENG117", "Business, Product Management and Human Resources", "Agile Delivery & Project Management", "Advanced", "Business-Oriented Technical",
         "How do you manage enterprise release trains, release candidate stabilization, and compliance sign-offs in regulated software?",
         "In regulated industries (healthcare, finance, aerospace), continuous automated deployment to production must adhere to strict regulatory compliance (HIPAA, SOC 2, ISO 27001). A Release Train model schedules fixed departure intervals for releases (e.g. bi-weekly). Features ready before cutoff board the train; incomplete features remain behind feature flags. A short stabilization phase executes automated end-to-end regression suites, security vulnerability static/dynamic analysis (SAST/DAST), and compliance audit trails. Cryptographic artifact signing and automated change management tickets verify auditability before deployment.",
         ["release train", "SOC 2", "compliance sign-off", "SAST/DAST", "artifact signing"],
         ["Regulated Software", "Release Management", "Compliance & Governance"]),

        ("ENG118", "Business, Product Management and Human Resources", "Business Analysis & Unit Economics", "Intermediate", "Scenario-Based",
         "Differentiate between Voluntary and Involuntary Churn in subscription businesses and explain automated dunning management.",
         "Voluntary churn occurs when a customer consciously decides to cancel their subscription due to dissatisfaction, lack of usage, or budget cuts. Involuntary (passive) churn occurs when a paying customer's subscription terminates unintentionally due to payment processing failures (expired credit cards, false-positive fraud declines, bank network timeouts). Involuntary churn accounts for 20-40% of all SaaS churn. Automated dunning management combats involuntary churn through smart retry schedules (retrying failed cards on optimal days of the week), automated pre-expiration email alerts, and real-time account updater integrations via Stripe/Visa.",
         ["involuntary churn", "voluntary churn", "dunning management", "payment retries", "SaaS retention"],
         ["Revenue Operations", "Churn Mitigation", "Subscription Billing"]),

        ("ENG119", "Business, Product Management and Human Resources", "Talent Acquisition & Leadership", "Advanced", "Conceptual",
         "Explain dual-track engineering career ladders: parallel Individual Contributor (IC) and Engineering Management progressions.",
         "Historically, technology organizations forced top engineers into people management roles to advance in compensation and seniority, resulting in frustrated managers and lost technical talent. A dual-track engineering career ladder establishes parallel, equally compensated growth tracks: the Management track (Engineering Manager -> Director -> VP) focusing on people development, organizational alignment, hiring, and delivery execution; and the Individual Contributor (IC) track (Staff -> Principal -> Distinguished Engineer) focusing on high-impact system architecture, technical strategy, and organizational mentorship. Both tracks carry equivalent equity and prestige.",
         ["dual-track career ladder", "Staff Engineer", "Engineering Manager", "technical leadership", "IC track"],
         ["Engineering Culture", "Career Development", "Organizational Design"]),

        ("ENG120", "Business, Product Management and Human Resources", "Business Analysis & Unit Economics", "Expert", "Business-Oriented Technical",
         "How do Discounted Cash Flow (DCF) models and valuation multiples (EV/ARR) value high-growth technology companies?",
         "Valuing high-growth technology companies involves two complementary methodologies. Discounted Cash Flow (DCF) projects free cash flows over 5-10 years and discounts them to present value using the Weighted Average Cost of Capital (WACC), adding a terminal value; while theoretically rigorous, DCF is highly sensitive to terminal growth rate and discount rate assumptions. Market multiple valuation benchmarks enterprise value against annual recurring revenue: EV/ARR. Multiples are driven by growth rate, gross margins, net revenue retention (NRR), and capital efficiency (Rule of 40: Growth Rate % + Free Cash Flow Margin % >= 40%).",
         ["DCF", "EV/ARR", "Rule of 40", "Net Revenue Retention", "valuation multiples"],
         ["Corporate Finance", "Startup Valuation", "Financial Metrics"])
    ]

def build_complete_dataset():
    all_raw = list(RECORDS) # First 10
    
    # 11 - 30
    for item in load_remaining_data():
        q_id, cat, subcat, diff, q_type, q, a, gloss, concepts = item
        all_raw.append({
            "id": q_id,
            "category": cat,
            "subcategory": subcat,
            "difficulty": diff,
            "question_type": q_type,
            "question": q,
            "answer": a,
            "glossary_terms_used": gloss,
            "key_concepts": concepts,
            "semantic_rubric_ideas": [
                {
                    "idea_id": f"{q_id}_IDEA_1",
                    "semantic_statement": f"Explains the core principles and underlying mechanics of {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts conceptual explanations and technical terminology."
                },
                {
                    "idea_id": f"{q_id}_IDEA_2",
                    "semantic_statement": f"Articulates practical tradeoffs, failure modes, or architectural optimizations for {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts discussions of performance, resilience, or design decisions."
                }
            ]
        })
        
    # 31 - 55
    for item in get_ml_topics():
        q_id, cat, subcat, diff, q_type, q, a, gloss, concepts = item
        all_raw.append({
            "id": q_id,
            "category": cat,
            "subcategory": subcat,
            "difficulty": diff,
            "question_type": q_type,
            "question": q,
            "answer": a,
            "glossary_terms_used": gloss,
            "key_concepts": concepts,
            "semantic_rubric_ideas": [
                {
                    "idea_id": f"{q_id}_IDEA_1",
                    "semantic_statement": f"Explains the foundational mathematical or algorithmic theory of {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts conceptual descriptions of models, statistics, and training dynamics."
                },
                {
                    "idea_id": f"{q_id}_IDEA_2",
                    "semantic_statement": f"Identifies validation strategies, failure mitigations, or optimization techniques in {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts practical deployment, regularization, or inference considerations."
                }
            ]
        })

    # 56 - 75
    for item in get_web_cloud_topics():
        q_id, cat, subcat, diff, q_type, q, a, gloss, concepts = item
        all_raw.append({
            "id": q_id,
            "category": cat,
            "subcategory": subcat,
            "difficulty": diff,
            "question_type": q_type,
            "question": q,
            "answer": a,
            "glossary_terms_used": gloss,
            "key_concepts": concepts,
            "semantic_rubric_ideas": [
                {
                    "idea_id": f"{q_id}_IDEA_1",
                    "semantic_statement": f"Explains the operational protocols and architectural mechanics of {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts descriptions of network protocols, cloud containers, or frontend patterns."
                },
                {
                    "idea_id": f"{q_id}_IDEA_2",
                    "semantic_statement": f"Articulates security safeguards, reliability protections, and scalability tradeoffs in {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts zero-trust security, observability, or performance optimization explanations."
                }
            ]
        })

    # 76 - 95
    for item in get_core_engineering_topics():
        q_id, cat, subcat, diff, q_type, q, a, gloss, concepts = item
        all_raw.append({
            "id": q_id,
            "category": cat,
            "subcategory": subcat,
            "difficulty": diff,
            "question_type": q_type,
            "question": q,
            "answer": a,
            "glossary_terms_used": gloss,
            "key_concepts": concepts,
            "semantic_rubric_ideas": [
                {
                    "idea_id": f"{q_id}_IDEA_1",
                    "semantic_statement": f"Explains the physical laws, material dynamics, or circuit principles governing {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts physics, engineering formulas, and analytical derivations."
                },
                {
                    "idea_id": f"{q_id}_IDEA_2",
                    "semantic_statement": f"Applies failure analysis, design safety factors, or troubleshooting methods to {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts engineering mitigations, safety codes, and diagnostic methodologies."
                }
            ]
        })

    # 96 - 120
    for item in get_business_topics():
        q_id, cat, subcat, diff, q_type, q, a, gloss, concepts = item
        all_raw.append({
            "id": q_id,
            "category": cat,
            "subcategory": subcat,
            "difficulty": diff,
            "question_type": q_type,
            "question": q,
            "answer": a,
            "glossary_terms_used": gloss,
            "key_concepts": concepts,
            "semantic_rubric_ideas": [
                {
                    "idea_id": f"{q_id}_IDEA_1",
                    "semantic_statement": f"Explains the strategic frameworks and analytical metrics fundamental to {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts financial formulas, agile principles, and strategic definitions."
                },
                {
                    "idea_id": f"{q_id}_IDEA_2",
                    "semantic_statement": f"Articulates leadership, cross-functional execution, or governance strategies in {subcat}.",
                    "required": True,
                    "weight": 0.5,
                    "acceptable_paraphrase_guidance": "Accepts organizational alignment, bias mitigation, or execution management."
                }
            ]
        })

    assert len(all_raw) == 120, f"Expected 120 records, got {len(all_raw)}"
    return all_raw

if __name__ == "__main__":
    records = build_complete_dataset()
    out_path = Path("data/QandA.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Successfully rebuilt {len(records)} unique records in {out_path}")
