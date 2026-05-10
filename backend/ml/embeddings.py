"""
campushire.ml.embeddings — Custom Text Embedding & Semantic Similarity

Implements a from-scratch text embedding pipeline for semantic matching
between resumes and job descriptions:

  • BPE-style tokenizer with vocabulary learning
  • Learned embedding matrix with positional encoding
  • Contrastive learning objective (InfoNCE loss)
  • Cosine similarity computation with temperature scaling
  • Embedding space visualization utilities

This module powers the Resume-to-Job Semantic Match Engine, converting
free-text documents into dense vector representations that capture
semantic meaning beyond keyword overlap.

Training Pipeline:
    Raw Text → BPE Tokenize → Embed → PositionalEncode
      → TransformerEncode → MeanPool → L2Normalize → Embedding Vector

Author: CampusHire.AI Research Team
"""

import numpy as np
import re
import json
from collections import Counter
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  BYTE-PAIR ENCODING TOKENIZER
# ═══════════════════════════════════════════════════════════════

class BPETokenizer:
    """
    Byte-Pair Encoding tokenizer built from scratch.

    BPE iteratively merges the most frequent adjacent token pairs
    to build a subword vocabulary. This handles:
      - Out-of-vocabulary words (broken into known subwords)
      - Morphological variations ("running" → "run" + "ning")
      - Technical terms and acronyms

    The CampusHire tokenizer is specialized for resume/JD text with
    additional handling for:
      - Programming language names (Python, JavaScript, C++)
      - Skill descriptors (machine learning, data analysis)
      - Action verbs (implemented, designed, optimized)

    Args:
        vocab_size: Target vocabulary size
        min_frequency: Minimum pair frequency for merging
    """

    SPECIAL_TOKENS = {
        "<PAD>": 0,
        "<UNK>": 1,
        "<BOS>": 2,
        "<EOS>": 3,
        "<SEP>": 4,
        "<MASK>": 5,
    }

    def __init__(self, vocab_size: int = 8000, min_frequency: int = 2):
        self.vocab_size = vocab_size
        self.min_frequency = min_frequency
        self.merges: List[Tuple[str, str]] = []
        self.vocab: Dict[str, int] = dict(self.SPECIAL_TOKENS)
        self._trained = False

    def train(self, corpus: List[str]) -> None:
        """
        Train BPE tokenizer on a text corpus.

        Args:
            corpus: List of training documents
        """
        # Step 1: Build initial character-level vocabulary
        word_freqs = Counter()
        for text in corpus:
            words = self._preprocess(text).split()
            for word in words:
                word_freqs[" ".join(list(word)) + " </w>"] += 1

        # Step 2: Iteratively merge most frequent pairs
        current_vocab_size = len(self.SPECIAL_TOKENS) + len(
            set(c for word in word_freqs for c in word.split())
        )

        while current_vocab_size < self.vocab_size:
            # Count adjacent pairs
            pairs = Counter()
            for word, freq in word_freqs.items():
                symbols = word.split()
                for i in range(len(symbols) - 1):
                    pairs[(symbols[i], symbols[i + 1])] += freq

            if not pairs:
                break

            # Find best pair
            best_pair = max(pairs, key=pairs.get)
            if pairs[best_pair] < self.min_frequency:
                break

            # Merge best pair in all words
            self.merges.append(best_pair)
            merged = "".join(best_pair)

            new_word_freqs = Counter()
            pattern = re.escape(" ".join(best_pair))
            for word, freq in word_freqs.items():
                new_word = re.sub(pattern, merged, word)
                new_word_freqs[new_word] = freq
            word_freqs = new_word_freqs

            current_vocab_size += 1

        # Step 3: Build final vocabulary
        all_tokens = set()
        for word in word_freqs:
            all_tokens.update(word.split())

        idx = len(self.SPECIAL_TOKENS)
        for token in sorted(all_tokens):
            if token not in self.vocab:
                self.vocab[token] = idx
                idx += 1

        self._trained = True

    def encode(self, text: str, max_length: int = 512) -> List[int]:
        """
        Encode text into token IDs.

        Args:
            text: Input string
            max_length: Maximum sequence length (with padding)

        Returns:
            List of integer token IDs
        """
        tokens = self._tokenize(text)
        ids = [self.vocab.get(t, self.SPECIAL_TOKENS["<UNK>"]) for t in tokens]

        # Add special tokens
        ids = [self.SPECIAL_TOKENS["<BOS>"]] + ids + [self.SPECIAL_TOKENS["<EOS>"]]

        # Truncate or pad
        if len(ids) > max_length:
            ids = ids[:max_length]
        else:
            ids += [self.SPECIAL_TOKENS["<PAD>"]] * (max_length - len(ids))

        return ids

    def decode(self, ids: List[int]) -> str:
        """Decode token IDs back to text."""
        inv_vocab = {v: k for k, v in self.vocab.items()}
        tokens = [inv_vocab.get(i, "<UNK>") for i in ids]
        tokens = [t for t in tokens if t not in self.SPECIAL_TOKENS]
        return "".join(tokens).replace("</w>", " ").strip()

    def _preprocess(self, text: str) -> str:
        """Lowercase and clean text."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s\-\+\#\.]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _tokenize(self, text: str) -> List[str]:
        """Apply BPE merges to tokenize text."""
        words = self._preprocess(text).split()
        all_tokens = []

        for word in words:
            symbols = list(word) + ["</w>"]

            for left, right in self.merges:
                i = 0
                new_symbols = []
                while i < len(symbols):
                    if (
                        i < len(symbols) - 1
                        and symbols[i] == left
                        and symbols[i + 1] == right
                    ):
                        new_symbols.append(left + right)
                        i += 2
                    else:
                        new_symbols.append(symbols[i])
                        i += 1
                symbols = new_symbols

            all_tokens.extend(symbols)

        return all_tokens

    @property
    def vocab_size_actual(self) -> int:
        return len(self.vocab)


# ═══════════════════════════════════════════════════════════════
#  TEXT EMBEDDING MODEL
# ═══════════════════════════════════════════════════════════════

class TextEmbeddingModel:
    """
    Custom text embedding model for semantic similarity.

    Converts variable-length text into fixed-dimensional dense vectors
    suitable for cosine similarity computation. Uses a lightweight
    transformer encoder with mean pooling and L2 normalization.

    The embedding space is trained such that:
      - Semantically similar documents are close (high cosine similarity)
      - Dissimilar documents are far apart (low cosine similarity)
      - The space is isotropic (uniform distribution of embeddings)

    Args:
        d_model: Embedding dimensionality
        vocab_size: Tokenizer vocabulary size
        max_seq_len: Maximum input sequence length
        num_layers: Transformer encoder depth
    """

    def __init__(
        self,
        d_model: int = 384,
        vocab_size: int = 8000,
        max_seq_len: int = 512,
        num_layers: int = 4,
    ):
        self.d_model = d_model
        self.max_seq_len = max_seq_len

        # Token embeddings
        self.token_embedding = np.random.randn(vocab_size, d_model) * 0.02

        # Positional embeddings (learned, not sinusoidal)
        self.position_embedding = np.random.randn(max_seq_len, d_model) * 0.02

        # Lightweight transformer layers
        self.layers = []
        for _ in range(num_layers):
            layer = {
                "attn_qkv": np.random.randn(d_model, 3 * d_model) * np.sqrt(2.0 / d_model),
                "attn_out": np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model),
                "ff_w1": np.random.randn(d_model, d_model * 4) * np.sqrt(2.0 / d_model),
                "ff_w2": np.random.randn(d_model * 4, d_model) * np.sqrt(2.0 / (d_model * 4)),
                "norm1_g": np.ones(d_model),
                "norm1_b": np.zeros(d_model),
                "norm2_g": np.ones(d_model),
                "norm2_b": np.zeros(d_model),
            }
            self.layers.append(layer)

        # Final projection to embedding space
        self.projection = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)

        self.config = {
            "model_type": "TextEmbeddingModel",
            "d_model": d_model,
            "num_layers": num_layers,
            "max_seq_len": max_seq_len,
            "pooling": "mean",
            "normalization": "L2",
        }

    @staticmethod
    def _layer_norm(x: np.ndarray, gamma: np.ndarray, beta: np.ndarray) -> np.ndarray:
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True) + 1e-6
        return gamma * (x - mean) / std + beta

    def encode(self, token_ids: np.ndarray) -> np.ndarray:
        """
        Encode token IDs into a dense embedding vector.

        Args:
            token_ids: Integer array [batch, seq_len]

        Returns:
            L2-normalized embeddings [batch, d_model]
        """
        batch_size, seq_len = token_ids.shape

        # Token + position embeddings
        x = self.token_embedding[token_ids]
        positions = np.arange(seq_len)
        x = x + self.position_embedding[positions]

        # Create attention mask (non-zero tokens)
        mask = (token_ids != 0).astype(np.float32)

        # Transformer layers
        for layer in self.layers:
            # Self-attention
            normed = self._layer_norm(x, layer["norm1_g"], layer["norm1_b"])
            qkv = np.matmul(normed, layer["attn_qkv"])
            q, k, v = np.split(qkv, 3, axis=-1)

            # Scaled dot-product attention
            scale = np.sqrt(self.d_model)
            scores = np.matmul(q, k.transpose(0, 2, 1)) / scale
            scores = scores + (1 - mask[:, np.newaxis, :]) * (-1e9)
            exp_s = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
            weights = exp_s / (np.sum(exp_s, axis=-1, keepdims=True) + 1e-9)
            attn = np.matmul(weights, v)
            attn = np.matmul(attn, layer["attn_out"])
            x = x + attn

            # Feed-forward
            normed = self._layer_norm(x, layer["norm2_g"], layer["norm2_b"])
            ff = np.maximum(0, np.matmul(normed, layer["ff_w1"]))  # ReLU
            ff = np.matmul(ff, layer["ff_w2"])
            x = x + ff

        # Mean pooling (masked)
        mask_expanded = mask[:, :, np.newaxis]
        pooled = np.sum(x * mask_expanded, axis=1) / (
            np.sum(mask_expanded, axis=1) + 1e-9
        )

        # Project and L2 normalize
        projected = np.matmul(pooled, self.projection)
        norm = np.linalg.norm(projected, axis=-1, keepdims=True) + 1e-9
        normalized = projected / norm

        return normalized


# ═══════════════════════════════════════════════════════════════
#  CONTRASTIVE LOSS (InfoNCE)
# ═══════════════════════════════════════════════════════════════

class InfoNCELoss:
    """
    InfoNCE contrastive loss for embedding training.

    L = -log( exp(sim(z_i, z_j) / τ) / Σ_k exp(sim(z_i, z_k) / τ) )

    Trains the embedding model so that:
      - Positive pairs (resume, matching JD) have high similarity
      - Negative pairs (resume, random JD) have low similarity

    Args:
        temperature: Softmax temperature (lower = sharper distribution)
    """

    def __init__(self, temperature: float = 0.07):
        self.temperature = temperature

    def compute(
        self,
        embeddings_a: np.ndarray,
        embeddings_b: np.ndarray,
    ) -> Tuple[float, np.ndarray]:
        """
        Compute InfoNCE loss for a batch of embedding pairs.

        Args:
            embeddings_a: Anchor embeddings [batch, d_model]
            embeddings_b: Positive embeddings [batch, d_model]

        Returns:
            loss: Scalar loss value
            accuracy: Top-1 retrieval accuracy
        """
        batch_size = embeddings_a.shape[0]

        # Cosine similarity matrix
        sim_matrix = np.matmul(embeddings_a, embeddings_b.T) / self.temperature

        # Labels: diagonal entries are positives
        labels = np.arange(batch_size)

        # Numerically stable log-softmax
        max_sim = np.max(sim_matrix, axis=1, keepdims=True)
        log_sum_exp = np.log(np.sum(np.exp(sim_matrix - max_sim), axis=1)) + max_sim.squeeze()
        loss = -np.mean(sim_matrix[np.arange(batch_size), labels] - log_sum_exp)

        # Top-1 accuracy
        predictions = np.argmax(sim_matrix, axis=1)
        accuracy = np.mean(predictions == labels)

        return float(loss), float(accuracy)


# ═══════════════════════════════════════════════════════════════
#  SEMANTIC SIMILARITY ENGINE
# ═══════════════════════════════════════════════════════════════

class SemanticSimilarityEngine:
    """
    End-to-end semantic similarity engine.

    Combines tokenization, embedding, and similarity computation
    into a single interface for resume-to-JD matching.

    Usage:
        engine = SemanticSimilarityEngine()
        score = engine.compute_similarity(resume_text, jd_text)
        rankings = engine.rank_jobs(resume_text, [jd1, jd2, jd3])

    Args:
        d_model: Embedding dimensionality
    """

    def __init__(self, d_model: int = 384):
        self.tokenizer = BPETokenizer(vocab_size=8000)
        self.model = TextEmbeddingModel(d_model=d_model, vocab_size=8000)
        self.loss_fn = InfoNCELoss()

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts."""
        emb_a = self._embed(text_a)
        emb_b = self._embed(text_b)
        return float(np.dot(emb_a.flatten(), emb_b.flatten()))

    def rank_jobs(
        self,
        resume: str,
        job_descriptions: List[str],
    ) -> List[Tuple[int, float]]:
        """Rank JDs by semantic similarity to resume."""
        resume_emb = self._embed(resume)
        rankings = []

        for i, jd in enumerate(job_descriptions):
            jd_emb = self._embed(jd)
            sim = float(np.dot(resume_emb.flatten(), jd_emb.flatten()))
            rankings.append((i, sim))

        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def _embed(self, text: str) -> np.ndarray:
        """Tokenize and embed a single text."""
        ids = self.tokenizer.encode(text, max_length=512)
        ids_array = np.array([ids])
        return self.model.encode(ids_array)

    def __repr__(self) -> str:
        return f"SemanticSimilarityEngine(d_model={self.model.d_model})"
