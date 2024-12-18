"""abstraction BDD module"""

import time
import os
from typing import Dict, List
from pysmt.fnode import FNode
import pydot
from dd import cudd as cudd_bdd
from theorydd import formula
from theorydd.smt_solver import SMTSolver
from theorydd.smt_solver_partial import PartialSMTSolver
from theorydd._string_generator import SequentialStringGenerator
from theorydd.formula import get_atoms
from theorydd.walker_bdd import BDDWalker
from theorydd._dd_dump_util import change_bbd_dot_names as _change_bbd_dot_names
from theorydd._utils import cudd_dump as _cudd_dump, cudd_load as _cudd_load


class AbstractionBDD:
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
        solver: str = "total",
        computation_logger: Dict = None,
        verbose: bool = False,
        folder_name: str | None = None,
    ):
        """
        builds an AbstractionBDD

        Args:
            phi (FNode): a pysmt formula
            solver (str) ["partial"]: used for T-atoms normalization, can be set to total or partial
            verbose (bool) [False]: set it to True to log computation on stdout
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
            folder_name (str | None) [None]: the path to a folder where data to load the AbstractionBDD is stored.
                If this is not None, then all other parameters are ignored
        """
        if folder_name is not None:
            self._load_from_folder(folder_name)
            return
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("Abstraction BDD") is None:
            computation_logger["Abstraction BDD"] = {}
        start_time = time.time()
        if verbose:
            print("Normalizing phi according to solver...")
        if solver == "total":
            smt_solver = SMTSolver()
        else:
            smt_solver = PartialSMTSolver()
        phi = formula.get_normalized(phi, smt_solver.get_converter())
        elapsed_time = time.time() - start_time
        if verbose:
            print("Phi was normalized in ", elapsed_time, " seconds")
        computation_logger["Abstraction BDD"]["phi normalization time"] = elapsed_time

        # CREATING VARIABLE MAPPING
        start_time = time.time()
        if verbose:
            print("Creating mapping...")
        self.mapping = {}
        atoms = get_atoms(phi)
        string_generator = SequentialStringGenerator()
        for atom in atoms:
            self.mapping[atom] = string_generator.next_string()
        elapsed_time = time.time() - start_time
        if verbose:
            print("Mapping created in ", elapsed_time, " seconds")
        computation_logger["Abstraction BDD"][
            "variable mapping creation time"
        ] = elapsed_time

        # BUILDING ACTUAL BDD
        start_time = time.time()
        if verbose:
            print("Building Abstraction BDD...")
        self.bdd = cudd_bdd.BDD()
        appended_values = set()
        all_values = []
        for value in self.mapping.values():
            if not value in appended_values:
                all_values.append(value)
        self.bdd.declare(*all_values)
        bdd_ordering = {}
        for i, item in enumerate(all_values):
            bdd_ordering[item] = i
        cudd_bdd.reorder(self.bdd, bdd_ordering)
        walker = BDDWalker(self.mapping, self.bdd)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        if verbose:
            print("Abstraction BDD for phi built in ", elapsed_time, " seconds")
        computation_logger["Abstraction BDD"]["DD building time"] = elapsed_time

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

    def dump(
        self,
        output_file: str,
        print_mapping: bool = False,
        dump_abstraction: bool = False,
    ) -> None:
        """Save the AbstractionBDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
            print_mapping (bool) [False]: set it to True to print the mapping
                between the names of the atoms in the DD and the original atoms
            dump_abstraction (bool) [False]: set it to True to dump a DD
                with the names of the abstraction of the atoms instead of the
                full names of atoms
        """
        temporary_dot = "bdd_temporary_dot.dot"
        reverse_mapping = dict((v, k) for k, v in self.mapping.items())
        if print_mapping:
            print("Mapping:")
            print(reverse_mapping)
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
            print("Unable to dump BDD file: format not unsupported")
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

    def _load_from_folder(self, folder_name:str) -> None:
        """Loads an Abstraction BDD from a folder

        Args:
            folder_name (str): the path to the folder where the BDD is stored
        """
        self.mapping = formula.load_abstraction_function(f"{folder_name}/abstraction.json")
        self.bdd = cudd_bdd.BDD()
        self.bdd.declare(*self.mapping.values())
        self.root = _cudd_load(f"{folder_name}/abstraction_bdd_data", self.bdd)


def abstraction_bdd_load_from_folder(folder_path: str) -> AbstractionBDD:
    """Loads an Abstraction BDD from a folder

    Args:
        folder_path (str): the path to the folder where the BDD is saved

    Returns:
        (AbstractionBDD) -> the Abstraction BDD loaded from the folder
    """
    return AbstractionBDD(None, folder_name=folder_path)
