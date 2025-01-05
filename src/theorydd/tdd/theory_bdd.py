"""theory BDD module"""

import json
import time
import os
import logging
from typing import Dict, List
from pysmt.fnode import FNode
import pydot
from dd import cudd as cudd_bdd
from theorydd import formula
from theorydd.util._dd_dump_util import change_bbd_dot_names as _change_bbd_dot_names
from theorydd.util._utils import (
    cudd_dump as _cudd_dump,
    cudd_load as _cudd_load,
    get_solver as _get_solver,
)
from theorydd.solvers.solver import SMTEnumerator
from theorydd.formula import get_atoms
from theorydd.walkers.walker_bdd import BDDWalker
from theorydd.solvers.lemma_extractor import find_qvars
from theorydd.constants import SAT
from theorydd.tdd.theory_dd import TheoryDD


class TheoryBDD(TheoryDD):
    """Class to generate and handle T-BDDs

    TBDDs are BDDs with a mixture of boolean atoms and T-atoms
    in which every branch represents a T-consistent truth
    assignment to the atoms of the encoded formula"""

    bdd: cudd_bdd.BDD
    root: cudd_bdd.Function
    qvars: List[FNode]
    mapping: Dict[FNode, object]
    logger: logging.Logger

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTEnumerator = "total",
        load_lemmas: str | None = None,
        tlemmas: List[FNode] = None,
        sat_result: bool | None = None,
        computation_logger: Dict = None,
        folder_name: str | None = None,
    ) -> None:
        """Builds a T-BDD. The construction requires the
        computation of All-SMT for the provided formula to
        extract T-lemmas and the subsequent construction of
        a BDD of phi & lemmas

        Args:
            phi (FNode) : a pysmt formula
            solver (str | SMTEnumerator) ["total"]: specifies which solver to use for All-SMT computation.
                Valid solvers are "partial", "total" and "extended_partial", or you can pass an instance of a SMTEnumerator
            load_lemmas (str) [None]: specify the path to a file from which to load phi & lemmas.
                This skips the All-SMT computation
            tlemmas (List[Fnode]): use previously computed tlemmas.
                This skips the All-SMT computation
            sat_result (bool) [None]: the result of the All-SMT computation. This value is overwritten if t-lemmas are not provided!!!
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info.
            folder_name (str | None) [None]: the path to a folder where data to load the T-BDD is stored.
                If this is not None, then all other parameters are ignored
        """
        super().__init__()
        self.logger = logging.getLogger("theorydd_bdd")
        if folder_name is not None:
            self._load_from_folder(folder_name)
            return
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("T-BDD") is None:
            computation_logger["T-BDD"] = {}

        # NORMALIZE PHI
        if isinstance(solver, str):
            smt_solver = _get_solver(solver)
        else:
            smt_solver = solver
        phi = self._normalize_input(
            phi, smt_solver, computation_logger["T-BDD"]
        )

        # LOAD LEMMAS
        tlemmas, sat_result = self._load_lemmas(
            phi,
            smt_solver,
            tlemmas,
            load_lemmas,
            sat_result,
            computation_logger["T-BDD"],
        )

        # COMPUTE PHI AND LEMMAS
        phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)

        # FIND QVARS
        self.qvars = find_qvars(
            phi,
            phi_and_lemmas,
            computation_logger=computation_logger["T-BDD"],
        )

        atoms = get_atoms(phi_and_lemmas)

        # CREATING VARIABLE MAPPING
        self.mapping = self._compute_mapping(
            atoms, computation_logger["T-BDD"]
        )

        # PREPARE FOR BUILDING
        start_time = time.time()
        self.logger.info("starting T-BDD preparation phase...")
        self.bdd = cudd_bdd.BDD()
        appended_values = set()
        all_values = [self.mapping[atom] for atom in self.qvars]
        for atom in self.qvars:
            appended_values.add(self.mapping[atom])
        for value in self.mapping.values():
            if not value in appended_values:
                all_values.append(value)
        self.bdd.declare(*all_values)
        bdd_ordering = {}
        for i, item in enumerate(all_values):
            bdd_ordering[item] = i
        cudd_bdd.reorder(self.bdd, bdd_ordering)
        walker = BDDWalker(self.mapping, self.bdd)
        elapsed_time = time.time() - start_time
        self.logger.info("BDD preparation phase completed in %s seconds", str(elapsed_time))
        computation_logger["T-BDD"]["DD preparation time"] = elapsed_time

        if sat_result is None or sat_result == SAT:
            self.root = self._build(phi,tlemmas,walker,computation_logger["T-BDD"])
        else:
            self.root = self._build_unsat(walker,computation_logger["T-BDD"])

    def _enumerate_qvars(self, tlemmas_dd: object, mapped_qvars: List[object]) -> object:
        return cudd_bdd.and_exists(tlemmas_dd, self.bdd.true, mapped_qvars)

    def __len__(self) -> int:
        """returns the number of nodes in the T-BDD"""
        return len(self.root)

    def count_nodes(self) -> int:
        """returns the number of nodes in the T-BDD"""
        return len(self)

    def count_vertices(self) -> int:
        """returns the number of nodes in the T-BDD"""
        return len(self) * 2

    def count_models(self) -> int:
        """returns the amount of models in the T-BDD"""
        return self.root.count(nvars=len(self.mapping.keys()) - len(self.qvars))

    def graphic_dump(
        self,
        output_file: str,
        print_mapping: bool = False,
        dump_abstraction: bool = False,
    ) -> None:
        """Save the T-SDD on a file with Graphviz

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
        # TODO! REMOVE THIS IN ALL CLASSES THAT INHERIT FROM THEORYDD
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
            print("Unable to dump T-BDD file: format not unsupported")
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
        """Save all the T-BDD data inside files in the specified folder

        Args:
            file_path (str): the path to the output file
        """
        # CHECK IF FOLDER EXISTS AND CREATE IT IF NOT
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # SAVE MAPPING
        formula.save_abstraction_function(
            self.mapping, f"{folder_path}/abstraction.json"
        )
        # SAVE QVARS
        qvars_indexes = [self.mapping[qvar] for qvar in self.qvars]
        with open(f"{folder_path}/qvars.qvars", "w", encoding="utf8") as out:
            json.dump(qvars_indexes, out)
        # SAVE DD
        _cudd_dump(self.root, f"{folder_path}/tbdd_data")

    def _load_from_folder(self, folder_path: str) -> None:
        """Load a T-BDD from a folder

        Args:
            folder_path (str): the path to the folder where the data is stored
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(
                f"Folder {folder_path} does not exist, cannot load T-BDD"
            )
        self.mapping = formula.load_abstraction_function(
            f"{folder_path}/abstraction.json"
        )
        reverse_mapping = dict((v, k) for k, v in self.mapping.items())
        self.bdd = cudd_bdd.BDD()
        self.bdd.declare(*self.mapping.values())
        self.root = _cudd_load(f"{folder_path}/tbdd_data", self.bdd)
        # load qvars
        with open(f"{folder_path}/qvars.qvars", "r", encoding="utf8") as input_data:
            qvars_indexes = json.load(input_data)
            self.qvars = [reverse_mapping[qvar_id] for qvar_id in qvars_indexes]


def tbdd_load_from_folder(folder_path: str) -> TheoryBDD:
    """Load a T-BDD from a file

    Args:
        file_path (str): the path to the file

    Returns:
        TheoryBDD: the T-BDD loaded from the file
    """
    return TheoryBDD(None, folder_name=folder_path)
