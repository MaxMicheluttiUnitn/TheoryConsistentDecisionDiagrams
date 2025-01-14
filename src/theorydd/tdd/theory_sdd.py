"""theory SDD module"""

from array import array
import json
import logging
import os
import time
from typing import Dict, List, Set
from collections.abc import Iterator
from pysmt.fnode import FNode
from pysdd.sdd import SddManager, Vtree, SddNode, WmcManager
from theorydd import formula
from theorydd.solvers.lemma_extractor import find_qvars
from theorydd.solvers.solver import SMTEnumerator
from theorydd.tdd.theory_dd import TheoryDD
from theorydd.formula import get_atoms
from theorydd.util._utils import get_solver as _get_solver
from theorydd.walkers.walker_sdd import SDDWalker
from theorydd.util._dd_dump_util import save_sdd_object as _save_sdd_object
from theorydd.constants import VALID_VTREE, SAT
from theorydd.util.custom_exceptions import InvalidVTreeException


class TheorySDD(TheoryDD):
    """Class to generate and handle T-SDDs

    T-SDDs are SDDs with a mixture of boolean atoms and T-atoms
    in which every enocded model represents a T-consistent truth
    assignment to the atoms of the encoded formula"""

    SDD: SddManager
    root: SddNode
    qvars: List
    abstraction: Dict[FNode, int]
    refinement: Dict[int, FNode]
    vtree: Vtree
    atom_literal_map: Dict  # Dict[FNode, SddLiteral]

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTEnumerator = "total",
        computation_logger: Dict = None,
        load_lemmas: str | None = None,
        sat_result: bool | None = None,
        tlemmas: List[FNode] = None,
        vtree_type: str = "balanced",
        folder_name: str | None = None,
    ) -> None:
        """Builds a T-SDD. The construction requires the
        computation of All-SMT for the provided formula to
        extract T-lemmas and the subsequent construction of
        a SDD of phi & lemmas

        Args:
            phi (FNode) : a pysmt formula
            solver (str | SMTEnumerator) ["partial"]: specifies which solver to use for All-SMT computation.
                Valid solvers are "total", "partial" and "extended_partial", or you can pass an instance of a SMTEnumerator
            load_lemmas (str) [None]: specify the path to a file from which to load phi & lemmas.
                This skips the All-SMT computation
            tlemmas (List[Fnode]): use previously computed tlemmas.
                This skips the All-SMT computation
            vtree_type (str) ["balanced"]: used for Vtree generation.
                Available values in theorydd.constants.VALID_VTREE
            sat_result (bool) [None]: the result of the All-SMT computation. This value is overwritten if t-lemmas are not provided!!!ù
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
            folder_name (str | None) [None]: the path to a folder where data to load the T-SDD is stored.
                If this is not None, then all other parameters are ignored
        """
        super().__init__()
        self.logger = logging.getLogger("theorydd_tsdd")

        if folder_name is not None:
            self._load_from_folder(folder_name)
            return
        if vtree_type not in VALID_VTREE:
            raise InvalidVTreeException(
                'Invalid V-Tree type "'
                + str(vtree_type)
                + '".\n Valid V-Tree types: '
                + str(VALID_VTREE)
            )
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("T-SDD") is None:
            computation_logger["T-SDD"] = {}
        # get the solver
        if isinstance(solver, str):
            smt_solver = _get_solver(solver)
        else:
            smt_solver = solver

        # normalize phi
        phi = self._normalize_input(phi, smt_solver, computation_logger["T-SDD"])

        # EXTRACTING T-LEMMAS
        tlemmas, sat_result = self._load_lemmas(
            phi,
            smt_solver,
            tlemmas,
            load_lemmas,
            sat_result,
            computation_logger["T-SDD"],
        )

        # COMPUTE PHI AND LEMMAS
        phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)

        # FINDING QVARS
        self.qvars = find_qvars(
            phi,
            phi_and_lemmas,
            computation_logger=computation_logger["T-SDD"],
        )

        atoms = get_atoms(phi_and_lemmas)

        # CREATING VARIABLE MAPPING
        self.abstraction = self._compute_mapping(atoms, computation_logger["T-SDD"])
        self.refinement = {v: k for k, v in self.abstraction.items()}

        # BUILDING V-TREE
        self._build_vtree(vtree_type, computation_logger["T-SDD"])

        # BUILDING SDD WITH WALKER
        start_time = time.time()
        self.logger.info("Preparing to build T-SDD...")
        self.manager = SddManager.from_vtree(self.vtree)
        sdd_literals = [
            self.manager.literal(i) for i in range(1, len(self.abstraction.keys()) + 1)
        ]
        self.atom_literal_map = self._get_atom_literal_map(sdd_literals)
        walker = SDDWalker(self.atom_literal_map, self.manager)
        elapsed_time = time.time() - start_time
        self.logger.info(
            "SDD preparation phase completed in %s seconds", str(elapsed_time)
        )
        computation_logger["T-SDD"]["DD preparation time"] = elapsed_time

        if sat_result is None or sat_result == SAT:
            self.root = self._build(phi, tlemmas, walker, computation_logger["T-SDD"])
        else:
            self.root = self._build_unsat(walker, computation_logger["T-SDD"])

    def _get_atom_literal_map(self, sdd_literals) -> Dict:
        """computes the atom literal map"""
        var_count = len(self.abstraction.keys())
        atom_to_literal_map = {}
        for i in range(1, var_count + 1):
            atom_to_literal_map[self.refinement[i]] = sdd_literals[i - 1]
        return atom_to_literal_map

    def _compute_mapping(
        self, atoms: List[FNode], computation_logger: dict
    ) -> Dict[FNode, int]:
        """computes the mapping"""
        start_time = time.time()
        self.logger.info("Creating mapping...")
        mapping = {}
        count = 1
        for atom in atoms:
            mapping[atom] = count
            count += 1
        elapsed_time = time.time() - start_time
        self.logger.info("Mapping created in %s seconds", str(elapsed_time))
        computation_logger["variable mapping creation time"] = elapsed_time
        return mapping

    def _enumerate_qvars(self, tlemmas_dd, mapped_qvars) -> object:
        """Enumerates over the fresh T-atoms in the T-lemmas"""
        existential_map = [0]
        for smt_atom in self.atom_literal_map.keys():
            if smt_atom in self.qvars:
                existential_map.append(1)
            else:
                existential_map.append(0)
        return self.manager.exists_multiple(array("i", existential_map), tlemmas_dd)

    def _build_vtree(self, vtree_type, computation_logger: Dict) -> None:
        start_time = time.time()
        self.logger.info("Building V-Tree...")
        # for now just use appearance order in phi
        var_count = len(self.abstraction.keys())
        var_order = list(range(1, var_count + 1))
        self.vtree = Vtree(var_count, var_order, vtree_type)
        elapsed_time = time.time() - start_time
        self.logger.info("V-Tree built in %s seconds", str(elapsed_time))
        computation_logger["V-Tree building time"] = elapsed_time

    def __len__(self) -> int:
        return max(self.root.count(), 1)

    def count_nodes(self) -> int:
        """Returns the number of nodes in the T-SDD"""
        return len(self)

    def count_vertices(self) -> int:
        """Returns the number of nodes in the T-SDD"""
        if self.root.is_true() or not self.root.is_decision() or self.root.is_false():
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

    def _get_care_vars(self) -> List[int]:
        """gets the labels of the variables that are not in self.qvars"""
        mapped_qvars = set([self.abstraction[i] for i in self.qvars])
        all_vars = set(self.abstraction.values())
        return all_vars.difference(mapped_qvars)

    def is_sat(self) -> bool:
        """Returns True if the encoded formula is satisfiable"""
        return self.root != self.manager.false()

    def is_valid(self) -> bool:
        """Returns True if the encoded formula is valid"""
        return self.root == self.manager.true()

    def condition(self, label: int) -> None:
        """Conditions the T-SDD over the given label.
        If the label is negative, than the label
        is considered negated

        Args:
            label (int): the label that is conditioned
        """
        negated = False
        if label < 0:
            negated = True
            label = -label
        key = self.refinement[label]
        condition_sdd = self.atom_literal_map[key]
        if negated:
            condition_sdd = ~condition_sdd
        self.root = self.root & condition_sdd

    def count_models(self) -> int:
        """Returns the amount of models in the T-SDD"""
        wmc: WmcManager = self.root.wmc(log_mode=False)
        return wmc.propagate() / (2 ** len(self.qvars))

    def graphic_dump(
        self,
        output_file: str,
        dump_abstraction: bool = True,
    ) -> None:
        """Save the T-SDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
            dump_abstraction (bool) [True]: set it to True to dump a DD
                with the names of the abstraction of the atoms instead of the
                full names of atoms
        """
        start_time = time.time()
        self.logger.info("Saving SDD...")
        if not dump_abstraction:
            raise NotImplementedError()
        # FIX THIS IN THE FUTURE:
        # SDD uses labels from A to Z
        # if less than 26 variables are prinnted
        # or labels as n1234 if more than 26
        # this is not very manageable in
        # the geenral case since some
        # labels may not appear in the SDD
        if _save_sdd_object(
            self.root, output_file, self.refinement, "SDD", dump_abstraction
        ):
            elapsed_time = time.time() - start_time
            self.logger.info(
                "SDD saved as %s in %s seconds", output_file, str(elapsed_time)
            )
        else:
            self.logger.info(
                "SDD could not be saved: The file format of %s is not supported",
                output_file,
            )

    def graphic_dump_vtree(self, output_file: str) -> None:
        """Save the T-SDD on a file with Graphviz

        Args:
            output_file (str): the path to the output file
        """
        if not _save_sdd_object(self.vtree, output_file, self.refinement, "VTree"):
            self.logger.info(
                "V-Tree could not be saved: The file format of %s is not supported",
                output_file,
            )

    def get_mapping(self) -> Dict:
        """Returns the variable mapping used"""
        return self.abstraction
    
    def _refine_model(self, model: Dict[int,int]) -> Dict[FNode, bool]:
        """Refines a model from the SDD to the original formula"""
        refined_model = {}
        for key, value in model.items():
            atom = self.refinement[key]
            if atom in self.qvars:
                continue
            if value == 0:
                refined_model[atom] = False
            else:
                refined_model[atom] = True
        return refined_model

    def pick(self) -> Dict[FNode, bool] | None:
        """Returns a model of the encoded formula"""
        if not self.is_sat():
            return None
        for mod in self.root.models():
            return self._refine_model(mod)
        
    def pick_all_iter(self) -> Iterator[Dict[FNode, bool]]:
        """Returns an iterator over the models of the encoded formula"""
        for mod in self.root.models():
            yield self._refine_model(mod)

    def pick_all(self) -> List[Dict[FNode, bool]]:
        """returns a list of all the models in the encoded formula"""
        if not self.is_sat():
            return []
        items = []
        for mod in self.root.models():
            items.append(self._refine_model(mod))
        return items

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
        # SAVE QVARS
        qvars_indexes = [self.abstraction[qvar] for qvar in self.qvars]
        with open(f"{folder_path}/qvars.qvars", "w", encoding="utf8") as out:
            json.dump(qvars_indexes, out)
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
            raise FileNotFoundError("The folder does not exist")
        self.vtree = vtree_load_from_folder(folder_path)
        self.abstraction = formula.load_abstraction_function(
            folder_path + "/abstraction.json"
        )
        self.manager = SddManager.from_vtree(self.vtree)
        self.refinement = {v: k for k, v in self.abstraction.items()}
        sdd_literals = [
            self.manager.literal(i) for i in range(1, len(self.abstraction.keys()) + 1)
        ]
        self.atom_literal_map = self._get_atom_literal_map(sdd_literals)
        self.root = self.manager.read_sdd_file(str.encode(f"{folder_path}/sdd.sdd"))
        with open(f"{folder_path}/qvars.qvars", "r", encoding="utf8") as input_data:
            qvars_indexes = json.load(input_data)
            self.qvars = [self.refinement[qvar_id] for qvar_id in qvars_indexes]


def vtree_load_from_folder(folder_path: str) -> Vtree:
    """Load a V-Tree from the specified folder

    Args:
        folder_path (str): the path to the folder containing the V-Tree
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError("The folder does not exist")
    return Vtree(filename=folder_path + "/vtree.vtree")


def tsdd_load_from_folder(folder_path: str) -> TheorySDD:
    """Load a T-SDD from the specified folder

    Args:
        folder_path (str): the path to the folder containing the T-SDD
    """
    return TheorySDD(None, folder_name=folder_path)

if __name__ == "__main__":
    from theorydd.formula import default_phi
    phi = default_phi()
    tsdd = TheorySDD(phi)
    tsdd.pick_all()
