"""abstraction BDD module"""

import time
import os
from typing import Dict
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


class AbstractionBDD:
    """class to generate and handle abstraction BDDs"""

    bdd: cudd_bdd.BDD
    root: cudd_bdd.Function
    mapping: Dict

    def __init__(
        self,
        phi: FNode,
        solver: str = "total",
        computation_logger: Dict = None,
        verbose: bool = False,
    ) -> None:
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("BDD") is None:
            computation_logger["BDD"] = {}
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
        computation_logger["BDD"]["phi normalization time"] = elapsed_time

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
        computation_logger["BDD"]["variable mapping creation time"] = elapsed_time

        # BUILDING ACTUAL BDD
        start_time = time.time()
        print("Building BDD...")
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
        print("BDD for phi built in ", elapsed_time, " seconds")
        computation_logger["BDD"]["DD building time"] = elapsed_time

    def __len__(self) -> int:
        return len(self.root)

    def count_nodes(self) -> int:
        """returns the number of nodes in the T-BDD"""
        return len(self)

    def count_vertices(self) -> int:
        """returns the number of nodes in the T-BDD"""
        return len(self) * 2

    def count_models(self) -> int:
        """returns the amount of models in the T-BDD"""
        return self.root.count(nvars=len(self.mapping.keys()))

    def dump(
        self,
        output_file: str,
        print_mapping: bool = True,
        dump_abstraction: bool = False,
    ) -> None:
        """save the DD on a file with graphviz"""
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
