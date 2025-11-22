"""Graph data structure."""

import numpy as np
import scipy.sparse as sp
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Graph:
    """Simple graph data structure."""

    def __init__(
        self,
        edges: Optional[List[Tuple[int, int]]] = None,
        num_nodes: Optional[int] = None
    ):
        """
        Initialize graph.

        Args:
            edges: List of edge tuples (source, target)
            num_nodes: Number of nodes (inferred if not provided)
        """
        self.edges = edges if edges is not None else []

        if num_nodes is None and edges:
            max_node = max(max(e) for e in edges)
            num_nodes = max_node + 1

        self.num_nodes = num_nodes if num_nodes is not None else 0
        self.num_edges = len(self.edges)

        self._adj_matrix = None

        logger.info(f"Initialized Graph: {self.num_nodes} nodes, {self.num_edges} edges")

    def add_edges(self, edges: List[Tuple[int, int]]):
        """
        Add edges to graph.

        Args:
            edges: List of edge tuples
        """
        self.edges.extend(edges)
        self.num_edges = len(self.edges)
        self._adj_matrix = None  # Invalidate cache

    def get_adjacency(self, sparse: bool = True) -> np.ndarray:
        """
        Get adjacency matrix.

        Args:
            sparse: Whether to return sparse matrix

        Returns:
            Adjacency matrix
        """
        if self._adj_matrix is None:
            # Build adjacency matrix
            adj = np.zeros((self.num_nodes, self.num_nodes))

            for src, dst in self.edges:
                adj[src, dst] = 1.0
                adj[dst, src] = 1.0  # Undirected

            self._adj_matrix = adj

        if sparse:
            return sp.csr_matrix(self._adj_matrix)
        else:
            return self._adj_matrix

    def get_neighbors(self, node: int) -> List[int]:
        """
        Get neighbors of a node.

        Args:
            node: Node index

        Returns:
            List of neighbor indices
        """
        adj = self.get_adjacency(sparse=False)
        return list(np.where(adj[node] > 0)[0])

    def __repr__(self):
        return f"Graph(num_nodes={self.num_nodes}, num_edges={self.num_edges})"
