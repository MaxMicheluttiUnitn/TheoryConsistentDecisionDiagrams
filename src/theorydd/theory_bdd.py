"""theory BDD module"""

import time
import os
from typing import Dict, List
from pysmt.fnode import FNode
import pydot
from dd import cudd as cudd_bdd
from theorydd import formula
from theorydd._dd_dump_util import change_bbd_dot_names as _change_bbd_dot_names
from theorydd.smt_solver import SAT, SMTSolver
from theorydd.smt_solver_partial import PartialSMTSolver
from theorydd._string_generator import SequentialStringGenerator
from theorydd.formula import get_atoms
from theorydd.walker_bdd import BDDWalker
from theorydd.lemma_extractor import extract, find_qvars
from theorydd.constants import SAT, UNSAT


class TheoryBDD:
    """Class to generate and handle T-BDDs
    
    TBDDs are BDDs with a mixture of boolean atoms and T-atoms
    in which every branch represents a T-consistent truth
    assignment to the atoms of the encoded formula"""

    bdd: cudd_bdd.BDD
    root: cudd_bdd.Function
    qvars: List[FNode]
    mapping: Dict

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTSolver | PartialSMTSolver = "partial",
        load_lemmas: str | None = None,
        tlemmas: List[FNode] = None,
        computation_logger: Dict = None,
        verbose: bool = False,
    ) -> None:
        """Builds a T-BDD. The construction requires the 
        computation of All-SMT for the provided formula to
        extract T-lemmas and the subsequent construction of 
        a BDD of phi & lemmas

        Args:
            phi (FNode) : a pysmt formula
            solver (str | SMTSolver | PartialSMTSolver) ["partial"]: specifies which solver to use for All-SMT computation.
                Valid solvers are "partial" and "total", or you can pass an instance of a SMTSolver or PartialSMTSolver
            load_lemmas (str) [None]: specify the path to a file from which to load phi & lemmas. 
                This skips the All-SMT computation
            tlemmas (List[Fnode]): use previously computed tlemmas. 
                This skips the All-SMT computation
            verbose (bool) [False]: set it to True to log computation on stdout
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
        """
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("T-BDD") is None:
            computation_logger["T-BDD"] = {}
        start_time = time.time()
        if verbose:
            print("Normalizing phi according to solver...")
        if isinstance(solver,str):
            if solver == "total":
                smt_solver = SMTSolver()
            else:
                smt_solver = PartialSMTSolver()
        else:
            smt_solver = solver
        phi = formula.get_normalized(phi, smt_solver.get_converter())
        elapsed_time = time.time() - start_time
        if verbose:
            print("Phi was normalized in ", elapsed_time, " seconds")
        computation_logger["T-BDD"]["phi normalization time"] = elapsed_time
        if verbose:
            print("Loading Lemmas...")
        if tlemmas is not None:
            computation_logger["T-BDD"]["ALL SMT mode"] = "loaded"
            phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)
        elif load_lemmas is not None:
            computation_logger["T-BDD"]["ALL SMT mode"] = "loaded"
            tlemmas = formula.read_phi(load_lemmas)
            phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)
        else:
            computation_logger["T-BDD"]["ALL SMT mode"] = "computed"
            _satisfiability, tlemmas = extract(
                phi,
                smt_solver,
                verbose=verbose,
                computation_logger=computation_logger["T-BDD"],
            )
            phi_and_lemmas = formula.get_phi_and_lemmas(phi,tlemmas)
        self.qvars = find_qvars(
            phi,
            phi_and_lemmas,
            verbose=verbose,
            computation_logger=computation_logger["T-BDD"],
        )
        phi = phi_and_lemmas

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
        computation_logger["T-BDD"]["variable mapping creation time"] = elapsed_time

        # BUILDING ACTUAL BDD
        start_time = time.time()
        if verbose:
            print("Building T-BDD...")
        self.bdd = cudd_bdd.BDD()
        appended_values = set()
        mapped_qvars = [self.mapping[atom] for atom in self.qvars]
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
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        if verbose:
            print("BDD for phi built in ", elapsed_time, " seconds")
        computation_logger["T-BDD"]["DD building time"] = elapsed_time

        # ENUMERATING OVER FRESH T-ATOMS
        if len(mapped_qvars) > 0:
            start_time = time.time()
            if verbose:
                print("Enumerating over fresh T-atoms...")
            root = cudd_bdd.and_exists(root, self.bdd.true, mapped_qvars)
            elapsed_time = time.time() - start_time
            if verbose:
                print("T-BDD for phi built in ", elapsed_time, " seconds")
            computation_logger["T-BDD"][
                "fresh T-atoms quantification time"
            ] = elapsed_time
        else:
            computation_logger["T-BDD"]["fresh T-atoms quantification time"] = 0

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
        return self.root.count(nvars=len(self.mapping.keys()) - len(self.qvars))

    def dump(
        self,
        output_file: str,
        print_mapping: bool = True,
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
