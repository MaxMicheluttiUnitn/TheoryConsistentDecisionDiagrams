"""module to handle LDDs"""

import time
from typing import Dict

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
    """class to handle LDDs. Wrapper to @masinag's dd which allows compatibility with pysmt FNodes"""

    manager: _ldd.LDD
    root: _ldd.Formula
    total_atoms: int

    def __init__(
        self,
        phi: FNode,
        theory: str,
        verbose: bool = False,
        computation_logger: Dict = None,
    ):
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("LDD") is None:
            computation_logger["LDD"] = {}

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
        if theory == "UTVPI":
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
        """returns the number of nodes in the T-SDD"""
        return len(self)

    def count_vertices(self) -> int:
        """returns the number of nodes in the T-SDD"""
        return 2 * len(self)

    def count_models(self) -> int:
        """returns the amount of models in the T-SDD"""
        return self.root.count(nvars=self.total_atoms)

    def dump(self, output_file: str) -> None:
        """save the DD on a file with graphviz"""
        self.manager.dump(output_file, [self.root])
