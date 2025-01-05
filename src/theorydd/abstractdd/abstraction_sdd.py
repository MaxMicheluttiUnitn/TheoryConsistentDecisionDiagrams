"""abstraction SDD module"""

import logging
import os
import time
from typing import Dict, List, Set
from pysmt.fnode import FNode
from pysdd.sdd import SddManager, Vtree, SddNode, WmcManager
from theorydd import formula
from theorydd.abstractdd.abstractdd import AbstractDD
from theorydd.solvers.solver import SMTEnumerator
from theorydd.formula import get_atoms
from theorydd.walkers.walker_sdd import SDDWalker
from theorydd.tdd.theory_sdd import vtree_load_from_folder as _vtree_load_from_folder
from theorydd.util._dd_dump_util import save_sdd_object as _save_sdd_object
from theorydd.util._utils import get_solver as _get_solver


class AbstractionSDD(AbstractDD):
    """Python class to generate and handle abstraction SDDs.

    Abstraction SDDs are SDDs of the boolean abstraction of a normalized
    T-formula. They represent all the models of the abstraction
    of the formula i. e. all the truth assignments to boolean atoms and
    T-atoms that satisfy the formula in the boolean domain. These
    SDDs may however present T-inconsistencies.
    """

    SDD: SddManager
    root: SddNode
    abstraction: Dict
    refinement: Dict  # NEEDED FOR SERIALIZATION
    vtree: Vtree

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTEnumerator = "total",
        vtree_type: str = "balanced",
        computation_logger: Dict = None,
        folder_name: str | None = None,
    ):
        """
        builds an AbstractionSDD

        Args:
            phi (FNode): a pysmt formula
            solver (str | SMTEnumerator) ["total"]: used for T-atoms normalization, can be set to "total", "partial" or "extended_partial"
                or a SMTEnumerator instance can be provided
            vtree_type (str) ["balanced"]: used for Vtree generation. Available values in theorydd.constants.VALID_VTREE
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
            folder_name (str | None) [None]: the path to a folder where data to load the AbstractionSDD is stored.
                If this is not None, then all other parameters are ignored
        """
        super().__init__()
        self.logger = logging.getLogger("theorydd_abstraction_sdd")
        if folder_name is not None:
            self._load_from_folder(folder_name)
            return
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("Abstraction SDD") is None:
            computation_logger["Abstraction SDD"] = {}
        start_time = time.time()
        self.logger.info("Normalizing phi according to solver...")
        # THE SOLVER IS ONLY USED FOR ATOM NORMALIZATION
        if isinstance(solver, str):
            smt_solver = _get_solver(solver)
        else:
            smt_solver = solver
        phi = formula.get_normalized(phi, smt_solver.get_converter())
        elapsed_time = time.time() - start_time
        self.logger.info("Phi was normalized in %s seconds", str(elapsed_time))
        computation_logger["Abstraction SDD"]["phi normalization time"] = elapsed_time

        # CREATING VARIABLE MAPPING
        self.abstraction = self._compute_mapping(
            phi, computation_logger["Abstraction SDD"]
        )

        # BUILDING V-TREE
        atoms = get_atoms(phi)
        self.vtree = self._build_vtree(
            vtree_type, atoms, computation_logger["Abstraction SDD"]
        )

        # BUILDING SDD WITH WALKER
        self._build(phi, atoms, computation_logger["Abstraction SDD"])

    def _build(
        self, phi: FNode, atoms: List[FNode], computation_logger: Dict
    ) -> None:
        """builds the DD"""
        start_time = time.time()
        self.logger.info("Building Abstraction SDD...")
        self.manager = SddManager.from_vtree(self.vtree)
        sdd_literals = [self.manager.literal(i) for i in range(1, len(atoms) + 1)]
        atom_literal_map = dict(zip(atoms, sdd_literals))
        walker = SDDWalker(atom_literal_map, self.manager)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        self.logger.info("Abstraction SDD built in %s seconds", str(elapsed_time))
        computation_logger["DD building time"] = elapsed_time

    def _build_vtree(
        self,
        vtree_type: str,
        atoms: List[FNode],
        computation_logger: Dict,
    ) -> Vtree:
        start_time = time.time()
        self.logger.info("Building V-Tree...")
        self.refinement = {v: k for k, v in self.abstraction.items()}
        var_order = list(range(1, len(atoms) + 1))
        vtree = Vtree(len(atoms), var_order, vtree_type)
        elapsed_time = time.time() - start_time
        self.logger.info("V-Tree built in %s seconds", str(elapsed_time))
        computation_logger["V-Tree building time"] = elapsed_time
        return vtree

    def __len__(self) -> int:
        return max(self.root.count(), 1)

    def count_nodes(self) -> int:
        """Returns the number of nodes in the AbstractionSDD"""
        return len(self)

    def count_vertices(self) -> int:
        """Returns the number of vertices in the AbstractionSDD"""
        if self.root.is_true() or not self.root.is_decision():
            return 0
        else:
            elems = self.root.elements()
            queue: List[SddNode] = []
            for elem in elems:
                queue.extend([elem[0], elem[1]])
            total_edges = len(elems)
            visited: Set[SddNode] = set()
            visited.add(self.root)
            while len(queue) > 0:
                first = queue.pop(0)
                if first.is_decision():
                    total_edges += 1
                    if not first in visited:
                        elems = first.elements()
                        for elem in elems:
                            queue.extend([elem[0], elem[1]])
                            total_edges += 1
                    visited.add(first)
            return total_edges

    def count_models(self) -> int:
        """Returns the amount of models in the AbstractionSDD"""
        wmc: WmcManager = self.root.wmc(log_mode=False)
        return wmc.propagate()

    def get_mapping(self) -> Dict[FNode, str]:
        """returns the mapping"""
        return self.abstraction

    def graphic_dump(
        self,
        output_file: str,
        dump_abstraction: bool = False,
    ) -> None:
        """Save the AbstractionSDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
            dump_abstraction (bool) [False]: set it to True to dump a DD
                with the names of the abstraction of the atoms instead of the
                full names of atoms
        """
        if not _save_sdd_object(
            self.root, output_file, self.refinement, "SDD", dump_abstraction
        ):
            self.logger.info(
                "SDD could not be saved: The file format of %s is not supported",
                output_file
            )

    def graphic_dump_vtree(self, output_file: str) -> None:
        """Save the AbstractionSDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
        """
        if not _save_sdd_object(
            self.vtree, output_file, self.refinement, "VTree"
        ):
            self.logger.info(
                "V-Tree could not be saved: The file format of %s is not supported",
                output_file
            )

    def save_to_folder(self, folder_path: str) -> None:
        """Save the T-SDD in the specified solver

        Args:
            folder_path (str): the path to the output folder
        """
        # check if folder exists
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # save vtree
        self.save_vtree_to_folder(folder_path)
        # save mapping
        formula.save_abstraction_function(
            self.abstraction, folder_path + "/abstraction.json"
        )
        # save sdd
        self.root.save(str.encode(folder_path + "/sdd.sdd"))

    def save_vtree_to_folder(self, folder_path: str) -> None:
        """Save the V-Tree in the specified folder

        Args:
            folder_path (str): the path to the output folder
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self.vtree.save(str.encode(folder_path + "/vtree.vtree"))

    def _load_from_folder(self, folder_path: str) -> None:
        """
        Load an AbstractionSDD from a folder

        Args:
            folder_path (str): the path to the folder where the data is stored
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(
                f"Folder {folder_path} does not exist, cannot load AbstractionSDD"
            )
        self.vtree = _vtree_load_from_folder(folder_path)
        self.manager = SddManager.from_vtree(self.vtree)
        self.root = self.manager.read_sdd_file(str.encode(f"{folder_path}/sdd.sdd"))
        self.abstraction = formula.load_abstraction_function(
            folder_path + "/abstraction.json"
        )
        self.refinement = {v: k for k, v in self.abstraction.items()}


def abstraction_sdd_load_from_folder(folder_path: str) -> AbstractionSDD:
    """
    Load an AbstractionSDD from a folder

    Args:
        folder_path (str): the path to the folder where the data is stored
    """
    return AbstractionSDD(None, folder_name=folder_path)
