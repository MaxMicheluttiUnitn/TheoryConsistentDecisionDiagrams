"""module to handle LDDs"""

import time
from typing import Any, Dict

from pysmt.shortcuts import BOOL, INT, REAL
from pysmt.fnode import FNode
from dd import ldd as _ldd

from theorydd.walker_ldd import LDDWalker
import theorydd.formula as _formula
from theorydd.custom_exceptions import (
    InvalidLDDTheoryException,
    UnsupportedSymbolException,
)
from theorydd._string_generator import SequentialStringGenerator


class TheoryLDD:
    """Class to handle LDDs. Uses @masinag's dd and
    allows compatibility with pysmt FNodes

    LDD are T-DDs available only for some specific theories:
    TVPI, TVPIZ, UTVPIZ, BOX, BOXZ
    """

    manager: _ldd.LDD
    root: Any
    total_atoms: int

    def __init__(
        self,
        phi: FNode,
        theory: str,
        verbose: bool = False,
        computation_logger: Dict = None,
    ):
        """Builds a LDD for phi

        Args:
            phi (FNode): a pysmt T-formula of the specified theory
            theory (str): the theory of the T-atoms of phi
            verbose (bool) [False]: set it to True to log computation on stdout
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
        """
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("LDD") is None:
            computation_logger["LDD"] = {}

        # CHECKING THEORY
        if theory == "TVPI":
            ldd_theory = _ldd.TVPI
        elif theory == "TVPIZ":
            ldd_theory = _ldd.TVPIZ
        elif theory == "UTVPIZ":
            ldd_theory = _ldd.UTVPIZ
        elif theory == "BOX":
            ldd_theory = _ldd.BOX
        elif theory == "BOXZ":
            ldd_theory = _ldd.BOXZ
        else:
            raise InvalidLDDTheoryException("Invalid theory " + theory)

        # FINDING VARS
        start_time = time.time()
        if verbose:
            print("Building LDD...")
        symbols = _formula.get_symbols(phi)
        self.total_atoms = len(_formula.get_atoms(phi))
        boolean_symbols: dict[FNode, str] = {}
        integer_symbols: dict[FNode, int] = {}
        int_ctr = 1
        str_gen = SequentialStringGenerator()
        for s in symbols:
            if s.get_type() == BOOL:
                boolean_symbols.update({s: str_gen.next_string()})
            elif s.get_type() == INT:
                integer_symbols.update({s: int_ctr})
                int_ctr += 1
            elif s.get_type() == REAL:
                integer_symbols.update({s: int_ctr})
                int_ctr += 1
            else:
                raise UnsupportedSymbolException(str(s))

        # BUILDING LDD
        # LDD(Id theory,#int vars,#bool vars)
        self.manager = _ldd.LDD(
            ldd_theory, len(integer_symbols.keys()), len(boolean_symbols.keys())
        )
        walker = LDDWalker(boolean_symbols, integer_symbols, self.manager)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        if verbose:
            print("LDD for phi built in ", elapsed_time, " seconds")
        computation_logger["LDD"]["DD building time"] = elapsed_time

    def __len__(self) -> int:
        return len(self.root)

    def count_nodes(self) -> int:
        """Returns the number of nodes in the T-SDD"""
        return len(self)

    def count_vertices(self) -> int:
        """Returns the number of nodes in the T-SDD"""
        return 2 * len(self)

    def count_models(self) -> int:
        """Returns the amount of models in the T-SDD"""
        support_size = len(self.manager.vars)
        if self.root == self.manager.true:
            return int(2 ** support_size)
        elif self.root == self.manager.false:
            return 0
        return _recursive_mc(self.root, {}, self.manager, support_size)

    def dump(self, output_file: str) -> None:
        """Save the LDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
        """
        self.manager.dump(output_file, [self.root])


def _recursive_mc(node, memo: Dict, manager, support_size: int) -> int:
    """recursive function for MC"""
    if node == manager.true:
        return 1
    if node == manager.false:
        return 0
    if node not in memo.keys():
        memo[node] = 0
    if memo[node] > 0:
        return memo[node]
    i = int(node._index)
    if node.high == manager.true or node.high == manager.false:
        i_1 = int(support_size)
    else:
        i_1 = int(node.high._index)
    if node.low == manager.true or node.low == manager.false:
        i_0 = int(support_size)
    else:
        i_0 = int(node.low._index)
    memo[node] = int(2 ** (i_1 - i - 1)) * _recursive_mc(
        node.high, memo, manager, support_size
    ) + int(2 ** (i_0 - i - 1)) * _recursive_mc(node.low, memo, manager, support_size)
    return memo[node]
