"""module to handle LDDs"""

import logging
import time
from typing import Any, Dict

from pysmt.shortcuts import BOOL, INT, REAL
from pysmt.fnode import FNode
from dd import ldd as _ldd

from theorydd.walkers.walker_ldd import LDDWalker
import theorydd.formula as _formula
from theorydd.util.custom_exceptions import (
    InvalidLDDTheoryException,
    UnsupportedSymbolException,
)
from theorydd.util._string_generator import SequentialStringGenerator


class LDD:
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
        computation_logger: Dict = None,
    ):
        """Builds a LDD for phi

        Args:
            phi (FNode): a pysmt T-formula of the specified theory
            theory (str): the theory of the T-atoms of phi
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
        """
        self.logger = logging.getLogger("theorydd_ldd")

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
        self.logger.info("Finding symbols...")
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
        elapsed_time = time.time() - start_time
        self.logger.info("Symbols found in %s seconds", str(elapsed_time))

        # BUILDING LDD
        self._build(phi, boolean_symbols, integer_symbols, ldd_theory, computation_logger["LDD"])

    def _build(self, phi: FNode, boolean_symbols: dict, integer_symbols: dict, theory, computation_logger: Dict):
        # LDD(Id theory,#int vars,#bool vars)
        start_time = time.time()
        self.logger.info("Building LDD...")
        self.manager = _ldd.LDD(
            theory, len(integer_symbols.keys()), len(boolean_symbols.keys())
        )
        walker = LDDWalker(boolean_symbols, integer_symbols, self.manager)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        self.logger.info("LDD for phi built in %s seconds", str(elapsed_time))
        computation_logger["DD building time"] = elapsed_time

    def __len__(self) -> int:
        return len(self.root)

    def count_nodes(self) -> int:
        """Returns the number of nodes in the LDD"""
        return len(self)

    def count_vertices(self) -> int:
        """Returns the number of nodes in the LDD"""
        return 2 * len(self)

    def count_models(self) -> int:
        """Returns the amount of models in the LDD"""
        support_size = len(self.manager.vars)
        return self.manager.count(self.root,nvars=support_size)

    def dump(self, output_file: str) -> None:
        """Save the LDD on a file

        Args:
            output_file (str): the path to the output file
        """
        self.manager.dump(output_file, [self.root])
