"""this module implements the disjoint set data strucure"""

from typing import Dict, Iterable, List


class _Node:
    """this class implements the nodes of the disjoint set data structure"""

    # index of parent
    parent: int
    # rank of the node
    rank: int
    # data of the node (variable in the formula's atoms)
    data: object

    def __init__(self, index, data):
        self.data = data
        self.parent = index
        self.rank = 1

    def get_parent(self) -> int:
        """returns the parent of the node"""
        return self.parent

    def get_rank(self) -> int:
        """returns the rank of the node"""
        return self.rank

    def get_data(self):
        """returns the data of the node"""
        return self.data

    def set_parent(self, parent: int):
        """sets the parent of the node"""
        self.parent = parent

    def set_rank(self, rank: int):
        """sets the rank of the node"""
        self.rank = rank


class DisjointSet:
    """this class implements the disjoint set data structure"""

    # list of nodes
    nodes: List[_Node]
    reference: Dict[object, int]

    def __init__(self, data: Iterable[object]):
        """make nodes for all variables in the formula"""
        self.nodes = [_Node(i, d) for i, d in enumerate(data)]
        self.reference = {d: i for i, d in enumerate(data)}

    def _find(self, index: int) -> int:
        """finds the representative of the set containing the node with the given index

        uses flattening to optimize the find operation"""
        parent = self.nodes[index].get_parent()
        if parent != index:
            self.nodes[index].set_parent(self._find(parent))
        return self.nodes[index].get_parent()

    def find(self, data: object) -> int:
        """finds the index of the representative of the set containing the node with the given data"""
        index = self.reference[data]
        return self._find(index)

    def union(self, data1: object, data2: object):
        """applies union to the sets containing the nodes with the given data"""
        index1 = self.reference[data1]
        index2 = self.reference[data2]
        self._union(index1, index2)

    def _union(self, index1: int, index2: int):
        """applies union to the sets containing the nodes with the given indices

        uses rank to optimize the union operation"""
        root_a = self._find(index1)
        root_b = self._find(index2)

        if root_a == root_b:
            return

        rank_a = self.nodes[root_a].get_rank()
        rank_b = self.nodes[root_b].get_rank()

        new_rank = rank_a + rank_b

        if rank_a >= rank_b:
            self.nodes[root_b].set_parent(root_a)
            self.nodes[root_a].set_rank(new_rank)
        else:
            self.nodes[root_a].set_parent(root_b)
            self.nodes[root_b].set_rank(new_rank)

    def get_sets(self) -> Dict[int, set[object]]:
        """returns the sets in the disjoint set"""
        sets: Dict[int, set[object]] = {}
        for i, node in enumerate(self.nodes):
            root = self._find(i)
            if root not in sets:
                sets[root] = set()
            sets[root].add(node.get_data())
        return sets
