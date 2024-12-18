"""abstraction SDD module"""

import os
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
from theorydd.theory_sdd import vtree_load_from_folder as _vtree_load_from_folder
from theorydd._dd_dump_util import save_sdd_object as _save_sdd_object


class AbstractionSDD:
    """Python class to generate and handle abstraction SDDs.

    Abstraction SDDs are SDDs of the boolean abstraction of a normalized
    T-formula. They represent all the models of the abstraction
    of the formula i. e. all the truth assignments to boolean atoms and
    T-atoms that satisfy the formula in the boolean domain. These
    SDDs may however present T-inconsistencies.
    """

    SDD: SddManager
    root: SddNode
    mapping: Dict
    name_to_atom_map: Dict  # NEEDED FOR SERIALIZATION
    vtree: Vtree

    def __init__(self,
        phi: FNode,
        solver: str = "total",
        vtree_type: str = "balanced",
        verbose: bool = False,
        computation_logger: Dict = None,
        folder_name: str | None = None):
        """
        builds an AbstractionSDD

        Args:
            phi (FNode): a pysmt formula
            solver (str) ["partial"]: used for T-atoms normalization, can be set to "total" or "partial"
            vtree_type (str) ["balanced"]: used for Vtree generation. Available values in theorydd.constants.VALID_VTREE
            verbose (bool) [False]: set it to True to log computation on stdout
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
            folder_name (str | None) [None]: the path to a folder where data to load the AbstractionSDD is stored.
                If this is not None, then all other parameters are ignored
        """
        if folder_name is not None:
            self._load_from_folder(folder_name)
            return
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("Abstraction SDD") is None:
            computation_logger["Abstraction SDD"] = {}
        start_time = time.time()
        if verbose:
            print("Normalizing phi according to solver...")
        # THE SOLVER IS ONLY USED FOR ATOM NORMALIZATION
        if solver == "total":
            smt_solver = SMTSolver()
        else:
            smt_solver = PartialSMTSolver()
        phi = formula.get_normalized(phi, smt_solver.get_converter())
        elapsed_time = time.time() - start_time
        if verbose:
            print("Phi was normalized in ", elapsed_time, " seconds")
        computation_logger["Abstraction SDD"]["phi normalization time"] = elapsed_time

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
        computation_logger["Abstraction SDD"]["variable mapping creation time"] = elapsed_time

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
        computation_logger["Abstraction SDD"]["V-Tree building time"] = elapsed_time

        # BUILDING SDD WITH WALKER
        start_time = time.time()
        if verbose:
            print("Building Abstraction SDD...")
        self.manager = SddManager.from_vtree(self.vtree)
        sdd_literals = [self.manager.literal(i) for i in range(1, var_count + 1)]
        atom_literal_map = dict(zip(atoms, sdd_literals))
        walker = SDDWalker(atom_literal_map, self.manager)
        self.root = walker.walk(phi)
        elapsed_time = time.time() - start_time
        if verbose:
            print("Abstraction SDD built in ", elapsed_time, " seconds")
        computation_logger["Abstraction SDD"]["DD building time"] = elapsed_time

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

    def dump(
        self,
        output_file: str,
        print_mapping: bool = False,
        dump_abstraction: bool = False,
    ) -> None:
        """Save the AbstractionSDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
            print_mapping (bool) [False]: set it to True to print the mapping
                between the names of the atoms in the DD and the original atoms
            dump_abstraction (bool) [False]: set it to True to dump a DD
                with the names of the abstraction of the atoms instead of the
                full names of atoms
        """
        if print_mapping:
            print("Mapping:")
            print(self.name_to_atom_map)
        if not _save_sdd_object(
            self.root, output_file, self.name_to_atom_map, "SDD", dump_abstraction
        ):
            print(
                "SDD could not be saved: The file format of ",
                output_file,
                " is not supported",
            )

    def dump_vtree(self, output_file: str) -> None:
        """Save the AbstractionSDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
        """
        if not _save_sdd_object(
            self.vtree, output_file, self.name_to_atom_map, "VTree"
        ):
            print(
                "V-Tree could not be saved: The file format of ",
                output_file,
                " is not supported",
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
        formula.save_abstraction_function(self.mapping, folder_path+"/abstraction.json")
        # save sdd
        self.root.save(str.encode(folder_path+"/sdd.sdd"))

    def save_vtree_to_folder(self, folder_path: str) -> None:
        """Save the V-Tree in the specified folder

        Args:
            folder_path (str): the path to the output folder
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self.vtree.save(str.encode(folder_path+"/vtree.vtree"))

    def _load_from_folder(self, folder_path: str) -> None:
        """
        Load an AbstractionSDD from a folder
        
        Args:
            folder_path (str): the path to the folder where the data is stored
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder {folder_path} does not exist, cannot load AbstractionSDD")
        self.vtree = _vtree_load_from_folder(folder_path)
        self.manager = SddManager.from_vtree(self.vtree)
        self.root = self.manager.read_sdd_file(str.encode(f"{folder_path}/sdd.sdd"))
        self.mapping = formula.load_abstraction_function(folder_path+"/abstraction.json")
        self.name_to_atom_map = {v: k for k, v in self.mapping.items()}

def abstraction_sdd_load_from_folder(folder_path: str) -> AbstractionSDD:
    """
    Load an AbstractionSDD from a folder
    
    Args:
        folder_path (str): the path to the folder where the data is stored
    """
    return AbstractionSDD(None, folder_name=folder_path)
