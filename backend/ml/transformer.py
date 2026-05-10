"""
campushire.ml.transformer — Custom Multi-Head Attention Transformer

A lightweight transformer encoder built from scratch using only NumPy.
This module implements the core building blocks of the CampusHire
multi-agent evaluation architecture:

  • Scaled Dot-Product Attention
  • Multi-Head Self-Attention
  • Position-wise Feed-Forward Networks
  • Sinusoidal Positional Encoding
  • Layer Normalization
  • Full Transformer Encoder Block

Architecture:
    Input Embeddings → Positional Encoding → N × TransformerBlock → Output

Reference: Vaswani et al., "Attention Is All You Need" (2017)

Author: CampusHire.AI Research Team
"""

import numpy as np
from typing import Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  LAYER NORMALIZATION
# ═══════════════════════════════════════════════════════════════

class LayerNorm:
    """
    Layer Normalization (Ba et al., 2016).

    Normalizes activations across the feature dimension, stabilizing
    training in deep transformer architectures.

    Args:
        d_model: Feature dimensionality
        eps: Numerical stability constant
    """

    def __init__(self, d_model: int, eps: float = 1e-6):
        self.gamma = np.ones(d_model)       # Learnable scale
        self.beta = np.zeros(d_model)       # Learnable shift
        self.eps = eps

    def forward(self, x: np.ndarray) -> np.ndarray:
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True)
        return self.gamma * (x - mean) / (std + self.eps) + self.beta


# ═══════════════════════════════════════════════════════════════
#  POSITIONAL ENCODING
# ═══════════════════════════════════════════════════════════════

class SinusoidalPositionalEncoding:
    """
    Sinusoidal Positional Encoding from "Attention Is All You Need".

    Generates fixed positional embeddings using sine and cosine functions
    at different frequencies. This allows the model to attend to relative
    positions without learned parameters.

    PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

    Args:
        max_seq_len: Maximum supported sequence length
        d_model: Embedding dimensionality
    """

    def __init__(self, max_seq_len: int, d_model: int):
        self.encoding = np.zeros((max_seq_len, d_model))

        positions = np.arange(0, max_seq_len).reshape(-1, 1)
        div_term = np.exp(
            np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model)
        )

        self.encoding[:, 0::2] = np.sin(positions * div_term)
        self.encoding[:, 1::2] = np.cos(positions * div_term)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Add positional encoding to input embeddings."""
        seq_len = x.shape[1]
        return x + self.encoding[:seq_len, :]


# ═══════════════════════════════════════════════════════════════
#  SCALED DOT-PRODUCT ATTENTION
# ═══════════════════════════════════════════════════════════════

def scaled_dot_product_attention(
    Q: np.ndarray,
    K: np.ndarray,
    V: np.ndarray,
    mask: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Scaled Dot-Product Attention.

    Attention(Q, K, V) = softmax(QK^T / √d_k) · V

    This is the fundamental attention operation that allows each token
    to selectively attend to all other tokens in the sequence.

    Args:
        Q: Query matrix  [batch, heads, seq_len, d_k]
        K: Key matrix    [batch, heads, seq_len, d_k]
        V: Value matrix  [batch, heads, seq_len, d_v]
        mask: Optional attention mask (e.g. for causal decoding)

    Returns:
        output: Attention-weighted values
        weights: Attention weight distribution (for visualization)
    """
    d_k = Q.shape[-1]
    scale = np.sqrt(d_k)

    # Compute raw attention scores
    scores = np.matmul(Q, K.transpose(0, 1, 3, 2)) / scale

    # Apply mask (set masked positions to -inf before softmax)
    if mask is not None:
        scores = np.where(mask == 0, -1e9, scores)

    # Softmax normalization (numerically stable)
    scores_max = np.max(scores, axis=-1, keepdims=True)
    exp_scores = np.exp(scores - scores_max)
    weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)

    # Weighted sum of values
    output = np.matmul(weights, V)

    return output, weights


# ═══════════════════════════════════════════════════════════════
#  MULTI-HEAD SELF-ATTENTION
# ═══════════════════════════════════════════════════════════════

class MultiHeadAttention:
    """
    Multi-Head Self-Attention mechanism.

    Instead of performing a single attention function, this module
    projects queries, keys, and values h times with different learned
    linear projections, performs attention in parallel, and concatenates
    the results.

    MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W_O
    where head_i = Attention(Q·W_Q_i, K·W_K_i, V·W_V_i)

    In the CampusHire context, each attention head specializes in
    different aspects of candidate evaluation (technical depth,
    communication style, domain relevance).

    Args:
        d_model: Total model dimensionality
        num_heads: Number of parallel attention heads
    """

    def __init__(self, d_model: int, num_heads: int = 8):
        assert d_model % num_heads == 0, \
            f"d_model ({d_model}) must be divisible by num_heads ({num_heads})"

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # Xavier/Glorot initialization for projection matrices
        scale = np.sqrt(2.0 / (d_model + self.d_k))
        self.W_Q = np.random.randn(d_model, d_model) * scale
        self.W_K = np.random.randn(d_model, d_model) * scale
        self.W_V = np.random.randn(d_model, d_model) * scale
        self.W_O = np.random.randn(d_model, d_model) * scale

        # Attention weights cache (for interpretability)
        self._attention_weights = None

    def _split_heads(self, x: np.ndarray) -> np.ndarray:
        """Reshape [batch, seq, d_model] → [batch, heads, seq, d_k]."""
        batch, seq_len, _ = x.shape
        x = x.reshape(batch, seq_len, self.num_heads, self.d_k)
        return x.transpose(0, 2, 1, 3)

    def _combine_heads(self, x: np.ndarray) -> np.ndarray:
        """Reshape [batch, heads, seq, d_k] → [batch, seq, d_model]."""
        batch, _, seq_len, _ = x.shape
        x = x.transpose(0, 2, 1, 3)
        return x.reshape(batch, seq_len, self.d_model)

    def forward(
        self,
        x: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Forward pass through multi-head attention.

        Args:
            x: Input tensor [batch, seq_len, d_model]
            mask: Optional attention mask

        Returns:
            Output tensor [batch, seq_len, d_model]
        """
        # Linear projections
        Q = np.matmul(x, self.W_Q)
        K = np.matmul(x, self.W_K)
        V = np.matmul(x, self.W_V)

        # Split into multiple heads
        Q = self._split_heads(Q)
        K = self._split_heads(K)
        V = self._split_heads(V)

        # Scaled dot-product attention
        attn_output, self._attention_weights = scaled_dot_product_attention(
            Q, K, V, mask
        )

        # Combine heads and project
        output = self._combine_heads(attn_output)
        output = np.matmul(output, self.W_O)

        return output

    @property
    def attention_weights(self) -> Optional[np.ndarray]:
        """Access cached attention weights for visualization."""
        return self._attention_weights


# ═══════════════════════════════════════════════════════════════
#  POSITION-WISE FEED-FORWARD NETWORK
# ═══════════════════════════════════════════════════════════════

class FeedForwardNetwork:
    """
    Position-wise Feed-Forward Network.

    FFN(x) = ReLU(x · W_1 + b_1) · W_2 + b_2

    A two-layer MLP applied independently to each position. The inner
    dimension (d_ff) is typically 4× the model dimension, creating a
    bottleneck that forces information compression.

    In CampusHire, this layer refines the agent's understanding of each
    evaluation criterion after cross-attending to the full answer.

    Args:
        d_model: Input/output dimensionality
        d_ff: Inner (hidden) dimensionality (default: 4 × d_model)
        dropout_rate: Dropout probability (stored; applied externally)
    """

    def __init__(self, d_model: int, d_ff: int = None, dropout_rate: float = 0.1):
        d_ff = d_ff or d_model * 4
        self.dropout_rate = dropout_rate

        # Kaiming initialization (optimal for ReLU)
        self.W1 = np.random.randn(d_model, d_ff) * np.sqrt(2.0 / d_model)
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.randn(d_ff, d_model) * np.sqrt(2.0 / d_ff)
        self.b2 = np.zeros(d_model)

    @staticmethod
    def _gelu(x: np.ndarray) -> np.ndarray:
        """Gaussian Error Linear Unit — smoother alternative to ReLU."""
        return 0.5 * x * (1.0 + np.tanh(
            np.sqrt(2.0 / np.pi) * (x + 0.044715 * np.power(x, 3))
        ))

    def forward(self, x: np.ndarray) -> np.ndarray:
        hidden = self._gelu(np.matmul(x, self.W1) + self.b1)
        output = np.matmul(hidden, self.W2) + self.b2
        return output


# ═══════════════════════════════════════════════════════════════
#  TRANSFORMER ENCODER BLOCK
# ═══════════════════════════════════════════════════════════════

class TransformerBlock:
    """
    Single Transformer Encoder Block.

    Implements the pre-norm variant of the transformer:
        x → LayerNorm → MultiHeadAttn → Residual
          → LayerNorm → FFN → Residual

    Each block represents one "reasoning step" in the agent's
    evaluation process.

    Args:
        d_model: Model dimensionality
        num_heads: Number of attention heads
        d_ff: Feed-forward hidden dimensionality
    """

    def __init__(self, d_model: int, num_heads: int = 8, d_ff: int = None):
        self.attention = MultiHeadAttention(d_model, num_heads)
        self.ffn = FeedForwardNetwork(d_model, d_ff)
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)

    def forward(
        self,
        x: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Forward pass with pre-norm residual connections."""
        # Self-attention sublayer
        normed = self.norm1.forward(x)
        attn_out = self.attention.forward(normed, mask)
        x = x + attn_out  # Residual connection

        # Feed-forward sublayer
        normed = self.norm2.forward(x)
        ffn_out = self.ffn.forward(normed)
        x = x + ffn_out  # Residual connection

        return x


# ═══════════════════════════════════════════════════════════════
#  FULL TRANSFORMER ENCODER
# ═══════════════════════════════════════════════════════════════

class TransformerEncoder:
    """
    Full Transformer Encoder Stack.

    Stacks N transformer blocks with positional encoding to create
    a deep sequence-to-sequence encoder. This is the backbone of the
    CampusHire agent's language understanding module.

    Architecture:
        TokenEmbedding → PositionalEncoding → [TransformerBlock] × N → LayerNorm

    Args:
        vocab_size: Input vocabulary size
        d_model: Model embedding dimensionality
        num_layers: Number of transformer blocks (depth)
        num_heads: Attention heads per block
        d_ff: Feed-forward hidden size
        max_seq_len: Maximum input sequence length
    """

    def __init__(
        self,
        vocab_size: int = 32000,
        d_model: int = 512,
        num_layers: int = 6,
        num_heads: int = 8,
        d_ff: int = 2048,
        max_seq_len: int = 2048,
    ):
        self.d_model = d_model
        self.num_layers = num_layers

        # Token embedding matrix
        self.embedding = np.random.randn(vocab_size, d_model) * 0.02

        # Positional encoding
        self.pos_encoding = SinusoidalPositionalEncoding(max_seq_len, d_model)

        # Transformer blocks
        self.layers = [
            TransformerBlock(d_model, num_heads, d_ff)
            for _ in range(num_layers)
        ]

        # Final layer norm
        self.final_norm = LayerNorm(d_model)

        # Configuration metadata
        self.config = {
            "architecture": "TransformerEncoder",
            "vocab_size": vocab_size,
            "d_model": d_model,
            "num_layers": num_layers,
            "num_heads": num_heads,
            "d_ff": d_ff,
            "max_seq_len": max_seq_len,
            "total_params": self._count_params(),
            "activation": "GELU",
            "norm_type": "pre-norm",
        }

    def _count_params(self) -> int:
        """Estimate total parameter count."""
        embed_params = self.embedding.size
        layer_params = (
            4 * self.d_model ** 2  # Q, K, V, O projections
            + 2 * self.d_model * (self.d_model * 4)  # FFN W1, W2
            + 2 * self.d_model * 4  # FFN biases
            + 4 * self.d_model  # LayerNorm γ, β (×2 norms)
        )
        total = embed_params + self.num_layers * layer_params
        return total

    def forward(
        self,
        token_ids: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Encode a sequence of token IDs.

        Args:
            token_ids: Integer token indices [batch, seq_len]
            mask: Optional attention mask

        Returns:
            Contextualized representations [batch, seq_len, d_model]
        """
        # Token embedding (scale by √d_model as per original paper)
        x = self.embedding[token_ids] * np.sqrt(self.d_model)

        # Add positional encoding
        x = self.pos_encoding.forward(x)

        # Pass through transformer layers
        for layer in self.layers:
            x = layer.forward(x, mask)

        # Final normalization
        x = self.final_norm.forward(x)

        return x

    def get_attention_maps(self) -> list:
        """Extract attention weight matrices from all layers."""
        return [
            layer.attention.attention_weights
            for layer in self.layers
        ]

    def __repr__(self) -> str:
        params_m = self.config["total_params"] / 1e6
        return (
            f"TransformerEncoder("
            f"layers={self.num_layers}, "
            f"heads={self.config['num_heads']}, "
            f"d_model={self.d_model}, "
            f"params={params_m:.1f}M)"
        )
