"""abstraction SDD module"""

import time
from typing import Dict, List, Set
from pysmt.fnode import FNode
from pysdd.sdd import SddManager, Vtree, SddNode, WmcManager
from theorydd import formula
from theorydd.smt_solver import SMTSolver
from theorydd.smt_solver_partial import PartialSMTSolver
from theorydd._string_generator import (
    SDDSequentailStringGenerator,
    SequentialStringGenerator,
)
from theorydd.formula import get_atoms
from theorydd.walker_sdd import SDDWalker
from theorydd._dd_dump_util import save_sdd_object as _save_sdd_object


class AbstractionSDD:
    """class to generate and handle abstraction SDDs"""

    SDD: SddManager
    root: SddNode
    mapping: Dict
    name_to_atom_map: Dict  # USED FOR SERIALIZATION
    vtree: Vtree

    def __init__(
        self,
        phi: FNode,
        solver: str = "total",
        computation_logger: Dict = None,
        verbose: bool = False,
        vtree_type: str = "balanced",
    ) -> None:
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("SDD") is None:
            computation_logger["SDD"] = {}
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
        computation_logger["SDD"]["phi normalization time"] = elapsed_time

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
        computation_logger["SDD"]["variable mapping creation time"] = elapsed_time

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
        var_order = list(range(1, var_count + 1))
        self.vtree = Vtree(var_count, var_order, vtree_type)
        elapsed_time = time.time() - start_time
        if verbose:
            print("V-Tree built in ", elapsed_time, " seconds")
        computation_logger["SDD"]["V-Tree building time"] = elapsed_time

        # BUILDING SDD WITH WALKER
        start_time = time.time()
        if verbose:
            print("Building SDD...")
        self.manager = SddManager.from_vtree(self.vtree)
        sdd_literals = [self.manager.literal(i) for i in range(1, var_count + 1)]
        atom_literal_map = dict(zip(atoms, sdd_literals))
        walker = SDDWalker(atom_literal_map, self.manager)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        if verbose:
            print("SDD built in ", elapsed_time, " seconds")
        computation_logger["SDD"]["DD building time"] = elapsed_time

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
        return wmc.propagate()

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
