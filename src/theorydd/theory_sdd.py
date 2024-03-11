"""theory SDD module"""

from array import array
import time
from typing import Dict, List, Set
from pysmt.fnode import FNode
from pysdd.sdd import SddManager, Vtree, SddNode, WmcManager
from theorydd import formula
from theorydd.lemma_extractor import extract, find_qvars
from theorydd.smt_solver import SMTSolver, SAT
from theorydd.smt_solver_partial import PartialSMTSolver
from theorydd._string_generator import (
    SDDSequentailStringGenerator,
    SequentialStringGenerator,
)
from theorydd.formula import get_atoms
from theorydd.walker_sdd import SDDWalker
from theorydd._dd_dump_util import save_sdd_object as _save_sdd_object
from theorydd.constants import SAT, UNSAT, VALID_VTREE
from theorydd.custom_exceptions import InvalidVTreeException

class TheorySDD:
    """class to generate and handle T-SDDs"""

    SDD: SddManager
    root: SddNode
    qvars: List
    mapping: Dict
    name_to_atom_map: Dict  # USED FOR SERIALIZATION
    vtree: Vtree

    def __init__(
        self,
        phi: FNode,
        solver: str = "total",
        computation_logger: Dict = None,
        verbose: bool = False,
        load_lemmas: str | None = None,
        tlemmas: List[FNode] = None,
        vtree_type: str = "balanced",
    ) -> None:
        if not vtree_type in VALID_VTREE:
            raise InvalidVTreeException("Invalid V-Tree type \""+str(vtree_type)+"\".\n Valid V-Tree types: "+str(VALID_VTREE))
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("T-SDD") is None:
            computation_logger["T-SDD"] = {}
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
        computation_logger["T-SDD"]["phi normalization time"] = elapsed_time
        if verbose:
            print("Loading Lemmas...")
        if tlemmas is not None:
            computation_logger["T-SDD"]["ALL SMT mode"] = "loaded"
            phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)
        elif load_lemmas is not None:
            computation_logger["T-BDD"]["ALL SMT mode"] = "loaded"
            tlemmas = formula.read_phi(load_lemmas)
            phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)
        else:
            computation_logger["T-BDD"]["ALL SMT mode"] = "computed"
            satisfiability, tlemmas = extract(
                phi,
                smt_solver,
                verbose=verbose,
                computation_logger=computation_logger["T-BDD"],
            )
            if satisfiability == SAT:
                phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)
            else:
                phi = formula.bottom()
                phi_and_lemmas = phi
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
        computation_logger["T-SDD"]["variable mapping creation time"] = elapsed_time

        # BUILDING V-TREE
        start_time = time.time()
        if verbose:
            print("Building V-Tree...")
        atoms = get_atoms(phi)
        var_count = len(atoms)
        string_generator = SDDSequentailStringGenerator()
        self.name_to_atom_map = {}
        for atom in atoms:
            self.name_to_atom_map[string_generator.next_string().upper()] = atom
        # print(name_to_atom_map)
        # for now just use appearance order in phi
        var_order = list(range(1, var_count + 1))
        self.vtree = Vtree(var_count, var_order, vtree_type)
        elapsed_time = time.time() - start_time
        if verbose:
            print("V-Tree built in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["V-Tree building time"] = elapsed_time

        # BUILDING SDD WITH WALKER
        start_time = time.time()
        if verbose:
            print("Building T-SDD...")
        self.manager = SddManager.from_vtree(self.vtree)
        sdd_literals = [self.manager.literal(i) for i in range(1, var_count + 1)]
        atom_literal_map = dict(zip(atoms, sdd_literals))
        walker = SDDWalker(atom_literal_map, self.manager)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        if verbose:
            print("SDD built in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["DD building time"] = elapsed_time

        # QUANTIFYING OVER FRESH T-ATOMS
        start_time = time.time()
        print("Quantifying over fresh T-atoms...")
        existential_map = [0]
        for smt_atom in atom_literal_map.keys():
            if smt_atom in self.qvars:
                existential_map.append(1)
            else:
                existential_map.append(0)
        self.root = self.manager.exists_multiple(array("i", existential_map), self.root)
        elapsed_time = time.time() - start_time
        print("Quantified over fresh T-atoms in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["fresh T-atoms quantification time"] = elapsed_time

    def __len__(self) -> int:
        return self.root.count()

    def count_nodes(self) -> int:
        """returns the number of nodes in the T-SDD"""
        return len(self)

    def count_vertices(self) -> int:
        """returns the number of nodes in the T-SDD"""
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
        """returns the amount of models in the T-SDD"""
        wmc: WmcManager = self.root.wmc(log_mode=False)
        return wmc.propagate() / (2 ** len(self.qvars))

    def dump(
        self,
        output_file: str,
        print_mapping: bool = True,
        dump_abstraction: bool = False,
    ) -> None:
        """save the DD on a file with graphviz"""
        start_time = time.time()
        print("Saving SDD...")
        if print_mapping:
            print("Mapping:")
            print(self.name_to_atom_map)
        if _save_sdd_object(
            self.root, output_file, self.name_to_atom_map, "SDD", dump_abstraction
        ):
            elapsed_time = time.time() - start_time
            print("SDD saved as " + output_file + " in ", elapsed_time, " seconds")
        else:
            print(
                "SDD could not be saved: The file format of ",
                output_file,
                " is not supported",
            )
