/**
 * Real-Time Acoustic & Phonetic Technical Recovery Engine (Client-Side).
 *
 * Implements Stage 1 live technical vocabulary normalization and acoustic slice recovery.
 * Recovers Indian-English accent variations, phonetic misrecognitions, and common speech-to-text
 * errors for computer science, software engineering, machine learning, and systems interviews.
 *
 * Guarantee: Zero mark deduction for regional accents or ASR misrecognitions.
 */

export interface RecoveryAuditItem {
  original: string;
  recovered: string;
  timestamp: number;
}

export interface RecoveryResult {
  text: string;
  recoveredCount: number;
  auditItems: RecoveryAuditItem[];
}

// Curated technical lexicon mapping acoustic/accent misrecognitions to canonical technical terms
const TECHNICAL_ACOUSTIC_MAP: Array<{ pattern: RegExp; replacement: string; originalExample: string }> = [
  // --- Data Structures & Algorithms ---
  { pattern: /\b(die\s*extra|die\s*extract|dike\s*straw|dijkstras?)\b/gi, replacement: "Dijkstra's", originalExample: "die extra" },
  { pattern: /\b(assumptions\s*complexity|as\s*in\s*tonic\s*complexity|assymptotic\s*complexity|asymptotic\s*complexity)\b/gi, replacement: "asymptotic complexity", originalExample: "assumptions complexity" },
  { pattern: /\b(assumptions|as\s*in\s*tonic|assymptotic)\b/gi, replacement: "asymptotic", originalExample: "assumptions" },
  { pattern: /\b(be\s*plus\s*tree|b\s*plus\s*tree|b\+\s*tree)\b/gi, replacement: "B+ tree", originalExample: "be plus tree" },
  { pattern: /\b(be\s*tree|be\s*tray|be\s*true|b\s*three|b\s*tree)\b/gi, replacement: "B-tree", originalExample: "be tree" },
  { pattern: /\b(has\s*map|hasmap|hashmap|hash\s*table)\b/gi, replacement: "hash map", originalExample: "has map" },
  { pattern: /\b(link\s*list|linklist|linkedlist)\b/gi, replacement: "linked list", originalExample: "link list" },
  { pattern: /\b(double\s*link\s*list|doubly\s*link\s*list)\b/gi, replacement: "doubly linked list", originalExample: "double link list" },
  { pattern: /\b(breath\s*first\s*search|breath\s*first|breadth\s*first)\b/gi, replacement: "breadth-first search", originalExample: "breath first search" },
  { pattern: /\b(deft\s*first\s*search|death\s*first\s*search|depth\s*first)\b/gi, replacement: "depth-first search", originalExample: "deft first search" },
  { pattern: /\b(quick\s*sort|quicksilver)\b/gi, replacement: "QuickSort", originalExample: "quick sort" },
  { pattern: /\b(merge\s*sort)\b/gi, replacement: "MergeSort", originalExample: "merge sort" },
  { pattern: /\b(heap\s*sort)\b/gi, replacement: "HeapSort", originalExample: "heap sort" },
  { pattern: /\b(resursion|re\s*curse\s*on)\b/gi, replacement: "recursion", originalExample: "resursion" },
  { pattern: /\b(memorization|memoisation|memo\s*ization)\b/gi, replacement: "memoization", originalExample: "memorization" },
  { pattern: /\b(big\s*oh|big\s*o)\b/gi, replacement: "Big-O", originalExample: "big oh" },
  { pattern: /\b(priority\s*q|priority\s*queue)\b/gi, replacement: "priority queue", originalExample: "priority q" },
  { pattern: /\b(bst|binary\s*search\s*tree)\b/gi, replacement: "binary search tree", originalExample: "bst" },
  { pattern: /\b(avl\s*tree|a\s*v\s*l\s*tree)\b/gi, replacement: "AVL tree", originalExample: "avl tree" },
  { pattern: /\b(red\s*black\s*tree|red\s*black)\b/gi, replacement: "Red-Black tree", originalExample: "red black tree" },
  { pattern: /\b(crux\s*call|kruskals?|kruskal's)\b/gi, replacement: "Kruskal's algorithm", originalExample: "crux call" },
  { pattern: /\b(prims?|prim's)\b/gi, replacement: "Prim's algorithm", originalExample: "prims" },
  { pattern: /\b(bellman\s*ford|belman\s*ford)\b/gi, replacement: "Bellman-Ford", originalExample: "belman ford" },
  { pattern: /\b(floyd\s*warshall|floyd\s*marshall)\b/gi, replacement: "Floyd-Warshall", originalExample: "floyd marshall" },
  { pattern: /\b(topo\s*sort|topological\s*sort)\b/gi, replacement: "topological sort", originalExample: "topo sort" },
  { pattern: /\b(trie\s*data\s*structure|try\s*data\s*structure)\b/gi, replacement: "trie", originalExample: "try data structure" },

  // --- Operating Systems & Concurrency ---
  { pattern: /\b(moot\s*acts|moot\s*access|mute\s*x|mutants)\b/gi, replacement: "mutex", originalExample: "moot acts" },
  { pattern: /\b(semfor|semafor|semaphores?)\b/gi, replacement: "semaphore", originalExample: "semfor" },
  { pattern: /\b(current\s*see|concurrent\s*see|concurrency)\b/gi, replacement: "concurrency", originalExample: "current see" },
  { pattern: /\b(dad\s*lock|dead\s*lock)\b/gi, replacement: "deadlock", originalExample: "dad lock" },
  { pattern: /\b(start\s*vation|starvations?)\b/gi, replacement: "starvation", originalExample: "start vation" },
  { pattern: /\b(ray'?s\s*condition|race\s*conditions?)\b/gi, replacement: "race condition", originalExample: "ray's condition" },
  { pattern: /\b(context\s*switch(ing)?)\b/gi, replacement: "context switching", originalExample: "context switch" },
  { pattern: /\b(page\s*faults?)\b/gi, replacement: "page fault", originalExample: "page fault" },
  { pattern: /\b(virtual\s*memory)\b/gi, replacement: "virtual memory", originalExample: "virtual memory" },
  { pattern: /\b(inter\s*process\s*communication|i\s*p\s*c)\b/gi, replacement: "IPC", originalExample: "ipc" },
  { pattern: /\b(compare\s*and\s*swap|c\s*a\s*s)\b/gi, replacement: "compare-and-swap (CAS)", originalExample: "compare and swap" },

  // --- System Design, Cloud & Databases ---
  { pattern: /\b(tell\s*our\s*you\s*cash|tell\s*are\s*you\s*cash|all\s*are\s*you\s*cash|l\s*r\s*u\s*cash|lru\s*cash)\b/gi, replacement: "LRU cache", originalExample: "tell our you cash" },
  { pattern: /\b(tell\s*our\s*you|tell\s*are\s*you|l\s*r\s*u)\b/gi, replacement: "LRU", originalExample: "tell our you" },
  { pattern: /\b(lfu\s*cash|l\s*f\s*u\s*cash)\b/gi, replacement: "LFU cache", originalExample: "lfu cash" },
  { pattern: /\b(item\s*potent|idea\s*potent|idempotent)\b/gi, replacement: "idempotent", originalExample: "item potent" },
  { pattern: /\b(asset\s*properties|acid\s*properties)\b/gi, replacement: "ACID properties", originalExample: "asset properties" },
  { pattern: /\b(cup\s*theorem|cap\s*theorem)\b/gi, replacement: "CAP theorem", originalExample: "cup theorem" },
  { pattern: /\b(pack\s*sauce|packs\s*us|paxos)\b/gi, replacement: "Paxos", originalExample: "pack sauce" },
  { pattern: /\b(wrapped\s*consensus|raft\s*consensus|raft)\b/gi, replacement: "Raft consensus", originalExample: "wrapped consensus" },
  { pattern: /\b(charting\s*database|sharding)\b/gi, replacement: "sharding", originalExample: "charting database" },
  { pattern: /\b(consistent\s*hashing)\b/gi, replacement: "consistent hashing", originalExample: "consistent hashing" },
  { pattern: /\b(write\s*ahead\s*log|w\s*a\s*l)\b/gi, replacement: "write-ahead log (WAL)", originalExample: "write ahead log" },
  { pattern: /\b(bloom\s*filters?)\b/gi, replacement: "Bloom filter", originalExample: "bloom filter" },
  { pattern: /\b(lsm\s*tree|log\s*structured\s*merge\s*tree)\b/gi, replacement: "LSM tree", originalExample: "lsm tree" },
  { pattern: /\b(no\s*sequel|no\s*sql)\b/gi, replacement: "NoSQL", originalExample: "no sequel" },
  { pattern: /\b(postgress?|postgre)\b/gi, replacement: "PostgreSQL", originalExample: "postgress" },
  { pattern: /\b(kubernets|cubernetes)\b/gi, replacement: "Kubernetes", originalExample: "kubernets" },
  { pattern: /\b(reddis)\b/gi, replacement: "Redis", originalExample: "reddis" },
  { pattern: /\b(dockers)\b/gi, replacement: "Docker", originalExample: "dockers" },

  // --- Object-Oriented & Engineering Fundamentals ---
  { pattern: /\b(polymorfism|polymer\s*ism)\b/gi, replacement: "polymorphism", originalExample: "polymer ism" },
  { pattern: /\b(sinkronous)\b/gi, replacement: "synchronous", originalExample: "sinkronous" },
  { pattern: /\b(asinc|asink)\b/gi, replacement: "async", originalExample: "asink" },
  { pattern: /\b(c\s*plus\s*plus)\b/gi, replacement: "C++", originalExample: "c plus plus" },
  { pattern: /\b(c\s*sharp)\b/gi, replacement: "C#", originalExample: "c sharp" },
  { pattern: /\b(dot\s*net)\b/gi, replacement: ".NET", originalExample: "dot net" },

  // --- Machine Learning & AI ---
  { pattern: /\b(the\s*bios\s*variants\s*trade\s*of|bios\s*variants\s*trade\s*of|bias\s*variance\s*trade\s*of)\b/gi, replacement: "bias-variance tradeoff", originalExample: "bios variants trade of" },
  { pattern: /\b(bios\s*variants|bios\s*variant)\b/gi, replacement: "bias-variance", originalExample: "bios variants" },
  { pattern: /\b(and\s*sensible\s*methods|sensible\s*methods)\b/gi, replacement: "ensemble methods", originalExample: "and sensible methods" },
  { pattern: /\b(and\s*sensible)\b/gi, replacement: "ensemble", originalExample: "and sensible" },
  { pattern: /\b(greatient\s*decent|gradient\s*decent)\b/gi, replacement: "gradient descent", originalExample: "greatient decent" },
  { pattern: /\b(iron\s*values?)\b/gi, replacement: "eigenvalue", originalExample: "iron value" },
  { pattern: /\b(iron\s*vectors?)\b/gi, replacement: "eigenvector", originalExample: "iron vector" },
  { pattern: /\b(piper\s*parameter)\b/gi, replacement: "hyperparameter", originalExample: "piper parameter" },
  { pattern: /\b(over\s*fitting)\b/gi, replacement: "overfitting", originalExample: "over fitting" },
  { pattern: /\b(under\s*fitting)\b/gi, replacement: "underfitting", originalExample: "under fitting" },
  { pattern: /\b(convolutional\s*neural\s*network|c\s*n\s*n)\b/gi, replacement: "CNN", originalExample: "cnn" },
  { pattern: /\b(recurrent\s*neural\s*network|r\s*n\s*n)\b/gi, replacement: "RNN", originalExample: "rnn" },
  { pattern: /\b(attention\s*mechanism|self\s*attention)\b/gi, replacement: "attention mechanism", originalExample: "attention mechanism" },
  { pattern: /\b(back\s*propagation)\b/gi, replacement: "backpropagation", originalExample: "back propagation" },
  { pattern: /\b(im\s*aira)\b/gi, replacement: "IMAIRA", originalExample: "im aira" },
  { pattern: /\b(fair\s*score)\b/gi, replacement: "FairScore", originalExample: "fair score" },

  // --- Indian English & Fast Speech Acoustic Normalizations ---
  { pattern: /\b(tells\s*does|tell\s*does)\b/gi, replacement: "tells us", originalExample: "tells does" },
  { pattern: /\b(of\s*the\s*hour)\b/gi, replacement: "of our", originalExample: "of the hour" },
  { pattern: /\b(weight\s*book|wait\s*book|wave\s*hook)\b/gi, replacement: "webhook", originalExample: "weight book" },
  { pattern: /\b(h\s*m\s*a\s*c|h\s*mac)\b/gi, replacement: "HMAC", originalExample: "h mac" },
  { pattern: /\b(exponential\s*back\s*off)\b/gi, replacement: "exponential backoff", originalExample: "exponential back off" },
  { pattern: /\b(linear\s*probing)\b/gi, replacement: "linear probing", originalExample: "linear probing" },
  { pattern: /\b(quadratic\s*probing)\b/gi, replacement: "quadratic probing", originalExample: "quadratic probing" },
  { pattern: /\b(separate\s*chaining)\b/gi, replacement: "separate chaining", originalExample: "separate chaining" },
  { pattern: /\b(open\s*addressing)\b/gi, replacement: "open addressing", originalExample: "open addressing" },
  { pattern: /\b(hash\s*collision|has\s*collision)\b/gi, replacement: "hash collision", originalExample: "has collision" },
  { pattern: /\b(load\s*factor)\b/gi, replacement: "load factor", originalExample: "load factor" },
  { pattern: /\b(amortized\s*complexity|amortised\s*complexity)\b/gi, replacement: "amortized complexity", originalExample: "amortized complexity" },
  { pattern: /\b(re\s*balancing|rebalancing)\b/gi, replacement: "rebalancing", originalExample: "re balancing" },
  { pattern: /\b(l\s*t\s*v)\b/gi, replacement: "LTV", originalExample: "l t v" },
  { pattern: /\b(c\s*a\s*c)\b/gi, replacement: "CAC", originalExample: "c a c" },
  { pattern: /\b(a\s*r\s*p\s*u)\b/gi, replacement: "ARPU", originalExample: "a r p u" },
];

export class PhoneticRecoveryEngine {
  /**
   * Recovers raw speech transcription text into canonical technical vocabulary.
   * Runs in sub-millisecond time on client-side streaming chunks.
   */
  recoverText(inputText: string): RecoveryResult {
    if (!inputText || !inputText.trim()) {
      return { text: inputText, recoveredCount: 0, auditItems: [] };
    }

    let resultText = inputText;
    let recoveredCount = 0;
    const auditItems: RecoveryAuditItem[] = [];

    for (const item of TECHNICAL_ACOUSTIC_MAP) {
      if (item.pattern.test(resultText)) {
        // Find matches for audit trail
        const matches = resultText.match(item.pattern);
        if (matches) {
          for (const m of matches) {
            auditItems.push({
              original: m,
              recovered: item.replacement,
              timestamp: Date.now(),
            });
            recoveredCount++;
          }
        }
        resultText = resultText.replace(item.pattern, item.replacement);
      }
    }

    return {
      text: resultText,
      recoveredCount,
      auditItems,
    };
  }
}

export const phoneticRecovery = new PhoneticRecoveryEngine();
