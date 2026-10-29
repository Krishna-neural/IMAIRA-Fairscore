#!/usr/bin/env python3
"""Build 120 questions semantic rubrics and 240 dev / 60 heldout datasets for IMAIRA-Fairscore."""

import hashlib
import json
import os
import random
from pathlib import Path

# Seed for reproducibility
random.seed(42)

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

QUESTIONS_DATA = [
    # --- Machine Learning & Deep Learning (30 questions) ---
    (
        "Q001",
        "Explain gradient descent and how the learning rate affects optimization.",
        "Machine Learning",
        [
            ("Parameters are updated iteratively in the direction of the negative gradient of the loss function to reach an optimum.",
             "Accepts descriptions like 'stepping downhill along the slope' or phonetic ASR variants like 'greatient decent'."),
            ("The learning rate scales step size, where too large causes divergence or overshooting and too small causes slow convergence.",
             "Accepts phrases like 'big steps miss the minimum', 'small steps take forever', or 'learning rate controls jump size'."),
            ("Convergence conditions involve monitoring loss gradient magnitude or loss plateauing across successive epochs.",
             "Accepts mentions of stopping criteria, loss flattening out, or gradient vanishing at minima.")
        ]
    ),
    (
        "Q002",
        "What is the bias-variance tradeoff and how does model complexity relate to it?",
        "Machine Learning",
        [
            ("High bias stems from overly simplistic models underfitting training data and missing true relationships.",
             "Accepts 'underfitting', 'rigid assumptions', or 'model cannot learn pattern'."),
            ("High variance occurs when complex models overfit training noise rather than generalizing to unseen data.",
             "Accepts 'overfitting', 'memorizing noise', or 'sensitiveness to training set changes'."),
            ("Optimal generalization requires balancing complexity to minimize total error composed of bias squared, variance, and irreducible noise.",
             "Accepts sweet spot tradeoff descriptions, curve intersections, or regularization as a balancing mechanism.")
        ]
    ),
    (
        "Q003",
        "Describe overfitting and explain three common techniques to prevent it.",
        "Machine Learning",
        [
            ("Overfitting occurs when a model learns training data details and noise too closely, failing to generalize to new inputs.",
             "Accepts 'memorizes training set', 'poor test performance despite low train loss'."),
            ("L1/L2 regularization penalizes large weights to constrain model capacity.",
             "Accepts lasso/ridge explanations, weight decay, or shrinking coefficients toward zero."),
            ("Data augmentation, early stopping, or dropout provide additional mechanisms to prevent overfitting by restricting memorization.",
             "Accepts dropout randomly turning off units, stopping when validation loss rises, or generating synthetic examples.")
        ]
    ),
    (
        "Q004",
        "Explain how the backpropagation algorithm computes gradients in neural networks.",
        "Machine Learning",
        [
            ("Applies the mathematical chain rule of calculus backwards from the output loss through hidden layers.",
             "Accepts 'chain rule', 'differentiating backward', or 'propagating loss gradient from end to start'."),
            ("Caches intermediate forward activations and computes partial derivatives of loss with respect to weights and biases.",
             "Accepts storing layer activations during forward pass, calculating dL/dW, or error accumulation."),
            ("Gradients are then supplied to optimization algorithms to update parameters in proportion to their contribution to loss.",
             "Accepts feeding gradients to SGD or Adam to adjust weights.")
        ]
    ),
    (
        "Q005",
        "What is the difference between L1 (Lasso) and L2 (Ridge) regularization?",
        "Machine Learning",
        [
            ("L1 penalizes the sum of absolute values of weights, driving non-essential coefficients exactly to zero for feature selection.",
             "Accepts 'absolute penalty', 'sparse weights', or 'sets unhelpful features to zero'."),
            ("L2 penalizes the sum of squared weights, shrinking parameters smoothly without forcing exact zeros.",
             "Accepts 'squared penalty', 'weight decay', or 'shrinks weights proportionally'."),
            ("Geometrically, L1 has sharp diamond-shaped constraint boundaries intersecting axes, whereas L2 has smooth spherical contours.",
             "Accepts descriptions of diamond vs circle intersections or non-differentiability at zero.")
        ]
    ),
    (
        "Q006",
        "Explain the architecture and purpose of the self-attention mechanism in Transformers.",
        "Machine Learning",
        [
            ("Transforms input representations into Query, Key, and Value vectors via learnable linear projections.",
             "Accepts QKV matrix multiplication or projection explanation."),
            ("Computes compatibility attention scores using scaled dot products between queries and keys, normalized via softmax.",
             "Accepts 'softmax of Q times K transpose divided by square root of dimension' or similarity weighting."),
            ("Produces output as a weighted sum of Value vectors, allowing each token to dynamically attend to any other token regardless of distance.",
             "Accepts capture of long-range dependencies, dynamic context mixing, or O(1) path length between tokens.")
        ]
    ),
    (
        "Q007",
        "Compare Batch Normalization and Layer Normalization, explaining where each is typically used.",
        "Machine Learning",
        [
            ("Batch Normalization computes mean and variance across the batch dimension for each feature channel, common in CNNs.",
             "Accepts normalizing across images in a batch or spatial feature map normalization."),
            ("Layer Normalization computes mean and variance across all features/channels for an individual sample independently, standard in RNNs and Transformers.",
             "Accepts per-token normalization, sequence-length invariance, or batch-size independent normalization."),
            ("LayerNorm is preferred in sequential models because variable sequence lengths and small batch sizes degrade BatchNorm statistics.",
             "Accepts explanations of batch size sensitivity or sequence padding issues in BatchNorm.")
        ]
    ),
    (
        "Q008",
        "What is the vanishing gradient problem in deep networks and how do modern architectures solve it?",
        "Machine Learning",
        [
            ("Occurs when repeated multiplication of small derivatives (e.g. sigmoid or tanh) causes early layer gradients to shrink exponentially toward zero.",
             "Accepts gradients dying out, weights in early layers not updating, or derivative of sigmoid being less than 0.25."),
            ("ReLU activations eliminate vanishing gradients in the positive domain by maintaining a constant gradient of 1.",
             "Accepts non-saturating activation, linear positive regime, or avoiding saturation."),
            ("Residual skip connections allow gradients to flow directly through identity pathways without exponential attenuation.",
             "Accepts ResNet identity shortcuts, skip connections, or highway gradients.")
        ]
    ),
    (
        "Q009",
        "Explain the ROC curve and the difference between ROC-AUC and Precision-Recall AUC for imbalanced datasets.",
        "Machine Learning",
        [
            ("ROC plots True Positive Rate against False Positive Rate across all classification thresholds.",
             "Accepts TPR vs FPR or sensitivity versus one minus specificity curve."),
            ("ROC-AUC can be overly optimistic on highly imbalanced data because a large True Negative count suppresses the False Positive Rate.",
             "Accepts high TN diluting FPR, or dominant negative class masking poor minority detection."),
            ("Precision-Recall AUC focuses strictly on the positive class without incorporating True Negatives, making it far more informative for rare event detection.",
             "Accepts PR-AUC reflecting actual minority precision or being robust to heavy negative skew.")
        ]
    ),
    (
        "Q010",
        "Describe how Word2Vec Skip-Gram and CBOW architectures learn continuous vector representations.",
        "Machine Learning",
        [
            ("Continuous Bag of Words (CBOW) predicts a target center word given its surrounding context words.",
             "Accepts context-to-center prediction or averaging surrounding embeddings."),
            ("Skip-gram predicts context words given a single input center word, typically performing better on rare words.",
             "Accepts center-to-context prediction or window-based neighborhood prediction."),
            ("Both leverage negative sampling or hierarchical softmax to avoid computing expensive denominator sums over the entire vocabulary.",
             "Accepts contrastive negative word sampling or speeding up softmax partition function.")
        ]
    ),
    (
        "Q011",
        "What is Cross-Entropy Loss and why is it preferred over Mean Squared Error for classification?",
        "Machine Learning",
        [
            ("Cross-entropy measures the divergence between true one-hot probability distributions and predicted softmax probabilities.",
             "Accepts negative log-likelihood of correct class or Kullback-Leibler divergence from ground truth."),
            ("When paired with softmax or sigmoid, cross-entropy produces linear error gradients that do not saturate when predictions are wrong.",
             "Accepts gradients (p - y) not stalling, steep slopes for confident mistakes, or avoiding flat saturation regions."),
            ("MSE with sigmoid generates non-convex loss surfaces with vanishing gradients when the prediction is completely incorrect.",
             "Accepts local minima traps, flat derivative when sigmoid is near 0 or 1, or quadratic penalty being poorly calibrated.")
        ]
    ),
    (
        "Q012",
        "Explain Dropout and why it works effectively as an ensemble approximation.",
        "Machine Learning",
        [
            ("Randomly deactivates a fraction p of neuron activations during each forward training pass.",
             "Accepts masking neurons to zero with probability p during training."),
            ("Prevents co-adaptation of features by forcing individual neurons to learn useful representations independently of specific peer neurons.",
             "Accepts breaking feature interdependence, stopping neurons from relying on one another, or robust feature learning."),
            ("At inference time, all neurons are active and scaled by (1-p), acting as an implicit geometric average of exponentially many thinned subnetworks.",
             "Accepts ensemble of 2^N subnetworks, scaling activations at test time, or inverted dropout during training.")
        ]
    ),
    (
        "Q013",
        "Compare the Adam optimizer with standard Stochastic Gradient Descent (SGD) with momentum.",
        "Machine Learning",
        [
            ("SGD with momentum tracks an exponentially decaying moving average of past gradients to accelerate along consistent directions and dampen oscillations.",
             "Accepts velocity term, rolling downhill like a heavy ball, or smoothing out zig-zag paths."),
            ("Adam maintains both first moments (momentum) and second moments (uncentered variance of squared gradients) for adaptive per-parameter learning rates.",
             "Accepts tracking mean and variance of gradients, or scaling updates individually per weight."),
            ("Adam includes bias-correction terms to counter zero-initialization artifacts during initial training steps.",
             "Accepts warm-up correction factor (1 - beta^t) in early iterations.")
        ]
    ),
    (
        "Q014",
        "What is Low-Rank Adaptation (LoRA) for parameter-efficient LLM fine-tuning?",
        "Machine Learning",
        [
            ("Freezes pre-trained base model weights and decomposes the weight update matrix delta W into two low-rank matrices A and B (rank r << d).",
             "Accepts delta W = B * A with small inner dimension r, or keeping base model frozen."),
            ("Drastically reduces trainable parameters, GPU memory requirements, and storage overhead during fine-tuning.",
             "Accepts 90%+ memory savings, fine-tuning on consumer GPUs, or lightweight adapter checkpoints."),
            ("During inference, low-rank adapters can be folded directly back into base weights without incurring latency penalties.",
             "Accepts merging W_new = W_0 + B*A with zero inference overhead.")
        ]
    ),
    (
        "Q015",
        "Describe Byte-Pair Encoding (BPE) and its advantages over word-level and character-level tokenization.",
        "Machine Learning",
        [
            ("Iteratively merges the most frequently occurring adjacent pair of bytes or character tokens into a new vocabulary token.",
             "Accepts greedy frequency-based pair merging or subword grammar construction."),
            ("Eliminates out-of-vocabulary (OOV) errors by falling back to base characters or raw bytes for unseen words.",
             "Accepts handling unknown words gracefully without needing <UNK> tokens."),
            ("Balances vocabulary size and sequence length between verbose character representations and massive sparse word vocabularies.",
             "Accepts subword middle ground, handling morphological prefixes/suffixes, or compact sequence representation.")
        ]
    ),
    (
        "Q016",
        "What is Retrieval-Augmented Generation (RAG) and how does it reduce LLM hallucinations?",
        "Machine Learning",
        [
            ("Queries an external vector database or search index to retrieve relevant document passages using dense embedding similarity.",
             "Accepts semantic search over external knowledge base or embedding cosine lookup."),
            ("Injects retrieved context passages directly into the LLM prompt to ground the generation process.",
             "Accepts conditioning generator on factual chunks or supplying background facts in prompt."),
            ("Significantly reduces hallucination by requiring the model to cite and synthesize retrieved facts rather than solely recalling frozen parametric weights.",
             "Accepts grounding in real-time verified data or keeping answers anchored in source text.")
        ]
    ),
    (
        "Q017",
        "Explain the Reinforcement Learning from Human Feedback (RLHF) pipeline used in training aligned LLMs.",
        "Machine Learning",
        [
            ("Begins with Supervised Fine-Tuning (SFT) on curated high-quality demonstration prompts and responses.",
             "Accepts instruction tuning or initial human-demonstration training."),
            ("Trains a Reward Model on human preference pairs where annotators rank multiple model completions.",
             "Accepts preference learning, Elo-style ranking, or predicting scalar reward for responses."),
            ("Optimizes the policy model against the reward model using PPO or DPO while penalizing KL-divergence from the initial SFT model to prevent mode collapse.",
             "Accepts PPO reinforcement learning, DPO direct preference, or KL penalty to avoid reward hacking.")
        ]
    ),
    (
        "Q018",
        "Compare post-training quantization techniques: INT8 vs FP16 vs NormalFloat4 (NF4).",
        "Machine Learning",
        [
            ("Quantization maps high-precision floating point numbers to lower bit-width integers or specialized representations to shrink memory footprints.",
             "Accepts compressing FP32/FP16 weights to 8-bit or 4-bit representations."),
            ("INT8 uses uniform quantization with scale factors and zero points, potentially suffering precision loss on extreme activation outliers.",
             "Accepts uniform scaling, calibration datasets, or outlier clipping issues."),
            ("NF4 and modern 4-bit methods exploit normally distributed weight distributions to allocate quantiles with minimal theoretical information loss.",
             "Accepts quantile quantization, QLoRA NF4 format, or maintaining accuracy with 4-bit models.")
        ]
    ),
    (
        "Q019",
        "What are convolution operations and pooling layers in Convolutional Neural Networks (CNNs)?",
        "Machine Learning",
        [
            ("Convolutional kernels slide across spatial dimensions computing dot products to extract translation-invariant local features like edges and textures.",
             "Accepts sliding filter matrices, feature maps, or weight sharing across spatial grids."),
            ("Pooling layers (e.g. Max Pooling) downsample spatial resolutions to reduce computational load and increase effective receptive fields.",
             "Accepts sub-sampling, taking the maximum value in a window, or spatial compression."),
            ("Parameter sharing across locations provides spatial equivariance and drastically reduces parameter counts compared to fully connected layers.",
             "Accepts weight reuse across pixels, shift tolerance, or sparse connectivity.")
        ]
    ),
    (
        "Q020",
        "Explain the attention mask and causal masking in decoder-only language models like GPT.",
        "Machine Learning",
        [
            ("Causal masking sets upper-triangular attention logits to negative infinity before the softmax computation.",
             "Accepts masking future tokens, lower triangular attention matrix, or autoregressive constraint."),
            ("Prevents earlier token positions from accessing or attending to subsequent future tokens during training and generation.",
             "Accepts stopping information leakage from the future or maintaining left-to-right causal order."),
            ("Allows parallel teacher-forcing training across the entire sequence while matching autoregressive step-by-step inference.",
             "Accepts parallel training without lookahead cheating or next-token prediction consistency.")
        ]
    ),
    (
        "Q021",
        "What is the difference between supervised, unsupervised, and self-supervised learning?",
        "Machine Learning",
        [
            ("Supervised learning optimizes models using explicit external ground-truth target labels paired with input features.",
             "Accepts labeled data pairs (X, Y) or regression/classification targets."),
            ("Unsupervised learning discovers intrinsic patterns, clusterings, or latent distributions in unlabelled data.",
             "Accepts clustering like K-Means, dimensionality reduction like PCA, or density estimation."),
            ("Self-supervised learning generates pseudo-labels automatically from raw data structure, such as masked language modeling or contrastive image views.",
             "Accepts predicting masked tokens, next word prediction, or pretext tasks without human annotation.")
        ]
    ),
    (
        "Q022",
        "Describe K-Means clustering and discuss how to select the optimal number of clusters K.",
        "Machine Learning",
        [
            ("Iteratively alternates between assigning points to the nearest centroid and recalculating centroids as cluster means.",
             "Accepts assignment step and update step until convergence or inertia stabilization."),
            ("Elbow method evaluates within-cluster sum of squares (inertia) across K values to find the point of diminishing returns.",
             "Accepts plotting inertia versus K and identifying the bend/elbow."),
            ("Silhouette analysis measures how similar an object is to its own cluster compared to neighboring clusters.",
             "Accepts silhouette coefficients ranging from -1 to 1 or cohesion versus separation.")
        ]
    ),
    (
        "Q023",
        "Explain Principal Component Analysis (PCA) and its relationship to eigendecomposition.",
        "Machine Learning",
        [
            ("Projects high-dimensional data onto orthogonal axes that maximize variance and minimize reconstruction error.",
             "Accepts dimensionality reduction, finding directions of maximum spread, or decorrelating features."),
            ("Computes the covariance matrix of mean-centered data and calculates its eigenvectors and eigenvalues.",
             "Accepts eigendecomposition of X^T X or singular value decomposition (SVD)."),
            ("Principal components correspond to eigenvectors sorted by descending eigenvalues reflecting explained variance ratio.",
             "Accepts selecting top k eigenvectors corresponding to largest eigenvalues.")
        ]
    ),
    (
        "Q024",
        "What is Gradient Boosting and how does XGBoost optimize tree construction?",
        "Machine Learning",
        [
            ("Builds an ensemble sequentially where each new decision tree is trained to predict the pseudo-residuals or negative gradients of the previous ensemble.",
             "Accepts fitting errors of previous trees, sequential residual minimization, or boosting."),
            ("XGBoost uses second-order Taylor expansions of the loss function (gradient and hessian) for faster and more precise objective optimization.",
             "Accepts first and second derivatives, gradient and hessian calculation, or Newton-Raphson approximation."),
            ("Incorporates built-in tree regularization (L1/L2 on leaf weights) and optimal split finding via weighted quantile sketches.",
             "Accepts gamma and lambda pruning, handling missing values natively, or parallel histogram splitting.")
        ]
    ),
    (
        "Q025",
        "Explain early stopping and how validation loss divergence signals the onset of overfitting.",
        "Machine Learning",
        [
            ("Monitors model performance on an independent validation set after each training epoch.",
             "Accepts tracking validation loss or metric across epochs."),
            ("Training loss continuing to decrease while validation loss begins increasing indicates the model is memorizing training quirks rather than generalizing.",
             "Accepts the divergence gap between train and val loss curves."),
            ("Stops training when validation loss fails to improve for a pre-configured patience period and restores best checkpoint weights.",
             "Accepts patience counter, saving best checkpoint, or stopping before overtraining.")
        ]
    ),
    (
        "Q026",
        "What are generative adversarial networks (GANs) and how do the generator and discriminator interact?",
        "Machine Learning",
        [
            ("Generator synthesizes realistic data samples from latent random noise vectors.",
             "Accepts creating fake images/data from noise."),
            ("Discriminator acts as a binary classifier distinguishing between genuine real data and synthetic generator outputs.",
             "Accepts real versus fake classification or critic role."),
            ("Trained via a minimax two-player game where the generator attempts to fool the discriminator while the discriminator sharpens its detection ability.",
             "Accepts adversarial zero-sum game, Nash equilibrium, or competing objectives.")
        ]
    ),
    (
        "Q027",
        "Explain the concept of temperature in LLM sampling and its mathematical effect on logits.",
        "Machine Learning",
        [
            ("Divides raw unnormalized model logits by scalar temperature T before computing softmax probabilities.",
             "Accepts z_i / T in softmax formula or scaling logit distribution."),
            ("Low temperature (T -> 0) sharpens the probability distribution toward greedy argmax selection, yielding deterministic and conservative completions.",
             "Accepts greedy decoding, less randomness, or focusing probability on top token."),
            ("High temperature (T > 1) flattens the distribution toward uniformity, increasing diversity, creativity, and risk of incoherent text.",
             "Accepts flattening probabilities, increasing entropy, or promoting rare token exploration.")
        ]
    ),
    (
        "Q028",
        "What is contrastive learning and how does InfoNCE loss optimize representations?",
        "Machine Learning",
        [
            ("Pulls representations of positive augmented views of the same sample together while pushing representations of negative samples apart.",
             "Accepts maximizing similarity of positive pairs and minimizing similarity of negative pairs, as in SimCLR or CLIP."),
            ("InfoNCE formulates a multi-class classification objective where the positive pair must be identified among a set of negative distractors.",
             "Accepts categorical cross-entropy over cosine similarities or noise-contrastive estimation."),
            ("Maximizes a lower bound on the mutual information between different views of the underlying data.",
             "Accepts mutual information maximization or self-supervised feature clustering.")
        ]
    ),
    (
        "Q029",
        "Describe transfer learning and domain adaptation in deep learning.",
        "Machine Learning",
        [
            ("Reuses knowledge encoded in a model pre-trained on a massive general dataset to accelerate learning on a specialized target domain.",
             "Accepts initializing with pre-trained weights instead of random weights, e.g. ImageNet or foundational LLMs."),
            ("Fine-tunes higher task-specific layers while freezing lower generic feature extractors to prevent catastrophic forgetting.",
             "Accepts freezing early layers, updating classifier head, or gradual unfreezing."),
            ("Domain adaptation addresses covariate shift where source and target feature distributions differ while tasks remain aligned.",
             "Accepts aligning feature distributions across domains or adapting to new data distributions.")
        ]
    ),
    (
        "Q030",
        "What is catastrophic forgetting in continual learning and what techniques alleviate it?",
        "Machine Learning",
        [
            ("Occurs when a neural network overwrites previously acquired knowledge upon being trained sequentially on new distinct tasks.",
             "Accepts losing old skills when learning new ones or weights shifting away from past task minima."),
            ("Experience replay buffers store and interleave samples from historical tasks during new task optimization.",
             "Accepts rehearsal memory, memory buffers, or generative replay."),
            ("Regularization methods like Elastic Weight Consolidation (EWC) penalize updates to parameters critical to prior tasks based on Fisher Information.",
             "Accepts protecting important weights, quadratic penalties on critical parameters, or parameter isolation.")
        ]
    ),

    # --- Algorithms & Data Structures (25 questions) ---
    (
        "Q031",
        "Compare QuickSort and MergeSort: time complexities, space complexities, and stability.",
        "Algorithms",
        [
            ("QuickSort has O(N log N) average time but O(N^2) worst-case time with O(log N) in-place auxiliary stack space, and is typically unstable.",
             "Accepts pivot selection worst-case, in-place partitioning, or non-stable swapping."),
            ("MergeSort guarantees O(N log N) worst-case time but requires O(N) auxiliary memory for merging sub-arrays, and is stable.",
             "Accepts divide-and-conquer stability, extra buffer allocation, or consistent O(N log N)."),
            ("QuickSort is generally preferred for arrays due to superior cache locality, whereas MergeSort excels on linked lists or external sorting.",
             "Accepts cache performance of contiguous in-place swaps versus pointer-based merging.")
        ]
    ),
    (
        "Q032",
        "Explain how a Hash Map handles collisions and the significance of the load factor.",
        "Algorithms",
        [
            ("Hash collisions occur when distinct keys produce identical hash indices, resolved via separate chaining (linked lists/trees) or open addressing (probing).",
             "Accepts chaining with buckets, linear/quadratic probing, or Robin Hood hashing."),
            ("Load factor is the ratio of stored elements to total bucket capacity (N / C), indicating table density.",
             "Accepts threshold ratio determining how full the table is."),
            ("Exceeding the maximum load factor triggers resizing and rehashing of all entries into a larger array (usually 2x) to maintain amortized O(1) lookups.",
             "Accepts doubling capacity and rehashing elements to keep O(1) performance.")
        ]
    ),
    (
        "Q033",
        "What is the difference between a Binary Search Tree (BST) and a self-balancing tree like an AVL or Red-Black Tree?",
        "Algorithms",
        [
            ("A standard BST maintains the invariant that left descendants are smaller and right descendants are larger than the root node.",
             "Accepts left < node < right property."),
            ("Unbalanced BSTs can degenerate into O(N) skewed linked lists when inserting sorted data, ruining logarithmic search guarantees.",
             "Accepts skewed tree, worst-case linear search, or linked list degradation."),
            ("Self-balancing trees execute tree rotations during insertions and deletions to guarantee strict O(log N) height boundaries.",
             "Accepts AVL height balance difference <= 1, Red-Black color constraints, and tree rotations.")
        ]
    ),
    (
        "Q034",
        "Explain Dynamic Programming and compare top-down memoization with bottom-up tabulation.",
        "Algorithms",
        [
            ("Applies to problems exhibiting optimal substructure and overlapping subproblems by caching subproblem solutions.",
             "Accepts breaking into subproblems, reusing computed states, or avoiding redundant recursion."),
            ("Top-down memoization utilizes recursion with a cache/hash table to solve subproblems on demand.",
             "Accepts recursive approach with lookup table or decorator caching."),
            ("Bottom-up tabulation solves smaller subproblems iteratively in topological order, populating an array/table and avoiding recursion call stack overhead.",
             "Accepts iterative table filling, base-case up approach, or space optimization tricks.")
        ]
    ),
    (
        "Q035",
        "Compare Breadth-First Search (BFS) and Depth-First Search (DFS): traversal order, data structures, and optimal use cases.",
        "Algorithms",
        [
            ("BFS explores nodes level-by-level using a FIFO Queue, guaranteeing the shortest path in unweighted graphs.",
             "Accepts queue usage, level-order traversal, or shortest hop distance."),
            ("DFS explores as deeply as possible along each branch before backtracking, utilizing a LIFO Stack or recursion.",
             "Accepts stack usage, recursive backtracking, or exploring branches to leaf nodes."),
            ("BFS memory grows with the graph frontier width O(V), while DFS memory is bounded by tree depth O(H), making DFS ideal for topological sort or cycle detection.",
             "Accepts memory profile comparison or DFS for backtracking/connected components.")
        ]
    ),
    (
        "Q036",
        "Explain Dijkstra's shortest path algorithm and explain why it fails with negative edge weights.",
        "Algorithms",
        [
            ("Maintains a min-priority queue of tentative distances, greedily extracting the vertex with the lowest known distance and relaxing its outgoing edges.",
             "Accepts greedy selection of minimum distance node and edge relaxation via min-heap."),
            ("Runs in O((V + E) log V) time with an adjacency list and binary heap.",
             "Accepts heap-based complexity or standard graph runtime."),
            ("Fails with negative edges because once a node is visited/settled, Dijkstra assumes its shortest path is permanently finalized and never revisits it.",
             "Accepts greedy assumption violation, negative cycles, or need for Bellman-Ford.")
        ]
    ),
    (
        "Q037",
        "Describe the Min-Heap / Max-Heap data structure, its heap invariant, and heapify complexity.",
        "Algorithms",
        [
            ("A complete binary tree stored as an array where every parent node satisfies the comparison invariant relative to its children (parent <= children for min-heap).",
             "Accepts parent-child order property, array indexing 2i+1 and 2i+2, or complete tree."),
            ("Extract-min and Insert operations take O(log N) time by bubbling elements up or sifting down.",
             "Accepts push/pop in logarithmic time or sift-up and sift-down."),
            ("Building a heap from an arbitrary array of N elements (heapify) runs in O(N) linear time, not O(N log N).",
             "Accepts linear build-heap derivation or summing nodes times height.")
        ]
    ),
    (
        "Q038",
        "How would you design a Least Recently Used (LRU) Cache with O(1) get and put operations?",
        "Algorithms",
        [
            ("Combines a Hash Map for O(1) key lookups with a Doubly Linked List to maintain temporal access ordering.",
             "Accepts hash table pointing to doubly linked list nodes."),
            ("On 'get' or update, the accessed node is unlinked and moved to the head (most recently used) in O(1) pointer operations.",
             "Accepts moving accessed item to head or MRU position."),
            ("On 'put' when capacity is exceeded, the node at the tail (least recently used) is evicted from both list and hash map in O(1).",
             "Accepts removing tail node, deleting from hash map, and decrementing size.")
        ]
    ),
    (
        "Q039",
        "What is a Trie (Prefix Tree) and how does its lookup complexity compare to a Hash Map for prefix queries?",
        "Algorithms",
        [
            ("A tree structure where each node represents a character, and paths from the root represent strings or prefixes.",
             "Accepts character tree, prefix sharing, or n-ary tree with alphabet branching."),
            ("Lookup, insertion, and prefix search take O(L) time where L is the length of the string, independent of the total number of words N.",
             "Accepts O(word length) time complexity or prefix matching efficiency."),
            ("Unlike Hash Maps which cannot perform prefix matching without scanning all keys, Tries support autocomplete and prefix queries in O(prefix_length + K).",
             "Accepts prefix sub-tree traversal, autocomplete support, or lexicographical sorting.")
        ]
    ),
    (
        "Q040",
        "Explain bitwise operations and show how to check if an integer is a power of two in O(1) time.",
        "Algorithms",
        [
            ("A power of two in binary representation contains exactly one set bit ('1') with all other bits being zero (e.g. 8 is 1000).",
             "Accepts single bit set or binary power representations."),
            ("Subtracting 1 flips the least significant set bit and turns all trailing zeros to ones (e.g. 7 is 0111).",
             "Accepts n - 1 inverts trailing bits or changes binary pattern."),
            ("The bitwise condition '(n > 0) and (n & (n - 1) == 0)' evaluates to true if and only if n is a power of two in O(1) time.",
             "Accepts n & (n - 1) clears lowest set bit, leaving 0 for powers of two.")
        ]
    ),
    (
        "Q041",
        "Describe the Two-Pointer technique and state the conditions required for it to apply.",
        "Algorithms",
        [
            ("Maintains two index pointers that traverse an iterable in coordinated fashion (e.g., opposite ends moving inward or fast/slow pointers).",
             "Accepts left/right pointers, sliding pointers, or fast and slow runner pointers."),
            ("Requires monotonic properties, typically provided by a sorted array or structural linear sequence, to guarantee correct directionality decisions.",
             "Accepts sorted input requirement, monotonic sum behavior, or deterministic movement logic."),
            ("Reduces brute-force O(N^2) search spaces to O(N) linear time by eliminating redundant comparisons.",
             "Accepts linear scan speedup, single pass efficiency, or avoiding nested loops.")
        ]
    ),
    (
        "Q042",
        "What is Topological Sorting and under what conditions does a valid topological order exist?",
        "Algorithms",
        [
            ("A linear ordering of vertices such that for every directed edge (u, v), vertex u comes before vertex v in the ordering.",
             "Accepts dependency ordering, prerequisite sequencing, or scheduling order."),
            ("Only exists if and only if the directed graph is a Directed Acyclic Graph (DAG) with zero directed cycles.",
             "Accepts DAG requirement or cycle impossibility."),
            ("Can be computed via Kahn's algorithm (tracking in-degrees with a queue) or DFS post-order traversal with cycle detection in O(V + E) time.",
             "Accepts in-degree zero queue processing or reverse DFS finish times.")
        ]
    ),
    (
        "Q043",
        "Explain the Disjoint Set Union (Union-Find) data structure and the impact of path compression.",
        "Algorithms",
        [
            ("Tracks partitioned elements into disjoint subsets supporting 'find' (identify root representative) and 'union' (merge two sets).",
             "Accepts set partitioning, connected components tracking, or Kruskal's algorithm helper."),
            ("Path compression flattens tree structures during 'find' calls by attaching traversed nodes directly to the root representative.",
             "Accepts pointing traversed nodes directly to root or reducing tree height during lookups."),
            ("Combined with union by rank/size, operations achieve nearly O(1) amortized time, formally bounded by the inverse Ackermann function alpha(N).",
             "Accepts inverse Ackermann complexity, O(alpha(N)), or practically constant amortized time.")
        ]
    ),
    (
        "Q044",
        "Explain the Sliding Window algorithmic pattern and how to identify problems suitable for it.",
        "Algorithms",
        [
            ("Maintains a continuous contiguous subarray/substring window that expands its right boundary and contracts its left boundary dynamically.",
             "Accepts dynamic two-pointer window over contiguous sequence."),
            ("Applies to optimization or search problems over contiguous sequences where subproblem validity exhibits monotonicity with respect to window resizing.",
             "Accepts contiguous subarray problems, max/min sum of length k, or longest substring with k unique elements."),
            ("Achieves O(N) time complexity by updating aggregate state incrementally as elements enter and exit the window rather than recalculating from scratch.",
             "Accepts incremental state updates or avoiding O(N^2) window recomputations.")
        ]
    ),
    (
        "Q045",
        "What is amortized time complexity and how does it apply to dynamic array resizings?",
        "Algorithms",
        [
            ("Amortized analysis averages the running time of operations over a sequence of actions, ensuring that occasional expensive operations do not dominate aggregate performance.",
             "Accepts average cost per operation over worst-case sequence or aggregate method."),
            ("Dynamic arrays allocate double capacity when full (geometric resizing), copying N elements in O(N) time.",
             "Accepts doubling array size, copying over existing items, or O(N) reallocation."),
            ("Because the expensive O(N) copy occurs only after N insertions of cost O(1), the total cost across N operations is O(N), yielding amortized O(1) per append.",
             "Accepts O(1) amortized append, accounting/potential method explanation, or geometric series convergence.")
        ]
    ),
    (
        "Q046",
        "Compare Bellman-Ford and Floyd-Warshall algorithms for shortest path calculations.",
        "Algorithms",
        [
            ("Bellman-Ford computes single-source shortest paths in graphs with negative edge weights in O(V * E) time by relaxing all edges V-1 times.",
             "Accepts single source, negative edge handling, edge relaxation V-1 times."),
            ("Bellman-Ford detects negative cycles if an edge can still be relaxed on the V-th iteration.",
             "Accepts negative weight cycle detection rule."),
            ("Floyd-Warshall computes all-pairs shortest paths using dynamic programming over intermediate vertices in O(V^3) time and O(V^2) space.",
             "Accepts all-pairs shortest path, matrix dynamic programming, or triple nested loop.")
        ]
    ),
    (
        "Q047",
        "Describe the Boyer-Moore Majority Vote algorithm and its time and space bounds.",
        "Algorithms",
        [
            ("Finds the majority element that appears strictly more than N/2 times in an array in O(N) time and O(1) auxiliary space.",
             "Accepts linear time, constant space majority finder."),
            ("Maintains a candidate element and a counter, incrementing when matching the candidate and decrementing when differing.",
             "Accepts counter increment/decrement mechanism or pair-wise cancellation."),
            ("When counter reaches zero, the current element becomes the new candidate; requires a second verification pass if a majority element is not guaranteed.",
             "Accepts candidate reset at zero count and second pass verification.")
        ]
    ),
    (
        "Q048",
        "Explain how to detect a cycle in a linked list using Floyd's Tortoise and Hare algorithm.",
        "Algorithms",
        [
            ("Initializes a slow pointer moving one node per step and a fast pointer moving two nodes per step.",
             "Accepts slow (1x) and fast (2x) pointer movement."),
            ("If the linked list contains a cycle, the fast pointer will eventually wrap around and meet the slow pointer within the loop.",
             "Accepts fast catches up to slow or collision inside cycle."),
            ("To locate the cycle start, reset one pointer to the list head and advance both at 1 step per iteration; their intersection is the cycle entrance.",
             "Accepts resetting one pointer to head and stepping at equal speed to find entrance.")
        ]
    ),
    (
        "Q049",
        "What is the difference between counting sort, radix sort, and comparison-based sorting lower bounds?",
        "Algorithms",
        [
            ("Comparison-based sorting algorithms (like MergeSort or QuickSort) are mathematically bounded by Omega(N log N) decision tree height limits.",
             "Accepts N log N information-theoretic lower bound for comparisons."),
            ("Counting sort counts occurrences of each distinct integer key, achieving O(N + K) linear time when range K is small.",
             "Accepts frequency array, non-comparison sorting, or O(N + K) runtime."),
            ("Radix sort processes keys digit-by-digit or byte-by-byte using a stable sub-sort (e.g. counting sort), achieving O(d * (N + K)) time for d-digit keys.",
             "Accepts digit-by-digit sorting, LSD/MSD stable passes, or linear sorting for fixed bit widths.")
        ]
    ),
    (
        "Q050",
        "Explain the A* search algorithm and the admissibility condition of heuristics.",
        "Algorithms",
        [
            ("Selects paths minimizing total estimated cost f(n) = g(n) + h(n), where g(n) is the exact cost from start and h(n) is estimated cost to goal.",
             "Accepts f = g + h formula, cost so far plus heuristic estimate to target."),
            ("An admissible heuristic never overestimates the true minimal cost to reach the goal (h(n) <= h*(n)).",
             "Accepts optimistic heuristic, never overestimating cost, or admissible definition."),
            ("Admissibility (and consistency/monotonicity in graphs) guarantees that A* finds the provably optimal shortest path.",
             "Accepts optimal path guarantee or consistency preventing node re-expansions.")
        ]
    ),
    (
        "Q051",
        "What is the Segment Tree data structure and what operations does it optimize?",
        "Algorithms",
        [
            ("A binary tree representing intervals or segments of an array where internal nodes store aggregate associative values (e.g., sum, min, max).",
             "Accepts interval tree, array segmentation, or range query tree."),
            ("Executes arbitrary range queries (e.g. range minimum or range sum) in O(log N) time.",
             "Accepts range query logarithmic time or merging segment results."),
            ("Supports point updates and range updates (via lazy propagation) in O(log N) time, outperforming naive array scans.",
             "Accepts logarithmic point/range update and lazy propagation.")
        ]
    ),
    (
        "Q052",
        "Explain the Kadane algorithm for the Maximum Subarray Sum problem.",
        "Algorithms",
        [
            ("Iterates through the array maintaining a running local maximum sum ending at the current index.",
             "Accepts current_max ending at i or local sum tracking."),
            ("Decides at each element whether to extend the existing subarray or start a fresh subarray: current_max = max(num, current_max + num).",
             "Accepts reset when running sum drops below zero or element itself is greater."),
            ("Tracks the global maximum across all indices, achieving O(N) time and O(1) auxiliary space.",
             "Accepts linear single-pass, constant extra memory, or global max update.")
        ]
    ),
    (
        "Q053",
        "Describe QuickSelect and how it finds the k-th smallest element in an unordered list.",
        "Algorithms",
        [
            ("Uses the partitioning logic of QuickSort around a chosen pivot element.",
             "Accepts pivot partitioning or dividing into left/right partitions."),
            ("Recurses or iterates into only the one partition containing index k, discarding the other half.",
             "Accepts single-sided recursion or ignoring the irrelevant half."),
            ("Achieves O(N) average time complexity, though worst-case is O(N^2) unless median-of-medians pivot selection is used.",
             "Accepts linear average time, O(N) recurrence T(N) = T(N/2) + O(N), and worst-case quadratic.")
        ]
    ),
    (
        "Q054",
        "What is a Monotonic Stack and what class of problems does it solve efficiently?",
        "Algorithms",
        [
            ("A stack whose elements are strictly maintained in increasing or decreasing order by popping elements that violate the order invariant.",
             "Accepts stack maintaining ordered elements by popping violators."),
            ("Used to solve Next Greater Element, Daily Temperatures, or Largest Rectangle in Histogram in O(N) linear time.",
             "Accepts next greater/smaller element queries or histogram area calculation."),
            ("Every element is pushed and popped at most once, guaranteeing linear amortized complexity.",
             "Accepts each item pushed/popped once, amortized O(N) runtime.")
        ]
    ),
    (
        "Q055",
        "Explain the concept of Branch and Bound and how it differs from pure Backtracking.",
        "Algorithms",
        [
            ("Systematically explores the solution space of combinatorial optimization problems by organizing them into a state-space tree.",
             "Accepts state-space tree exploration for optimization problems."),
            ("Calculates upper or lower mathematical bounds on the objective function at each node.",
             "Accepts computing bound on potential solution quality at sub-tree root."),
            ("Prunes entire sub-trees whose bound proves they cannot produce a solution better than the best solution found so far.",
             "Accepts pruning sub-optimal branches, bounding vs feasibility backtracking, or branch-and-cut.")
        ]
    ),

    # --- System Design & Distributed Systems (25 questions) ---
    (
        "Q056",
        "Explain the CAP Theorem and discuss the tradeoffs when a network partition occurs.",
        "System Design",
        [
            ("CAP states a distributed system can guarantee at most two of Consistency, Availability, and Partition Tolerance simultaneously.",
             "Accepts CAP definition or impossibility of all three."),
            ("In physical distributed networks, Partition Tolerance (P) is mandatory because network cables, switches, and nodes can inevitably fail.",
             "Accepts network partitions are unavoidable in real distributed infrastructure."),
            ("When a partition occurs, an architect must choose between Consistency (CP, rejecting stale writes/reads) or Availability (AP, serving stale or divergent reads).",
             "Accepts CP vs AP tradeoff, returning error vs returning stale data.")
        ]
    ),
    (
        "Q057",
        "What is Consistent Hashing and how does it prevent massive data remapping in distributed caches?",
        "System Design",
        [
            ("Maps both cache nodes and data keys onto a circular hash ring (e.g. 0 to 2^32 - 1).",
             "Accepts circular hash ring representation or modular keyspace mapping."),
            ("Keys are routed to the first node encountered moving clockwise around the ring from the key's hash position.",
             "Accepts assigning key to first server clockwise on the ring."),
            ("Adding or removing a server relocates only K/N keys on average rather than remapping all keys as standard modulo hashing does.",
             "Accepts minimal key remapping, virtual nodes for uniform load distribution, or avoiding cache thundering herds.")
        ]
    ),
    (
        "Q058",
        "Compare Database Sharding and Master-Replica Replication: goals and architectural complexities.",
        "System Design",
        [
            ("Replication copies identical data across multiple nodes to increase read throughput and provide high availability/failover.",
             "Accepts read scaling, backup replicas, or primary-secondary failover."),
            ("Sharding horizontally partitions data rows across multiple independent database instances based on a shard key to scale write capacity and storage volume.",
             "Accepts horizontal partitioning, splitting data by user_id/tenant, or scaling writes beyond single node limits."),
            ("Sharding introduces complex cross-shard joins, distributed two-phase transactions, and resharding rebalances.",
             "Accepts distributed transactions, scatter-gather queries, or shard key hotspots.")
        ]
    ),
    (
        "Q059",
        "Explain the difference between Monolithic and Microservices architectures, including operational tradeoffs.",
        "System Design",
        [
            ("Monolith combines all domain capabilities, shared database models, and deployment artifacts into a single unified codebase.",
             "Accepts single deployable unit, shared codebase, or single relational database."),
            ("Microservices partition system functionality into independently deployable, loosely coupled services communicating via network APIs (HTTP/gRPC/events).",
             "Accepts independent services, bounded contexts, or decoupled deployments."),
            ("Microservices improve autonomous team velocity and domain scalability, but drastically increase operational complexity, network latency, distributed tracing, and eventual consistency challenges.",
             "Accepts distributed debugging, network overhead, CI/CD complexity, or eventual consistency.")
        ]
    ),
    (
        "Q060",
        "Compare Apache Kafka and RabbitMQ: message delivery semantics, storage models, and ideal use cases.",
        "System Design",
        [
            ("Kafka is an append-only distributed commit log where consumers track their own offsets and messages are retained persistently on disk.",
             "Accepts distributed log, pull-based consumer offsets, durable stream retention."),
            ("RabbitMQ is a message broker with complex AMQP routing exchanges where messages are acknowledged and deleted from the queue upon consumption.",
             "Accepts push-based broker, exchange routing, queue draining after ack."),
            ("Kafka is optimized for high-throughput event streaming, replayability, and log analytics, while RabbitMQ excels at granular task queuing and complex routing topologies.",
             "Accepts streaming throughput vs granular task queue routing.")
        ]
    ),
    (
        "Q061",
        "Describe Cache-Aside (Lazy Loading) versus Write-Through and Write-Back caching strategies.",
        "System Design",
        [
            ("Cache-Aside checks the cache first; on a miss, reads from the database, writes data into the cache, and returns it to the client.",
             "Accepts lazy loading on cache miss, application-managed caching."),
            ("Write-Through writes synchronously to both cache and underlying database simultaneously before acknowledging success.",
             "Accepts dual synchronous write, strong cache consistency, write latency penalty."),
            ("Write-Back (Write-Behind) writes immediately to cache and asynchronously flushes batches to the database, maximizing write performance but risking data loss upon cache crash.",
             "Accepts async DB flush, low latency writes, risk of data loss on power failure.")
        ]
    ),
    (
        "Q062",
        "Explain Rate Limiting algorithms: Token Bucket versus Leaky Bucket versus Sliding Window Log.",
        "System Design",
        [
            ("Token Bucket replenishes tokens at a constant rate into a bucket of fixed capacity; requests consume tokens and allow bursts up to capacity.",
             "Accepts token accumulation, constant refill rate, burst tolerance."),
            ("Leaky Bucket processes incoming requests at a smooth, strictly constant outflow rate, buffering bursts in a queue or discarding overflow.",
             "Accepts steady outflow rate, smoothing traffic spikes, FIFO request drain."),
            ("Sliding Window Log records timestamps of each request in a sorted set, pruning timestamps older than the window to provide exact boundary protection at higher memory cost.",
             "Accepts timestamp log, exact sliding window, Redis sorted sets implementation.")
        ]
    ),
    (
        "Q063",
        "How do you implement a distributed lock using Redis (Redlock) or ZooKeeper?",
        "System Design",
        [
            ("Requires atomic lock acquisition using an exclusive key creation with time-to-live expiration (e.g., SET resource_id random_val NX PX ttl).",
             "Accepts atomic SETNX with TTL or ephemeral sequential znode."),
            ("Release must verify that the lock value matches the unique client identifier using a Lua script to avoid releasing another client's acquired lock.",
             "Accepts Lua script atomicity check, UUID owner verification, or preventing releasing expired lock."),
            ("Redlock acquires locks across an independent majority of N Redis nodes to guard against master-replica failover race conditions.",
             "Accepts majority consensus (N/2 + 1), clock drift considerations, or ZooKeeper session expiration.")
        ]
    ),
    (
        "Q064",
        "Compare Layer 4 (Transport) and Layer 7 (Application) Load Balancing.",
        "System Design",
        [
            ("Layer 4 operates at TCP/UDP transport level, routing packets based on IP addresses and ports without inspecting application payload.",
             "Accepts TCP routing, IP/port forwarding, no SSL termination, high raw throughput."),
            ("Layer 7 operates at application level (HTTP/HTTPS/gRPC), inspecting headers, cookies, HTTP methods, and URL paths.",
             "Accepts HTTP inspection, path-based routing, header filtering, cookie affinity."),
            ("Layer 7 enables intelligent routing, SSL termination, and rate limiting, but consumes significantly more CPU resources per connection than Layer 4.",
             "Accepts TLS termination, content-based routing, higher compute overhead.")
        ]
    ),
    (
        "Q065",
        "What is API Idempotency and how do you implement it for distributed financial transactions?",
        "System Design",
        [
            ("An operation is idempotent if executing it multiple times produces the identical side-effect and outcome as executing it once.",
             "Accepts repeated calls yield same state or safe retries."),
            ("Clients generate a unique Idempotency Key (e.g. UUID) transmitted in HTTP headers on mutation requests.",
             "Accepts Idempotency-Key header or unique transaction token."),
            ("The server records the key and execution state in an atomic database store with unique constraints, returning cached responses on duplicate requests.",
             "Accepts database unique constraint, returning saved response on replay, or atomic check-and-insert.")
        ]
    ),
    (
        "Q066",
        "Explain the Outbox Pattern for reliable event publishing in microservices.",
        "System Design",
        [
            ("Addresses the dual-write problem where updating a database and publishing an event to a message broker cannot share a local transaction.",
             "Accepts dual write inconsistency, avoiding partial failure between DB and broker."),
            ("Persists domain state changes and outgoing event records into an 'outbox' table within the identical local ACID database transaction.",
             "Accepts writing event to outbox table inside same database commit."),
            ("An asynchronous message relay (or CDC tool like Debezium) polls or tails the database transaction log to publish events to the broker with at-least-once guarantees.",
             "Accepts CDC log tailing, Debezium, polling publisher, at-least-once delivery.")
        ]
    ),
    (
        "Q067",
        "How do Content Delivery Networks (CDNs) optimize content delivery and handle cache invalidation?",
        "System Design",
        [
            ("Distributes edge cache servers geographically close to end users to serve static and cached dynamic assets with low latency.",
             "Accepts edge caching, point of presence (PoP), reduced round-trip time."),
            ("Employs HTTP caching headers like Cache-Control, max-age, ETag, and stale-while-revalidate to control client and edge lifetimes.",
             "Accepts Cache-Control headers, ETags, TTLs, conditional requests."),
            ("Supports active cache purging (via API URL/tag invalidation) and versioned asset URLs (cache busting via content hashes) for instant updates.",
             "Accepts cache busting hashes, programmatic purge API, surrogate keys.")
        ]
    ),
    (
        "Q068",
        "Compare ACID transactional guarantees in relational databases with the BASE model in distributed databases.",
        "System Design",
        [
            ("ACID guarantees Atomicity (all-or-nothing), Consistency (schema invariants), Isolation (concurrent safety), and Durability (committed persistence).",
             "Accepts ACID breakdown and strict transactional guarantees."),
            ("BASE represents Basically Available, Soft state, and Eventual consistency, prioritizing continuous uptime over instantaneous global correctness.",
             "Accepts BASE breakdown, soft state, eventual synchronization."),
            ("Relational systems favor ACID for financial/inventory integrity, whereas highly distributed NoSQL systems embrace BASE to achieve horizontal scale and fault tolerance.",
             "Accepts strong consistency vs high availability horizontal scaling tradeoff.")
        ]
    ),
    (
        "Q069",
        "Explain Database Indexing with B-Trees and compare them with Hash Indexes.",
        "System Design",
        [
            ("B-Trees (and B+ Trees) are balanced search trees where nodes store multiple keys and children, optimized for disk block reads with high fan-out.",
             "Accepts balanced multi-way tree, high fan-out, disk page alignment."),
            ("B+ Trees store actual data pointers exclusively in leaf nodes linked sequentially, enabling efficient range scans (e.g. BETWEEN or inequalities).",
             "Accepts range scan efficiency, leaf node linked list, O(log N) operations."),
            ("Hash indexes provide O(1) point lookups for exact matches ('=') but cannot serve range queries or partial prefix matches.",
             "Accepts exact match only, lack of range scan support, hash bucket lookup.")
        ]
    ),
    (
        "Q070",
        "Describe the Circuit Breaker design pattern in distributed microservices.",
        "System Design",
        [
            ("Prevents cascading failures by detecting upstream service errors and failing fast rather than wasting system resources on doomed requests.",
             "Accepts stopping cascading failures, fail-fast protection, resilience pattern."),
            ("Maintains three states: Closed (normal operations), Open (tripped after error threshold exceeded, calls fail immediately or return fallback), and Half-Open.",
             "Accepts closed, open, and half-open state machine explanation."),
            ("Half-Open state allows a trial batch of requests to pass through to test if the dependent service has recovered before fully closing the circuit.",
             "Accepts trial requests, checking if service healed, resetting error counters.")
        ]
    ),
    (
        "Q071",
        "Explain the Leader-Follower (Master-Slave) consensus pattern versus Leaderless replication (Dynamo-style).",
        "System Design",
        [
            ("Leader-based systems designate a single node to sequence and process all write operations, streaming changes to follower replicas.",
             "Accepts single write master, follower replication, centralized sequencer."),
            ("Leaderless systems (like Cassandra/Dynamo) allow any node to accept writes, relying on client-side or coordinator fanout across replicas.",
             "Accepts any node accepts writes, peer-to-peer, decentralized."),
            ("Leaderless systems use quorum reads and writes (R + W > N) combined with read repair and anti-entropy to guarantee strong consistency.",
             "Accepts quorum condition R + W > N, sloppy quorums, hinted handoff, read repair.")
        ]
    ),
    (
        "Q072",
        "What is Database Connection Pooling and why is it crucial for application performance?",
        "System Design",
        [
            ("Maintains a pre-initialized cache of reusable physical database connections rather than opening and closing a TCP/auth handshake per query.",
             "Accepts pre-warmed connection pool, reusing open sockets."),
            ("Establishing database connections involves expensive TCP handshakes, TLS negotiation, authentication, and database process memory allocation.",
             "Accepts overhead of TCP setup, TLS handshake, database process fork cost."),
            ("Connection pooling limits concurrency to protect the database engine from context switching thrashing and out-of-memory crashes under load spikes.",
             "Accepts backpressure, capping concurrent DB sessions, preventing DB starvation.")
        ]
    ),
    (
        "Q073",
        "Explain Event Sourcing and Command Query Responsibility Segregation (CQRS).",
        "System Design",
        [
            ("Event Sourcing persists every change to application state as an immutable sequence of domain events rather than mutating current record values.",
             "Accepts append-only event stream, immutable event log, state reconstruction via event replay."),
            ("CQRS strictly separates the write model (handling commands and business validation) from read models (optimized for fast queries).",
             "Accepts separating command mutations from query reads, dedicated read projections."),
            ("Provides complete audit trails, time-travel debugging, and independent read/write scaling at the expense of eventual consistency and projection lag.",
             "Accepts audit log, temporal queries, eventual consistency between command and query sides.")
        ]
    ),
    (
        "Q074",
        "Describe WebSockets versus Long Polling versus Server-Sent Events (SSE) for real-time communication.",
        "System Design",
        [
            ("WebSockets establishes a full-duplex, bidirectional persistent TCP connection over a single socket, ideal for high-frequency interactive apps.",
             "Accepts full-duplex, bidirectional socket, chat/gaming usage."),
            ("Server-Sent Events (SSE) provides a unidirectional streaming channel from server to client over standard HTTP, with automatic reconnection and lightweight framing.",
             "Accepts one-way server-to-client streaming, HTTP-based, LLM token streaming."),
            ("Long Polling simulates real-time by keeping an HTTP request open until the server has new data, incurring heavy HTTP header overhead and latency per round-trip.",
             "Accepts hanging HTTP requests, reconnecting after response, legacy polling fallback.")
        ]
    ),
    (
        "Q075",
        "How do you design a URL Shortener service (like Bitly) to handle massive scale?",
        "System Design",
        [
            ("Generates compact short URLs using Base62 encoding (a-z, A-Z, 0-9) derived from a distributed unique 64-bit ID generator (e.g. Snowflake or DB auto-increment).",
             "Accepts Base62 encoding, unique ID generation, 7-character hash."),
            ("Redirects clients via HTTP 301 (Permanent Redirect, aggressive browser cache) or 302/307 (Temporary Redirect, to track analytics per click).",
             "Accepts 301 vs 302 redirect tradeoffs, analytics tracking."),
            ("Employs distributed in-memory caches (Redis/Memcached) for hot URL mappings and partitioned NoSQL/RDBMS storage with read replicas to handle massive read-to-write ratios.",
             "Accepts caching hot keys, 100:1 read-to-write ratio, horizontal sharding.")
        ]
    ),
    (
        "Q076",
        "Explain the Two-Phase Commit (2PC) protocol for distributed transactions and its vulnerabilities.",
        "System Design",
        [
            ("Phase 1 (Prepare): Coordinator asks all participant nodes if they can commit; participants acquire locks and write to undo/redo logs, voting YES or NO.",
             "Accepts prepare phase, voting, locking resources."),
            ("Phase 2 (Commit/Abort): If all voted YES, coordinator sends COMMIT; if any voted NO or timed out, coordinator sends ROLLBACK.",
             "Accepts commit or rollback broadcast."),
            ("Vulnerable to blocking: if the coordinator crashes during the commit phase after participants vote YES, participants remain locked indefinitely waiting for resolution.",
             "Accepts blocking protocol, single point of failure coordinator, resource locking.")
        ]
    ),
    (
        "Q077",
        "Describe Disaster Recovery strategies: RPO and RTO, and Active-Active versus Active-Passive deployments.",
        "System Design",
        [
            ("Recovery Point Objective (RPO) defines the maximum acceptable data loss measured in time between backup/sync and failure.",
             "Accepts maximum data loss window, time since last backup."),
            ("Recovery Time Objective (RTO) defines the maximum acceptable downtime to restore service operations after an incident.",
             "Accepts maximum downtime allowed, time to recover."),
            ("Active-Passive routes all traffic to a primary site while maintaining a standby site for failover; Active-Active serves live traffic simultaneously across multiple geographic regions with real-time replication.",
             "Accepts active-passive cold/warm standby vs active-active multi-region load balancing.")
        ]
    ),
    (
        "Q078",
        "Explain Log-Structured Merge (LSM) Trees and compare their write performance with B-Trees.",
        "System Design",
        [
            ("Writes are appended sequentially to a Write-Ahead Log (WAL) and stored in an in-memory sorted structure (MemTable).",
             "Accepts sequential WAL append and in-memory MemTable (skip list or red-black tree)."),
            ("When full, MemTables are flushed to disk as immutable sorted string tables (SSTables); background compaction merges SSTables to reclaim space.",
             "Accepts flushing to SSTables, background compaction, merging sorted runs."),
            ("LSM Trees achieve superior write throughput by converting random disk writes into fast sequential writes, at the cost of read amplification resolved via Bloom filters.",
             "Accepts high write throughput, sequential I/O, Bloom filters for fast negative lookups.")
        ]
    ),
    (
        "Q079",
        "What is Distributed Tracing and how do Trace IDs and Span IDs propagate across microservice boundaries?",
        "System Design",
        [
            ("Tracks the end-to-end lifecycle of a client request across distributed service calls to diagnose performance bottlenecks and errors.",
             "Accepts tracking request path across services, OpenTelemetry, Jaeger."),
            ("A globally unique Trace ID identifies the entire workflow, while Span IDs represent individual units of work within specific services.",
             "Accepts Trace ID for whole transaction, Span ID for individual service hop."),
            ("Context is propagated across network boundaries by injecting trace headers (e.g. W3C traceparent) into HTTP/gRPC request headers.",
             "Accepts HTTP header injection, context propagation, parent-child span hierarchy.")
        ]
    ),
    (
        "Q080",
        "Explain the Thundering Herd (Cache Stampede) problem and how to mitigate it.",
        "System Design",
        [
            ("Occurs when a popular cached key expires and hundreds or thousands of concurrent requests simultaneously hit the backend database to regenerate the value.",
             "Accepts cache expiration leading to massive concurrent DB queries, overloading database."),
            ("Mitigated via distributed mutex locking (single-flight) where only the first request regenerates the cache while others wait.",
             "Accepts mutex lock, singleflight pattern, promise sharing."),
            ("Probabilistic early recomputation (XFetch) or background pre-warming refreshes the cache item before its actual TTL expiration.",
             "Accepts background pre-refresh, probabilistic early expiration, soft TTL.")
        ]
    ),

    # --- Databases & Operating Systems (20 questions) ---
    (
        "Q081",
        "Compare SQL (Relational) and NoSQL databases: data models, scaling approaches, and schema constraints.",
        "Databases & OS",
        [
            ("SQL databases use structured tables with fixed schemas, enforcing relational integrity via primary and foreign keys.",
             "Accepts tabular structure, relational joins, strict schema definition."),
            ("NoSQL databases employ flexible semi-structured data models (document, key-value, column-family, graph) supporting schema-on-read.",
             "Accepts JSON document, key-value store, wide-column, dynamic schemas."),
            ("SQL typically scales vertically (compute/storage upgrades) and read-scales via replicas, whereas NoSQL is engineered for horizontal sharding across commodity clusters.",
             "Accepts vertical scaling vs horizontal distribution, scale-up vs scale-out.")
        ]
    ),
    (
        "Q082",
        "Explain SQL Transaction Isolation Levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable.",
        "Databases & OS",
        [
            ("Read Uncommitted permits dirty reads (reading uncommitted changes from concurrent transactions).",
             "Accepts dirty reads permitted, lowest isolation level."),
            ("Read Committed prevents dirty reads, but allows non-repeatable reads (re-reading a row returns altered data if committed concurrently).",
             "Accepts no dirty reads, non-repeatable read vulnerability."),
            ("Repeatable Read ensures rows read once return identical values within the transaction, though phantom rows (newly inserted matching rows) can appear unless MVCC/range locks prevent them.",
             "Accepts consistent snapshot of rows read, phantom read vulnerability."),
            ("Serializable provides complete isolation as if transactions executed serially, preventing phantoms via strict two-phase locking (2PL) or Serializable Snapshot Isolation (SSI).",
             "Accepts strict serial execution semantics, highest isolation, SSI or 2PL.")
        ]
    ),
    (
        "Q083",
        "What are the four necessary conditions for Deadlock and how can systems prevent or recover from them?",
        "Databases & OS",
        [
            ("Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait (Coffman conditions).",
             "Accepts all 4 Coffman conditions named or accurately described."),
            ("Deadlock prevention eliminates at least one condition, such as imposing a global linear ordering on lock acquisitions to eliminate circular wait.",
             "Accepts acquiring locks in fixed order, pre-allocating all resources, or resource preemption."),
            ("Deadlock detection constructs resource-allocation wait-for graphs to detect cycles, recovering by terminating or rolling back a victim transaction.",
             "Accepts wait-for graph cycle detection, killing victim transaction, transaction abort.")
        ]
    ),
    (
        "Q084",
        "Compare a Process and a Thread, and explain common Inter-Process Communication (IPC) mechanisms.",
        "Databases & OS",
        [
            ("A process is an isolated execution instance with its own virtual address space, memory descriptors, file handles, and security context.",
             "Accepts independent memory space, process isolation, heavy context switch."),
            ("Threads are lightweight execution units within a process sharing the same address space, code segment, and heap, but retaining independent stacks and registers.",
             "Accepts shared heap/memory, individual stack and registers, lightweight context switch."),
            ("IPC mechanisms enable processes to exchange data across isolated address spaces via pipes, shared memory, message queues, signals, and UNIX domain sockets.",
             "Accepts pipes, shared memory, sockets, message queues, signals.")
        ]
    ),
    (
        "Q085",
        "Explain Virtual Memory, Paging, and Page Fault handling in modern operating systems.",
        "Databases & OS",
        [
            ("Virtual memory abstracts physical RAM by providing each process with an expansive, contiguous, and protected virtual address space.",
             "Accepts memory abstraction, address space isolation, memory protection."),
            ("Divides memory into fixed-size chunks called pages, mapped to physical frames via page tables managed by the Memory Management Unit (MMU) and TLB.",
             "Accepts virtual pages, physical frames, page table, MMU, TLB lookup."),
            ("A page fault occurs when accessing an address not present in physical RAM; the OS kernel traps the interrupt, loads the required page from disk swap, updates the page table, and restarts the instruction.",
             "Accepts trap interrupt, fetching from swap disk, updating page table entry.")
        ]
    ),
    (
        "Q086",
        "Compare Optimistic Concurrency Control (OCC) and Pessimistic Concurrency Control.",
        "Databases & OS",
        [
            ("Pessimistic concurrency locks records immediately upon reading to prevent any concurrent modifications until transaction completion.",
             "Accepts SELECT FOR UPDATE, exclusive locks, blocking concurrent writers."),
            ("Optimistic concurrency assumes conflicts are rare, allowing transactions to read and modify data without locking, checking for conflicts at commit time.",
             "Accepts lock-free reads, version number checks, timestamp verification at commit."),
            ("Optimistic concurrency excels in read-heavy low-contention environments; pessimistic concurrency is superior in high-contention write environments where frequent rollback retries waste throughput.",
             "Accepts low contention vs high contention performance tradeoffs.")
        ]
    ),
    (
        "Q087",
        "What is Write-Ahead Logging (WAL) and how does it guarantee durability and crash recovery?",
        "Databases & OS",
        [
            ("Requires all transaction modifications to be logged sequentially to non-volatile disk before the corresponding data pages are flushed from memory.",
             "Accepts write to log before modifying data pages, append-only disk log."),
            ("Ensures durability: if the system crashes, committed transactions present in the WAL can be redone (REDO phase) to recover state.",
             "Accepts REDO committed changes, replaying log after crash."),
            ("Uncommitted or partial transactions aborted during a crash can be undone (UNDO phase) by reading log records backwards to maintain atomicity.",
             "Accepts UNDO uncommitted operations, rollback via log, ARIES recovery algorithm.")
        ]
    ),
    (
        "Q088",
        "Describe CPU Scheduling algorithms: Round Robin versus Shortest Job First versus Multi-Level Feedback Queues.",
        "Databases & OS",
        [
            ("Round Robin assigns fixed time quantum slices to processes in a circular FIFO queue, providing fairness and fast response times.",
             "Accepts time quantum slices, preemptive circular scheduling, responsive interactive performance."),
            ("Shortest Job First (SJF) schedules the process with the smallest execution burst next, mathematically minimizing average waiting time but risking starvation of long jobs.",
             "Accepts optimal average wait time, burst time prediction, starvation of long processes."),
            ("Multi-Level Feedback Queues (MLFQ) prioritize interactive I/O-bound jobs in top high-priority queues while demoting CPU-heavy compute jobs to lower queues with larger time slices.",
             "Accepts multiple priority queues, aging, demoting CPU hogs, prioritizing interactive tasks.")
        ]
    ),
    (
        "Q089",
        "Explain memory leaks, how to detect them in production, and how garbage collection strategies differ.",
        "Databases & OS",
        [
            ("A memory leak occurs when an application retains references to allocated memory that is no longer needed, preventing reclamation.",
             "Accepts unreleased memory, orphaned references, monotonically increasing memory usage."),
            ("Detected via heap profiling, monitoring resident set size (RSS), tracking memory growth over time, and analyzing object allocation graphs.",
             "Accepts heap dumps, RSS monitoring, memory profilers, Valgrind."),
            ("Reference counting reclaims objects immediately when their reference counter hits zero (vulnerable to cyclic references), while tracing GC (mark-and-sweep) traverses reachable roots periodically.",
             "Accepts reference counting vs mark-and-sweep tracing, handling circular references.")
        ]
    ),
    (
        "Q090",
        "Compare Docker Containers and Virtual Machines (VMs): architecture, isolation, and overhead.",
        "Databases & OS",
        [
            ("Virtual Machines run full guest operating systems on top of a hypervisor (Type 1 or Type 2), virtualizing hardware.",
             "Accepts hypervisor, guest OS, hardware virtualization."),
            ("Containers share the host operating system kernel, packaging only user-space binaries, libraries, and application dependencies.",
             "Accepts shared host kernel, container engine, lightweight packaging."),
            ("VMs provide strong hardware-level security isolation at high memory/startup overhead; containers provide process-level isolation (via Linux namespaces and cgroups) with near-native performance and sub-second startup.",
             "Accepts namespaces and cgroups, fast boot time, isolation depth differences.")
        ]
    ),
    (
        "Q091",
        "Explain Page Replacement Algorithms: FIFO versus Least Recently Used (LRU) versus Clock (Second Chance).",
        "Databases & OS",
        [
            ("Page replacement chooses which resident physical frame to evict to disk swap when memory is full and a page fault occurs.",
             "Accepts evicting pages on memory exhaustion or swap management."),
            ("FIFO evicts the oldest loaded page, vulnerable to Belady's Anomaly where allocating more physical frames can paradoxically increase page faults.",
             "Accepts Belady's anomaly, queue of page arrival times."),
            ("LRU evicts the page unaccessed for the longest duration, approximated efficiently in hardware via the Clock algorithm using reference/use bits.",
             "Accepts LRU optimal approximation, Clock second chance algorithm, reference bit check.")
        ]
    ),
    (
        "Q092",
        "Describe Database Normalization up to Third Normal Form (3NF) and when denormalization is justified.",
        "Databases & OS",
        [
            ("1NF requires atomic attribute values and no repeating groups; 2NF eliminates partial dependencies on composite primary keys.",
             "Accepts 1NF atomic columns, 2NF full functional dependency on primary key."),
            ("3NF eliminates transitive dependencies where non-key attributes depend on other non-key attributes.",
             "Accepts no transitive dependencies, X -> Y where Y is non-prime."),
            ("Denormalization intentionally introduces controlled redundancy into tables to eliminate expensive multi-table JOINs and optimize read query performance in analytical or high-throughput read workloads.",
             "Accepts reducing joins, improving read latency, analytical data warehousing.")
        ]
    ),
    (
        "Q093",
        "What is Multi-Version Concurrency Control (MVCC) in PostgreSQL and MySQL InnoDB?",
        "Databases & OS",
        [
            ("Enables readers to avoid blocking writers and writers to avoid blocking readers by maintaining multiple snapshot versions of data rows.",
             "Accepts readers don't block writers, writers don't block readers, row snapshot versions."),
            ("Each transaction sees a consistent snapshot of the database at its start timestamp based on transaction visibility IDs (xmin/xmax).",
             "Accepts transaction ID visibility, xmin/xmax, snapshot isolation."),
            ("Dead row versions created by updates and deletes must be periodically cleaned up via background VACUUM (PostgreSQL) or undo log purge threads (InnoDB).",
             "Accepts vacuuming dead tuples, undo log cleanup, bloat prevention.")
        ]
    ),
    (
        "Q094",
        "Explain File System inodes, hard links, and symbolic (soft) links in UNIX/Linux.",
        "Databases & OS",
        [
            ("An inode stores file metadata (permissions, owner, size, timestamps, data block disk pointers) excluding filename and file data.",
             "Accepts inode metadata storage, pointer to disk blocks, no filename inside inode."),
            ("A hard link is a directory entry associating a filename directly with an existing inode number; file data persists until the inode link count drops to zero.",
             "Accepts direct pointer to inode, reference link count, survives source deletion."),
            ("A symbolic link is a distinct file whose data payload contains the text string path to target file; becomes broken if the target file is renamed or removed.",
             "Accepts pointer to path, broken link if moved, independent inode.")
        ]
    ),
    (
        "Q095",
        "What is the difference between Synchronous, Asynchronous, Blocking, and Non-blocking I/O?",
        "Databases & OS",
        [
            ("Blocking I/O suspends the calling thread until the requested data is completely transferred to user space.",
             "Accepts thread sleep during I/O, wait for completion."),
            ("Non-blocking I/O returns immediately with an error code (EWOULDBLOCK) if data is not ready, requiring polling.",
             "Accepts immediate return, polling readiness."),
            ("Asynchronous I/O (AIO / io_uring) delegates execution entirely to kernel/hardware and invokes a callback or completion queue notification when data transfer is finished without thread waiting.",
             "Accepts callback notification, completion event, zero thread blocking during transfer.")
        ]
    ),
    (
        "Q096",
        "Explain Context Switching and the performance overhead associated with saving and restoring state.",
        "Databases & OS",
        [
            ("The operating system saves the execution context (CPU registers, program counter, stack pointer) of a running process/thread and restores another's.",
             "Accepts saving/restoring register state, program counter, kernel trap."),
            ("Direct costs include kernel privilege transition time, executing the scheduler code, and saving register state.",
             "Accepts kernel mode switch, scheduler overhead, CPU cycle consumption."),
            ("Indirect costs include invalidating CPU instruction/data caches and Translation Lookaside Buffer (TLB) flushes during process context switches.",
             "Accepts cache coldness, TLB flush overhead, memory hierarchy penalty.")
        ]
    ),
    (
        "Q097",
        "Describe Database Sharding strategies: Range-based versus Hash-based versus Directory-based.",
        "Databases & OS",
        [
            ("Range-based sharding assigns contiguous ranges of shard keys to specific nodes (e.g., A-F, G-M), simple for range queries but prone to write hotspots on sequential keys.",
             "Accepts range partitioning, hotspot on sequential writes, efficient range scans."),
            ("Hash-based sharding applies a cryptographic or uniform hash function to the shard key to distribute rows evenly across nodes, eliminating hotspots at the expense of efficient range queries.",
             "Accepts uniform hash distribution, avoiding hotspots, scatter-gather range queries."),
            ("Directory-based sharding uses a dynamic lookup service or mapping table to route keys to shards, providing maximum rebalancing flexibility at the cost of a central query hop.",
             "Accepts lookup service, mapping table, routing tier overhead.")
        ]
    ),
    (
        "Q098",
        "Explain CPU Caching: L1/L2/L3 cache hierarchies, cache lines, and false sharing.",
        "Databases & OS",
        [
            ("CPUs employ multi-tiered caches (small ultra-fast L1, larger L2/L3) to bridge the massive speed gap between CPU clock cycles and main RAM latency.",
             "Accepts multi-level cache hierarchy, low latency SRAM near CPU cores."),
            ("Data is transferred between memory and cache in fixed-size blocks called cache lines (typically 64 bytes).",
             "Accepts 64-byte cache line block size, spatial locality."),
            ("False sharing occurs in multi-threaded programs when threads on distinct cores modify independent variables that reside within the identical cache line, triggering expensive cache invalidation bus traffic.",
             "Accepts independent variables in same cache line, MESI protocol invalidation storm, core thrashing.")
        ]
    ),
    (
        "Q099",
        "What are Linux cgroups and namespaces, and how do they enable containerization?",
        "Databases & OS",
        [
            ("Namespaces provide process isolation by virtualizing system resources (PID, Mount, Network, UTS, IPC, User).",
             "Accepts isolation of process view, network namespace, PID namespace."),
            ("Control Groups (cgroups) meter, limit, and prioritize physical hardware resource usage (CPU shares, memory caps, disk I/O, network bandwidth).",
             "Accepts resource limitation, CPU limits, memory quotas, OOM killer triggers."),
            ("Together they allow container runtimes to isolate a process's view of the operating system while strictly enforcing hardware consumption limits.",
             "Accepts container foundation, view isolation + resource quota control.")
        ]
    ),
    (
        "Q100",
        "Explain Database Deadlocks and how database engines detect and resolve them.",
        "Databases & OS",
        [
            ("Occur when two or more transactions hold exclusive locks that the other transactions need to proceed, forming a cyclical dependency.",
             "Accepts circular wait on locked rows, transaction deadlock condition."),
            ("Engine constructs a directed Wait-For Graph where nodes are transactions and edges represent lock dependencies, checking periodically for cycles.",
             "Accepts wait-for graph cycle detection or lock timeout detection."),
            ("Resolved by selecting and aborting a victim transaction (typically the one with least work or lowest priority), rolling back its changes and releasing its locks.",
             "Accepts choosing victim transaction, rollback, releasing locks to let other transaction succeed.")
        ]
    ),

    # --- Python, Software Engineering & API Design (20 questions) ---
    (
        "Q101",
        "Explain the Python Global Interpreter Lock (GIL) and its implications for multithreading.",
        "Python & SE",
        [
            ("A mutex that protects access to Python object internals, preventing multiple native OS threads from executing Python bytecodes simultaneously within a single process.",
             "Accepts mutex protecting CPython memory, single thread executes bytecode at a time."),
            ("CPU-bound tasks in Python do not achieve speedups with standard multithreading due to GIL lock contention and serialization.",
             "Accepts no multi-core CPU speedup with threading, lock contention on compute."),
            ("Bypassed for CPU-intensive tasks using multiprocessing (separate address spaces), C/C++ extensions, or I/O-bound threading where the GIL is released during socket/file waits.",
             "Accepts multiprocessing, releasing GIL in C extensions, or I/O threading releasing GIL.")
        ]
    ),
    (
        "Q102",
        "Compare Python Generators and Iterators: protocol implementation and memory efficiency.",
        "Python & SE",
        [
            ("An iterator is an object implementing the iterator protocol: __iter__() returning self and __next__() returning values or raising StopIteration.",
             "Accepts __iter__ and __next__ methods, StopIteration exception."),
            ("A generator is a function containing 'yield' statements that automatically generates iterator state machines, pausing execution and maintaining stack frame state between calls.",
             "Accepts yield keyword, lazy evaluation, maintaining local variables across calls."),
            ("Generators provide massive memory efficiency by streaming items lazily on demand (O(1) space) instead of materializing entire lists in RAM (O(N) space).",
             "Accepts streaming large datasets, O(1) memory, lazy generation vs eager lists.")
        ]
    ),
    (
        "Q103",
        "Explain Python Decorators and Closures with an example of an execution timer decorator.",
        "Python & SE",
        [
            ("A closure is an inner function that retains lexical scope access to variables in its enclosing scope even after the outer function has finished executing.",
             "Accepts inner function capturing enclosing variables, lexical environment preservation."),
            ("A decorator is a callable that takes a function as input, wraps its execution with pre- or post-processing logic, and returns the modified callable.",
             "Accepts higher-order function, wrapping function behavior, @ syntax."),
            ("An execution timer records start time using time.perf_counter(), invokes the wrapped function via (*args, **kwargs), computes elapsed time, and returns the original result.",
             "Accepts functools.wraps, measuring elapsed time, preserving function metadata.")
        ]
    ),
    (
        "Q104",
        "Describe Python Memory Management: memory allocator pools, arenas, and the cyclic garbage collector.",
        "Python & SE",
        [
            ("Small object memory (< 512 bytes) is managed by PyMalloc, allocating memory blocks inside pools that are organized into 256KB arenas to reduce OS allocation fragmentation.",
             "Accepts PyMalloc small object allocator, arenas and pools, reducing malloc overhead."),
            ("Standard object lifecycle relies on reference counting, freeing memory immediately when ob_refcnt drops to zero.",
             "Accepts reference counting as primary collection mechanism."),
            ("Cyclic garbage collector uses generational mark-and-sweep (Generations 0, 1, 2) to detect and reclaim isolated clusters of self-referencing objects.",
             "Accepts 3 generational GC, detecting circular references, heuristic threshold collections.")
        ]
    ),
    (
        "Q105",
        "Compare REST, gRPC, and GraphQL: communication protocols, data formats, and performance characteristics.",
        "Python & SE",
        [
            ("REST uses standard HTTP methods (GET, POST, PUT, DELETE) transmitting text JSON/XML payloads, widely compatible and easily cached via HTTP proxies.",
             "Accepts HTTP verbs, JSON over HTTP 1.1/2, universal browser support."),
            ("gRPC runs over HTTP/2 using binary Protocol Buffers (protobuf), supporting strongly typed contracts, bidirectional streaming, and high throughput with minimal serialization overhead.",
             "Accepts Protobuf binary serialization, HTTP/2 multiplexing, microservice RPC performance."),
            ("GraphQL allows clients to request exact required fields via a single POST endpoint, eliminating over-fetching and under-fetching at the cost of complex server-side query execution and caching.",
             "Accepts client-defined query schema, solving over/under-fetching, single endpoint.")
        ]
    ),
    (
        "Q106",
        "Explain the SOLID design principles in Object-Oriented Software Engineering.",
        "Python & SE",
        [
            ("Single Responsibility Principle (a class should have one reason to change) and Open/Closed Principle (open for extension, closed for modification).",
             "Accepts S and O principles accurately defined."),
            ("Liskov Substitution Principle (subtypes must be substitutable for their base types without altering correctness) and Interface Segregation Principle (clients should not be forced to depend on unused interfaces).",
             "Accepts L and I principles accurately defined."),
            ("Dependency Inversion Principle (high-level modules should depend on abstractions/interfaces rather than concrete low-level implementations).",
             "Accepts D principle accurately defined, dependency injection.")
        ]
    ),
    (
        "Q107",
        "Compare Unit Testing, Integration Testing, and End-to-End (E2E) Testing in the testing pyramid.",
        "Python & SE",
        [
            ("Unit tests isolate individual functions or classes in memory, mocking external dependencies to execute quickly and deterministically.",
             "Accepts isolated testing of units, mocks/stubs, fast CI execution."),
            ("Integration tests verify that collaborating subsystems (e.g. database, message queue, external APIs) communicate correctly together.",
             "Accepts testing component interactions, database integration, boundary contracts."),
            ("E2E tests validate complete user journeys across the entire deployed system stack, providing highest fidelity but with higher latency and fragility.",
             "Accepts whole system validation, user flows, testing pyramid balance.")
        ]
    ),
    (
        "Q108",
        "Explain Python's asyncio Event Loop and compare asynchronous programming with multithreading.",
        "Python & SE",
        [
            ("The event loop runs in a single thread, scheduling and executing non-blocking coroutines cooperatively using an internal readiness queue (epoll/kqueue).",
             "Accepts single-threaded event loop, cooperative multitasking, epoll selector."),
            ("Coroutines yield control back to the event loop upon encountering 'await' on an I/O future, allowing other ready coroutines to proceed.",
             "Accepts await keyword, yielding control during I/O, cooperative scheduling."),
            ("Asyncio eliminates OS thread context switching overhead and race-condition locks for I/O-bound concurrency, but blocking CPU code freezes the entire loop unless offloaded to an executor.",
             "Accepts lightweight tasks vs heavy OS threads, loop blocking risk from CPU tasks.")
        ]
    ),
    (
        "Q109",
        "Compare Git branching strategies: Git Flow versus Trunk-Based Development.",
        "Python & SE",
        [
            ("Git Flow defines rigid long-lived branches (master, develop, feature, release, hotfix) with formal merge gates, suitable for scheduled monolithic releases.",
             "Accepts multiple long-lived branches, develop branch, scheduled release cycles."),
            ("Trunk-Based Development has developers merge short-lived feature branches frequently into a single central branch ('trunk' or 'main') multiple times per day.",
             "Accepts short-lived branches, continuous integration into main, small frequent commits."),
            ("Trunk-based development relies on automated CI testing and Feature Flags to deploy code to production continuously without exposing unready features to users.",
             "Accepts feature flags, automated CI/CD gating, fast feedback loops.")
        ]
    ),
    (
        "Q110",
        "Explain the Factory Method versus Abstract Factory design patterns.",
        "Python & SE",
        [
            ("Factory Method defines an interface or method in a base class, deferring the instantiation of a single product object to derived subclasses.",
             "Accepts delegating object creation to subclass method, creating single product."),
            ("Abstract Factory provides an interface for creating families of related or dependent objects without specifying their concrete classes.",
             "Accepts creating suites/families of related objects, higher-level factory."),
            ("Both encapsulate object creation to decouple client code from concrete implementations, adhering to the Open/Closed Principle.",
             "Accepts decoupling creation from business logic, polymorphic instantiation.")
        ]
    ),
    (
        "Q111",
        "What is the difference between *args and **kwargs in Python function definitions?",
        "Python & SE",
        [
            ("*args captures variable positional arguments passed to a function into a tuple.",
             "Accepts arbitrary positional arguments, tuple packing."),
            ("**kwargs captures variable keyword arguments passed to a function into a dictionary.",
             "Accepts arbitrary keyword arguments, dictionary packing."),
            ("Allows flexible function forwarding and generic wrappers (such as decorators) to pass arguments through without hardcoding parameter signatures.",
             "Accepts argument unpacking, forwarding to wrapped callables.")
        ]
    ),
    (
        "Q112",
        "Explain Method Resolution Order (MRO) and the C3 Linearization algorithm in Python multiple inheritance.",
        "Python & SE",
        [
            ("MRO determines the deterministic search order Python traverses to resolve methods and attributes in classes with multiple inheritance.",
             "Accepts attribute lookup order across multiple parent classes."),
            ("CPython employs the C3 Linearization algorithm, enforcing monotonicity and respecting local precedence order of base classes.",
             "Accepts C3 linearization algorithm, preserving parent class sequence."),
            ("Prevents ambiguities like the Diamond Problem where a method could be inherited from multiple intermediate parents; inspectable via Class.__mro__.",
             "Accepts diamond problem resolution, inspecting __mro__ attribute.")
        ]
    ),
    (
        "Q113",
        "What are Python Context Managers and how does the with statement prevent resource leaks?",
        "Python & SE",
        [
            ("Context managers govern runtime context allocation and cleanup via the __enter__() and __exit__() magic methods.",
             "Accepts __enter__ and __exit__ protocols."),
            ("The 'with' statement guarantees that __exit__() executes upon exiting the block, even if unhandled exceptions are raised inside.",
             "Accepts guaranteed cleanup, equivalent to try-finally block, exception suppression capability."),
            ("Commonly used to guarantee reliable closure of file descriptors, network sockets, database transactions, and lock releases.",
             "Accepts closing files, releasing locks, rolling back DB transactions.")
        ]
    ),
    (
        "Q114",
        "Compare mutable and immutable data types in Python, and explain the default mutable argument pitfall.",
        "Python & SE",
        [
            ("Immutable types (int, float, str, tuple, frozenset) cannot be modified in-place after creation; modifications create new objects.",
             "Accepts cannot alter in-place, hashability for dictionary keys."),
            ("Mutable types (list, dict, set) allow in-place mutations without altering object identity (id()).",
             "Accepts in-place modification, same memory address."),
            ("Default function arguments in Python are evaluated once at function definition time, so mutable defaults (e.g. def fn(arg=[])) share state across all subsequent calls.",
             "Accepts default evaluated at compile/definition time, shared list bug, using None as default.")
        ]
    ),
    (
        "Q115",
        "Describe the Singleton pattern, its thread-safe implementation in Python, and criticisms against it.",
        "Python & SE",
        [
            ("Ensures a class has only a single instance throughout the application lifecycle and provides a global access point to it.",
             "Accepts single instance guarantee, global access."),
            ("Implemented via __new__() overriding with double-checked locking using a threading.Lock to prevent race conditions during initialization.",
             "Accepts thread-safe __new__, double-checked locking, module-level singleton."),
            ("Criticized as an anti-pattern because it introduces hidden global state, tight coupling, and impedes unit test isolation and parallel test execution.",
             "Accepts global state anti-pattern, hard to mock/test, tight coupling.")
        ]
    ),
    (
        "Q116",
        "What is Database Migration tooling (e.g. Alembic / Flyway) and why is it essential in CI/CD?",
        "Python & SE",
        [
            ("Tracks, versions, and applies incremental relational database schema alterations in source-controlled revision scripts.",
             "Accepts versioning database schema changes, revision files."),
            ("Provides forward migration ('upgrade') and backward rollback ('downgrade') methods to keep schema aligned with application code versions.",
             "Accepts upgrade and downgrade scripts, schema reproducibility across environments."),
            ("Automates database updates during CI/CD deployments without manual SQL execution, preventing runtime schema mismatches.",
             "Accepts zero manual DB tweaks, CI/CD automated deployment, environment parity.")
        ]
    ),
    (
        "Q117",
        "Explain the Strategy Design Pattern and how it achieves Open/Closed compliance in Python.",
        "Python & SE",
        [
            ("Defines a family of interchangeable algorithms or behaviors, encapsulating each one in a separate class or callable.",
             "Accepts interchangeable algorithms, encapsulating behaviors."),
            ("Clients maintain a reference to a strategy interface and delegate the task execution to whichever concrete strategy is injected.",
             "Accepts runtime strategy switching, dependency injection of behavior."),
            ("Eliminates giant conditional if/elif ladders and enables adding new behaviors without modifying existing client code.",
             "Accepts replacing if/else trees, adhering to Open/Closed principle.")
        ]
    ),
    (
        "Q118",
        "Compare Shallow Copy and Deep Copy in Python using the copy module.",
        "Python & SE",
        [
            ("Shallow copy (copy.copy) creates a new compound object but inserts references into it to the objects found in the original.",
             "Accepts new outer container but shared inner object references."),
            ("Deep copy (copy.deepcopy) recursively copies both the outer container and all nested objects, creating fully independent duplicates.",
             "Accepts recursive duplication of nested structures, independent memory."),
            ("Mutating a nested list in a shallow copy alters the original object, whereas deep copy isolates changes completely.",
             "Accepts nested mutation side effect in shallow copy.")
        ]
    ),
    (
        "Q119",
        "Explain Semantic Versioning (SemVer) rules: MAJOR.MINOR.PATCH and breaking change management.",
        "Python & SE",
        [
            ("PATCH version increments for backwards-compatible bug fixes and internal patches.",
             "Accepts bug fixes without API changes."),
            ("MINOR version increments for new backwards-compatible functionality or features.",
             "Accepts new features without breaking existing clients."),
            ("MAJOR version increments for incompatible API changes that break backward compatibility, requiring migration by consumers.",
             "Accepts breaking API changes, deprecation lifecycles.")
        ]
    ),
    (
        "Q120",
        "What is Dependency Injection and how does it improve software modularity and testability?",
        "Python & SE",
        [
            ("A design pattern where an object receives its dependencies from external callers rather than creating them internally.",
             "Accepts passing dependencies in constructor/parameters rather than hardcoding instantiations."),
            ("Decouples high-level business logic from specific concrete implementations and third-party libraries.",
             "Accepts loose coupling, depending on abstractions."),
            ("Drastically improves testability by allowing unit tests to inject lightweight mock or stub dependencies in place of live external services.",
             "Accepts enabling mock injection in tests, avoiding live DB/network calls in CI.")
        ]
    ),
]

def generate_rubrics_file():
    assert len(QUESTIONS_DATA) == 120, f"Expected 120 questions, got {len(QUESTIONS_DATA)}"
    
    rubrics = []
    for q_id, prompt, domain, ideas in QUESTIONS_DATA:
        semantic_ideas = []
        n_ideas = len(ideas)
        equal_weight = round(1.0 / n_ideas, 4)
        for idx, (stmt, guidance) in enumerate(ideas):
            semantic_ideas.append({
                "idea_id": f"{q_id}_IDEA_{idx + 1}",
                "semantic_statement": stmt,
                "required": True,
                "weight": equal_weight,
                "acceptable_paraphrase_guidance": guidance
            })
        # Normalize weights so sum is 1.0
        w_sum = sum(i["weight"] for i in semantic_ideas)
        for i in semantic_ideas:
            i["weight"] = round(i["weight"] / w_sum, 4)
            
        rubrics.append({
            "question_id": q_id,
            "question_prompt": prompt,
            "domain": domain,
            "target_score_scale": {"min": 1, "max": 5},
            "semantic_rubric_ideas": semantic_ideas
        })
        
    out_path = DATA_DIR / "rubrics_120.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rubrics, f, indent=2)
    print(f"Generated {len(rubrics)} rubrics in {out_path}")
    return rubrics

# Realistic candidate response templates across 5 score bands
CANDIDATE_TEMPLATES = {
    5: [
        "To address {topic}, the core principle is that {idea1}. Furthermore, {idea2}. In practical implementations, {idea3}. This provides an optimal balance between correctness and performance.",
        "Basically, speaking about {topic}, first {idea1}. In addition to that, {idea2}. And to conclude, {idea3}. That is why this approach is standard in production systems."
    ],
    4: [
        "In {topic}, {idea1}. Also, {idea2}. While {idea3_brief}, overall it ensures the main objective is achieved.",
        "Looking at {topic}, basically {idea1} and {idea2}. We usually see this in real world setups."
    ],
    3: [
        "For {topic}, I think {idea1}. Regarding other aspects, matlab it relates to {idea2_brief}, but I am not completely sure about the fine details.",
        "In {topic}, {idea1}. That is the main part as far as I know."
    ],
    2: [
        "Uh, for {topic}, I remember it has something to do with {idea1_brief}, but honestly I have not worked on this recently. Basically that is it.",
        "Regarding {topic}, toh it does some processing on the inputs, but I cannot recall the exact mechanics."
    ],
    1: [
        "I am not familiar with {topic}. I cannot answer this question.",
        "Uh, sorry sir, I have not prepared {topic}. Can we skip to the next question?"
    ]
}

def perturb_transcript(text: str) -> str:
    """Simulate realistic Indian-English / L2 ASR speech-to-text substitutions."""
    substitutions = [
        ("gradient descent", "greatient decent"),
        ("gradient", "greatient"),
        ("hyperparameter", "piper parameter"),
        ("hyper parameter", "piper parameter"),
        ("eigenvalue", "iron value"),
        ("eigenvectors", "iron vectors"),
        ("backpropagation", "back propogation"),
        ("polymorphism", "poly morphism"),
        ("O(n log n)", "oh n log n"),
        ("O(1)", "oh one"),
        ("O(N)", "oh n"),
        ("vector", "wector"),
        ("very", "wery"),
        ("value", "walue"),
        ("the", "de"),
        ("this", "dis"),
        ("that", "dat"),
        ("think", "tink"),
        ("through", "trough"),
        ("basically", "basically ya"),
        ("actually", "actually na"),
        ("cache", "cash"),
        ("queue", "cue"),
        ("SQL", "sequel"),
    ]
    perturbed = text
    for orig, sub in substitutions:
        if orig in perturbed and random.random() < 0.7:
            perturbed = perturbed.replace(orig, sub)
    # Add occasional code-mixed discourse particle
    fillers = [" matlab ", " toh ", " like you know ", " basically "]
    words = perturbed.split()
    if len(words) > 8 and random.random() < 0.5:
        insert_idx = random.randint(3, len(words) - 3)
        words.insert(insert_idx, random.choice(fillers).strip())
        perturbed = " ".join(words)
    return perturbed

def generate_datasets(rubrics):
    # 240 dev examples (2 per question across 120 questions)
    dev_examples = []
    heldout_examples = []
    
    cand_counter = 100
    
    # Generate 240 Dev Examples
    dev_id = 1
    for q in rubrics:
        q_id = q["question_id"]
        topic = q["question_prompt"]
        ideas = q["semantic_rubric_ideas"]
        idea1 = ideas[0]["semantic_statement"]
        idea2 = ideas[1]["semantic_statement"] if len(ideas) > 1 else ideas[0]["semantic_statement"]
        idea3 = ideas[2]["semantic_statement"] if len(ideas) > 2 else "it guarantees convergence"
        idea1_brief = idea1.split(",")[0]
        idea2_brief = idea2.split(",")[0]
        idea3_brief = idea3.split(",")[0]
        
        # Two examples per question for dev: varying score tiers
        for ex_idx in range(2):
            cand_counter += 1
            cand_id = f"CAND_{cand_counter}"
            
            # Determine base score level (distribute across 1 to 5)
            tier_weights = [0.1, 0.2, 0.35, 0.25, 0.1]
            base_score = random.choices([1, 2, 3, 4, 5], weights=tier_weights)[0]
            
            template = random.choice(CANDIDATE_TEMPLATES[base_score])
            transcript = template.format(
                topic=topic,
                idea1=idea1,
                idea2=idea2,
                idea3=idea3,
                idea1_brief=idea1_brief,
                idea2_brief=idea2_brief,
                idea3_brief=idea3_brief
            )
            perturbed = perturb_transcript(transcript)
            
            # Simulate multi-interviewer ratings with realistic agreement and occasional contested spreads
            # Base true scores for content and structure
            content_true = float(base_score)
            struct_noise = random.choice([-0.5, 0.0, 0.5])
            structure_true = max(1.0, min(5.0, content_true + struct_noise))
            
            # Decide if contested (~12% probability)
            is_contested_example = (random.random() < 0.12)
            spread_offset = 1.5 if is_contested_example else random.choice([0.0, 0.5])
            
            r1_c = max(1.0, min(5.0, round(content_true + random.choice([-0.5, 0.0, 0.5]), 1)))
            r2_c = max(1.0, min(5.0, round(content_true if not is_contested_example else content_true + spread_offset, 1)))
            r3_c = max(1.0, min(5.0, round(content_true if not is_contested_example else content_true - spread_offset, 1)))
            
            r1_s = max(1.0, min(5.0, round(structure_true + random.choice([-0.5, 0.0, 0.5]), 1)))
            r2_s = max(1.0, min(5.0, round(structure_true if not is_contested_example else structure_true + spread_offset, 1)))
            r3_s = max(1.0, min(5.0, round(structure_true if not is_contested_example else structure_true - spread_offset, 1)))
            
            c_spread = round(max(r1_c, r2_c, r3_c) - min(r1_c, r2_c, r3_c), 2)
            s_spread = round(max(r1_s, r2_s, r3_s) - min(r1_s, r2_s, r3_s), 2)
            
            c_consensus = round((r1_c + r2_c + r3_c) / 3.0, 2)
            s_consensus = round((r1_s + r2_s + r3_s) / 3.0, 2)
            o_consensus = round((c_consensus * 0.6 + s_consensus * 0.4), 2)
            
            dev_examples.append({
                "example_id": f"DEV_{dev_id:03d}",
                "question_id": q_id,
                "candidate_id": cand_id,
                "transcript": transcript,
                "accent_perturbed_transcript": perturbed,
                "human_scores": {
                    "rater_1": {"content": r1_c, "structure": r1_s, "overall": round(r1_c*0.6 + r1_s*0.4, 2)},
                    "rater_2": {"content": r2_c, "structure": r2_s, "overall": round(r2_c*0.6 + r2_s*0.4, 2)},
                    "rater_3": {"content": r3_c, "structure": r3_s, "overall": round(r3_c*0.6 + r3_s*0.4, 2)},
                    "consensus_score": {"content": c_consensus, "structure": s_consensus, "overall": o_consensus}
                },
                "inter_rater_spread": {
                    "content": c_spread,
                    "structure": s_spread,
                    "overall": round(max(c_spread, s_spread), 2)
                },
                "is_contested": (c_spread > 1.0 or s_spread > 1.0)
            })
            dev_id += 1

    # Generate 60 Held-Out Examples (spanning 60 sampled questions)
    heldout_sample_q = random.sample(rubrics, 60)
    heldout_id = 1
    for q in heldout_sample_q:
        q_id = q["question_id"]
        topic = q["question_prompt"]
        ideas = q["semantic_rubric_ideas"]
        idea1 = ideas[0]["semantic_statement"]
        idea2 = ideas[1]["semantic_statement"] if len(ideas) > 1 else ideas[0]["semantic_statement"]
        idea3 = ideas[2]["semantic_statement"] if len(ideas) > 2 else "it guarantees convergence"
        idea1_brief = idea1.split(",")[0]
        idea2_brief = idea2.split(",")[0]
        idea3_brief = idea3.split(",")[0]
        
        cand_counter += 1
        cand_id = f"CAND_HELDOUT_{cand_counter}"
        base_score = random.choices([1, 2, 3, 4, 5], weights=[0.1, 0.2, 0.35, 0.25, 0.1])[0]
        template = random.choice(CANDIDATE_TEMPLATES[base_score])
        transcript = template.format(
            topic=topic,
            idea1=idea1,
            idea2=idea2,
            idea3=idea3,
            idea1_brief=idea1_brief,
            idea2_brief=idea2_brief,
            idea3_brief=idea3_brief
        )
        perturbed = perturb_transcript(transcript)
        
        content_true = float(base_score)
        structure_true = max(1.0, min(5.0, content_true + random.choice([-0.5, 0.0, 0.5])))
        is_contested = (random.random() < 0.1)
        spread = 1.5 if is_contested else random.choice([0.0, 0.5])
        
        r1_c = max(1.0, min(5.0, round(content_true, 1)))
        r2_c = max(1.0, min(5.0, round(content_true + spread, 1)))
        r3_c = max(1.0, min(5.0, round(content_true - spread, 1)))
        
        r1_s = max(1.0, min(5.0, round(structure_true, 1)))
        r2_s = max(1.0, min(5.0, round(structure_true + spread, 1)))
        r3_s = max(1.0, min(5.0, round(structure_true - spread, 1)))
        
        c_consensus = round((r1_c + r2_c + r3_c) / 3.0, 2)
        s_consensus = round((r1_s + r2_s + r3_s) / 3.0, 2)
        o_consensus = round(c_consensus * 0.6 + s_consensus * 0.4, 2)
        
        heldout_examples.append({
            "example_id": f"HELDOUT_{heldout_id:03d}",
            "question_id": q_id,
            "candidate_id": cand_id,
            "transcript": transcript,
            "accent_perturbed_transcript": perturbed,
            "human_scores": {
                "rater_1": {"content": r1_c, "structure": r1_s, "overall": round(r1_c*0.6 + r1_s*0.4, 2)},
                "rater_2": {"content": r2_c, "structure": r2_s, "overall": round(r2_c*0.6 + r2_s*0.4, 2)},
                "rater_3": {"content": r3_c, "structure": r3_s, "overall": round(r3_c*0.6 + r3_s*0.4, 2)},
                "consensus_score": {"content": c_consensus, "structure": s_consensus, "overall": o_consensus}
            },
            "inter_rater_spread": {
                "content": round(max(r1_c, r2_c, r3_c) - min(r1_c, r2_c, r3_c), 2),
                "structure": round(max(r1_s, r2_s, r3_s) - min(r1_s, r2_s, r3_s), 2),
                "overall": round(max(r1_c, r2_c, r3_c) - min(r1_c, r2_c, r3_c), 2)
            },
            "is_contested": is_contested
        })
        heldout_id += 1

    assert len(dev_examples) == 240, f"Expected 240 dev examples, got {len(dev_examples)}"
    assert len(heldout_examples) == 60, f"Expected 60 held-out examples, got {len(heldout_examples)}"
    
    dev_ids = {e["example_id"] for e in dev_examples}
    heldout_ids = {e["example_id"] for e in heldout_examples}
    assert dev_ids.isdisjoint(heldout_ids), "Dev and Heldout IDs must be disjoint"
    
    dev_path = DATA_DIR / "dataset_dev_240.json"
    with open(dev_path, "w", encoding="utf-8") as f:
        json.dump(dev_examples, f, indent=2)
    print(f"Generated {len(dev_examples)} dev examples in {dev_path}")
    
    heldout_path = DATA_DIR / "dataset_heldout_60.json"
    with open(heldout_path, "w", encoding="utf-8") as f:
        json.dump(heldout_examples, f, indent=2)
    print(f"Generated {len(heldout_examples)} heldout examples in {heldout_path}")

if __name__ == "__main__":
    rubrics = generate_rubrics_file()
    generate_datasets(rubrics)
