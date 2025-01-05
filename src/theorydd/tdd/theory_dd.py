"""interface for the theory DD classes"""

from abc import ABC, abstractmethod
import logging
import time
from typing import Dict, List, Tuple

from pysmt.fnode import FNode

from theorydd import formula
from theorydd.solvers.lemma_extractor import extract
from theorydd.solvers.solver import SMTEnumerator
from theorydd.util._string_generator import SequentialStringGenerator
from theorydd.walkers.walker_bdd import BDDWalker
from theorydd.walkers.walker_sdd import SDDWalker


class TheoryDD(ABC):
    """interface for the theory DD classes

    This interface must be implemented by all the theory DDs that are used to compute all-SMT.
    """

    def __init__(self):
        self.mapping = {}
        self.qvars = []
        self.logger = logging.getLogger("thoerydd_tdd")

    def _compute_mapping(
        self, atoms: List[FNode], computation_logger: dict
    ) -> Dict[FNode, str]:
        """computes the mapping"""
        start_time = time.time()
        self.logger.info("Creating mapping...")
        mapping = {}

        string_generator = SequentialStringGenerator()
        for atom in atoms:
            mapping[atom] = string_generator.next_string()
        elapsed_time = time.time() - start_time
        self.logger.info("Mapping created in %s seconds", str(elapsed_time))
        computation_logger["variable mapping creation time"] = elapsed_time
        return mapping

    def _normalize_input(
        self, phi: FNode, solver: SMTEnumerator, computation_logger: Dict
    ) -> FNode:
        """normalizes the input"""
        start_time = time.time()
        self.logger.info("Normalizing phi according to solver...")
        phi = formula.get_normalized(phi, solver.get_converter())
        elapsed_time = time.time() - start_time
        self.logger.info("Phi was normalized in %s seconds",str(elapsed_time))
        computation_logger["phi normalization time"] = elapsed_time
        return phi

    def _load_lemmas(
        self,
        phi: FNode,
        smt_solver: SMTEnumerator,
        tlemmas: List[FNode] | None,
        load_lemmas: str | None,
        sat_result: bool,
        computation_logger: Dict,
    ) -> Tuple[List[FNode], bool]:
        """loads the lemmas"""
        # LOADING LEMMAS
        start_time = time.time()
        self.logger.info("Loading Lemmas...")
        if tlemmas is not None:
            computation_logger["ALL SMT mode"] = "loaded"
        elif load_lemmas is not None:
            computation_logger["ALL SMT mode"] = "loaded"
            tlemmas = [formula.read_phi(load_lemmas)]
        else:
            computation_logger["ALL SMT mode"] = "computed"
            sat_result, tlemmas, _bm = extract(
                phi,
                smt_solver,
                computation_logger=computation_logger,
            )
        tlemmas = list(
            map(
                lambda l: formula.get_normalized(l, smt_solver.get_converter()), tlemmas
            )
        )
        # BASICALLY PADDING TO AVOID POSSIBLE ISSUES
        while len(tlemmas) < 2:
            tlemmas.append(formula.top())
        elapsed_time = time.time() - start_time
        self.logger.info("Lemmas loaded in %s seconds", str(elapsed_time))
        computation_logger["lemmas loading time"] = elapsed_time
        return tlemmas, sat_result

    def _build_unsat(
        self, walker: BDDWalker | SDDWalker, computation_logger: Dict
    ) -> object:
        """builds the T-DD for an UNSAT formula

        Returns the root of the DD"""
        start_time = time.time()
        self.logger.info("Building T-DD for UNSAT formula...")
        root = walker.walk(formula.bottom())
        elapsed_time = time.time() - start_time
        self.logger.info("T-DD for UNSAT formula built in %s seconds", str(elapsed_time))
        computation_logger["UNSAT DD building time"] = elapsed_time
        return root

    def _build(
        self,
        phi: FNode,
        tlemmas: List[FNode],
        walker: BDDWalker,
        computation_logger: Dict,
    ) -> None:
        """Builds the T-DD"""
        # DD for phi
        start_time = time.time()
        self.logger.info("Building DD for phi...")
        phi_bdd = walker.walk(phi)
        elapsed_time = time.time() - start_time
        self.logger.info("DD for phi built in %s seconds", str(elapsed_time))
        computation_logger["phi DD building time"] = elapsed_time

        # DD for t-lemmas
        start_time = time.time()
        self.logger.info("Building T-DD for big and of t-lemmas...")
        tlemmas_dd = walker.walk(formula.big_and(tlemmas))
        elapsed_time = time.time() - start_time
        self.logger.info("DD for T-lemmas built in %s seconds", str(elapsed_time))
        computation_logger["t-lemmas DD building time"] = elapsed_time

        # ENUMERATING OVER FRESH T-ATOMS
        mapped_qvars = [self.mapping[atom] for atom in self.qvars]
        if len(mapped_qvars) > 0:
            start_time = time.time()
            self.logger.info("Enumerating over fresh T-atoms...")
            tlemmas_dd = self._enumerate_qvars(tlemmas_dd, mapped_qvars)
            elapsed_time = time.time() - start_time
            self.logger.info(
                    "fresh T-atoms quantification completed in %s seconds", str(elapsed_time)
                )
            computation_logger["fresh T-atoms quantification time"] = elapsed_time
        else:
            computation_logger["fresh T-atoms quantification time"] = 0

        # JOINING PHI BDD AND TLEMMAS BDD
        start_time = time.time()
        self.logger.info("Joining phi DD and lemmas T-DD...")
        root = phi_bdd & tlemmas_dd
        elapsed_time = time.time() - start_time
        self.logger.info("T-DD for phi and t-lemmas joint in %s seconds", str(elapsed_time))
        computation_logger["DD joining time"] = elapsed_time
        return root

    @abstractmethod
    def _enumerate_qvars(
        self, tlemmas_dd: object, mapped_qvars: List[object]
    ) -> object:
        """enumerates over the fresh T-atoms"""
        raise NotImplementedError()

    @abstractmethod
    def _load_from_folder(self, folder_path: str):
        """loads the DD from a folder"""
        pass

    @abstractmethod
    def save_to_folder(self, folder_path: str):
        """saves the DD to a folder"""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """returns the number of nodes in the DD"""
        pass

    @abstractmethod
    def count_nodes(self) -> int:
        """Returns the number of nodes in the DD"""
        pass

    @abstractmethod
    def count_vertices(self) -> int:
        """Returns the number of nodes in the DD"""
        pass

    @abstractmethod
    def count_models(self) -> int:
        """Returns the amount of models in the DD"""
        pass

    @abstractmethod
    def graphic_dump(self, output_file: str) -> None:
        """Save the DD on a file

        Args:
            output_file (str): the path to the output file
        """
        pass
