"""abstraction BDD module"""

import logging
import time
import os
from typing import Dict, List
from pysmt.fnode import FNode
import pydot
from dd import cudd as cudd_bdd
from theorydd import formula
from theorydd.abstractdd.abstractdd import AbstractDD
from theorydd.solvers.solver import SMTEnumerator
from theorydd.walkers.walker_bdd import BDDWalker
from theorydd.util._dd_dump_util import change_bbd_dot_names as _change_bbd_dot_names
from theorydd.util._utils import cudd_dump as _cudd_dump, cudd_load as _cudd_load, get_solver as _get_solver


class AbstractionBDD(AbstractDD):
    """Python class to generate and handle abstraction BDDs.

    Abstraction BDDs are BDDs of the boolean abstraction of a normalized
    T-formula. They represent all the models of the abstraction
    of the formula i. e. all the truth assignments to boolean atoms and
    T-atoms that satisfy the formula in the boolean domain. These
    BDDs may however present T-inconsistencies.
    """

    bdd: cudd_bdd.BDD
    root: cudd_bdd.Function
    mapping: Dict[FNode, object]

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTEnumerator = "total",
        computation_logger: Dict = None,
        folder_name: str | None = None,
    ):
        """
        builds an AbstractionBDD

        Args:
            phi (FNode): a pysmt formula
            solver (str | SMTEnumerator) ["total"]: used for T-atoms normalization, can be set to total, 
                partial or extended_partial or a SMTEnumerator can be provided
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
            folder_name (str | None) [None]: the path to a folder where data to load the AbstractionBDD is stored.
                If this is not None, then all other parameters are ignored
        """
        super().__init__()
        self.logger = logging.getLogger("theorydd_abstraction_bdd")
        if folder_name is not None:
            self._load_from_folder(folder_name)
            return
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("Abstraction BDD") is None:
            computation_logger["Abstraction BDD"] = {}
        start_time = time.time()
        self.logger.info("Normalizing phi according to solver...")
        if isinstance(solver, str):
            smt_solver = _get_solver(solver)
        else:
            smt_solver = solver
        phi = formula.get_normalized(phi, smt_solver.get_converter())
        elapsed_time = time.time() - start_time
        self.logger.info("Phi was normalized in %s seconds", str(elapsed_time))
        computation_logger["Abstraction BDD"]["phi normalization time"] = elapsed_time

        # CREATING VARIABLE MAPPING
        self.mapping = self._compute_mapping(phi, computation_logger["Abstraction BDD"])

        # BUILDING ACTUAL BDD
        self._build(phi, computation_logger["Abstraction BDD"])

    def _build(self, phi:FNode, computation_logger: Dict):
        """builds the DD"""
        start_time = time.time()
        self.logger.info("Building Abstraction BDD...")
        self.bdd = cudd_bdd.BDD()
        all_values = list(self.mapping.values())
        self.bdd.declare(*all_values)
        bdd_ordering = {}
        for i, item in enumerate(all_values):
            bdd_ordering[item] = i
        cudd_bdd.reorder(self.bdd, bdd_ordering)
        walker = BDDWalker(self.mapping, self.bdd)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        self.logger.info("Abstraction BDD for phi built in %s seconds", str(elapsed_time))
        computation_logger["DD building time"] = elapsed_time

    def __len__(self) -> int:
        return len(self.root)

    def count_nodes(self) -> int:
        """Returns the number of nodes in the Abstraction-BDD"""
        return len(self)

    def count_vertices(self) -> int:
        """Returns the number of nodes in the Abstraction-BDD"""
        return len(self) * 2

    def count_models(self) -> int:
        """Returns the amount of models in the Abstraction-BDD"""
        return self.root.count(nvars=len(self.mapping.keys()))

    def graphic_dump(
        self,
        output_file: str,
        dump_abstraction: bool = False,
    ) -> None:
        """Save the AbstractionBDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
            dump_abstraction (bool) [False]: set it to True to dump a DD
                with the names of the abstraction of the atoms instead of the
                full names of atoms
        """
        temporary_dot = "bdd_temporary_dot.dot"
        reverse_mapping = dict((v, k) for k, v in self.mapping.items())
        if output_file.endswith(".dot"):
            self.bdd.dump(output_file, filetype="dot", roots=[self.root])
            if not dump_abstraction:
                _change_bbd_dot_names(output_file, reverse_mapping)
        elif output_file.endswith(".svg"):
            self.bdd.dump(temporary_dot, filetype="dot", roots=[self.root])
            if not dump_abstraction:
                _change_bbd_dot_names(temporary_dot, reverse_mapping)
            with open(temporary_dot, "r", encoding="utf8") as dot_content:
                (graph,) = pydot.graph_from_dot_data(dot_content.read())
                graph.write_svg(output_file)
            os.remove(temporary_dot)
        else:
            self.logger.info("Unable to dump BDD file: format not unsupported")
            return

    def get_mapping(self) -> Dict:
        """Returns the variable mapping used"""
        return self.mapping

    def pick(self) -> Dict[FNode, bool] | None:
        """Returns a partial model of the encoded formula"""
        if self.root == self.bdd.false:
            return None
        return self._convert_assignment(self.root.pick())

    def _convert_assignment(self, assignment):
        inv_map = {v: k for k, v in self.mapping.items()}
        return {inv_map[var]: truth for var, truth in assignment.items()}

    def pick_all(self) -> List[Dict[FNode, bool]]:
        """Returns all partial models of the encoded formula"""
        if self.root == self.bdd.false:
            return []
        items = list(self.bdd.pick_iter(self.root))
        return [self._convert_assignment(i) for i in items]

    def save_to_folder(self, folder_path: str) -> None:
        """Saves the Abstraction BDD to a folder

        Args:
            folder_path (str): the path to the folder where the BDD will be saved
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # SAVE MAPPING
        formula.save_abstraction_function(
            self.mapping, f"{folder_path}/abstraction.json"
        )
        # SAVE BDD
        _cudd_dump(self.root, f"{folder_path}/abstraction_bdd_data")

    def _load_from_folder(self, folder_path:str) -> None:
        """Loads an Abstraction BDD from a folder

        Args:
            folder_name (str): the path to the folder where the BDD is stored
        """
        self.mapping = formula.load_abstraction_function(f"{folder_path}/abstraction.json")
        self.bdd = cudd_bdd.BDD()
        self.bdd.declare(*self.mapping.values())
        self.root = _cudd_load(f"{folder_path}/abstraction_bdd_data", self.bdd)


def abstraction_bdd_load_from_folder(folder_path: str) -> AbstractionBDD:
    """Loads an Abstraction BDD from a folder

    Args:
        folder_path (str): the path to the folder where the BDD is saved

    Returns:
        (AbstractionBDD) -> the Abstraction BDD loaded from the folder
    """
    return AbstractionBDD(None, folder_name=folder_path)
