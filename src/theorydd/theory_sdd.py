"""theory SDD module"""

from array import array
import time
from typing import Dict, List, Set
from pysmt.fnode import FNode
from pysdd.sdd import SddManager, Vtree, SddNode, WmcManager
from theorydd import formula
from theorydd.lemma_extractor import extract, find_qvars
from theorydd.smt_solver import SMTSolver
from theorydd.smt_solver_full_partial import FullPartialSMTSolver
from theorydd.smt_solver_partial import PartialSMTSolver
from theorydd._string_generator import (
    SDDSequentailStringGenerator,
    SequentialStringGenerator,
)
from theorydd.formula import get_atoms
from theorydd.walker_sdd import SDDWalker
from theorydd._dd_dump_util import save_sdd_object as _save_sdd_object
from theorydd.constants import VALID_VTREE, VALID_SOLVER
from theorydd.custom_exceptions import InvalidVTreeException, InvalidSolverException


class TheorySDD:
    """Class to generate and handle T-SDDs

    T-SDDs are SDDs with a mixture of boolean atoms and T-atoms
    in which every enocded model represents a T-consistent truth
    assignment to the atoms of the encoded formula"""

    SDD: SddManager
    root: SddNode
    qvars: List
    mapping: Dict
    name_to_atom_map: Dict  # USED FOR SERIALIZATION
    vtree: Vtree

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTSolver | PartialSMTSolver | FullPartialSMTSolver = "partial",
        computation_logger: Dict = None,
        verbose: bool = False,
        load_lemmas: str | None = None,
        tlemmas: List[FNode] = None,
        vtree_type: str = "balanced",
    ) -> None:
        """Builds a T-SDD. The construction requires the
        computation of All-SMT for the provided formula to
        extract T-lemmas and the subsequent construction of
        a SDD of phi & lemmas

        Args:
            phi (FNode) : a pysmt formula
            solver (str | SMTSolver | PartialSMTSolver) ["partial"]: specifies which solver to use for All-SMT computation.
                Valid solvers are "partial" and "total", or you can pass an instance of a SMTSolver or PartialSMTSolver
            load_lemmas (str) [None]: specify the path to a file from which to load phi & lemmas.
                This skips the All-SMT computation
            tlemmas (List[Fnode]): use previously computed tlemmas.
                This skips the All-SMT computation
            vtree_type (str) ["balanced"]: used for Vtree generation.
                Available values in theorydd.constants.VALID_VTREE
            verbose (bool) [False]: set it to True to log computation on stdout
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
        """
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
        start_time = time.time()
        if verbose:
            print("Normalizing phi according to solver...")
        if isinstance(solver, str):
            if solver == "total":
                smt_solver = SMTSolver()
            elif solver == "partial":
                smt_solver = PartialSMTSolver()
            elif solver == "full_partial":
                smt_solver = FullPartialSMTSolver()
            else:
                raise InvalidSolverException(
                    solver
                    + " is not a valid solvers. Valid solvers: "
                    + str(VALID_SOLVER)
                )
        else:
            smt_solver = solver
        phi = formula.get_normalized(phi, smt_solver.get_converter())
        elapsed_time = time.time() - start_time
        if verbose:
            print("Phi was normalized in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["phi normalization time"] = elapsed_time
        if verbose:
            print("Loading Lemmas...")
        if tlemmas is not None:
            computation_logger["T-SDD"]["ALL SMT mode"] = "loaded"
        elif load_lemmas is not None:
            computation_logger["T-SDD"]["ALL SMT mode"] = "loaded"
            tlemmas = [formula.read_phi(load_lemmas)]
        else:
            computation_logger["T-SDD"]["ALL SMT mode"] = "computed"
            _satisfiability, tlemmas, _bm = extract(
                phi,
                smt_solver,
                verbose=verbose,
                computation_logger=computation_logger["T-SDD"],
            )
        tlemmas = list(
            map(
                lambda l: formula.get_normalized(l, smt_solver.get_converter()), tlemmas
            )
        )
        phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)
        self.qvars = find_qvars(
            phi,
            phi_and_lemmas,
            verbose=verbose,
            computation_logger=computation_logger["T-SDD"],
        )
        # phi = phi_and_lemmas

        # CREATING VARIABLE MAPPING
        start_time = time.time()
        if verbose:
            print("Creating mapping...")
        self.mapping = {}
        atoms = get_atoms(phi_and_lemmas)
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
        atoms = get_atoms(phi_and_lemmas)
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
            print("Preparing to build T-SDD...")
        self.manager = SddManager.from_vtree(self.vtree)
        sdd_literals = [self.manager.literal(i) for i in range(1, var_count + 1)]
        atom_literal_map = dict(zip(atoms, sdd_literals))
        walker = SDDWalker(atom_literal_map, self.manager)
        if verbose:
            print("BDD preparation phase completed in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["DD preparation time"] = elapsed_time

        start_time = time.time()
        if verbose:
            print("Building SDD for phi...")
        phi_sdd = walker.walk(phi)
        elapsed_time = time.time() - start_time
        if verbose:
            print("SDD built in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["phi DD building time"] = elapsed_time

        # BUILDING T-LEMMAS SDD
        start_time = time.time()
        if verbose:
            print("Building T-SDD for big and of t-lemmas...")
        tlemmas_sdd = walker.walk(formula.big_and(tlemmas))
        elapsed_time = time.time() - start_time
        if verbose:
            print("SDD built in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["phi DD building time"] = elapsed_time

        # QUANTIFYING OVER FRESH T-ATOMS
        start_time = time.time()
        if verbose:
            print("Quantifying over fresh T-atoms...")
        existential_map = [0]
        for smt_atom in atom_literal_map.keys():
            if smt_atom in self.qvars:
                existential_map.append(1)
            else:
                existential_map.append(0)
        tlemmas_sdd = self.manager.exists_multiple(
            array("i", existential_map), tlemmas_sdd
        )
        elapsed_time = time.time() - start_time
        if verbose:
            print("Quantified over fresh T-atoms in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["fresh T-atoms quantification time"] = elapsed_time

        # JOINING PHI SDD AND TLEMMAS SDD
        start_time = time.time()
        if verbose:
            print("Joining phi BDD and lemmas T-SDD...")
        self.root = phi_sdd & tlemmas_sdd
        elapsed_time = time.time() - start_time
        if verbose:
            print("T-SDD for phi and t-lemmas joint in ", elapsed_time, " seconds")
        computation_logger["T-SDD"]["DD joining time"] = elapsed_time

    def __len__(self) -> int:
        return max(self.root.count(), 1)

    def count_nodes(self) -> int:
        """Returns the number of nodes in the T-SDD"""
        return len(self)

    def count_vertices(self) -> int:
        """Returns the number of nodes in the T-SDD"""
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
        """Returns the amount of models in the T-SDD"""
        wmc: WmcManager = self.root.wmc(log_mode=False)
        return wmc.propagate() / (2 ** len(self.qvars))

    def dump(
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

    def dump_vtree(self, output_file: str) -> None:
        """Save the T-SDD on a file with Graphviz

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

    def get_mapping(self) -> Dict:
        """Returns the variable mapping used"""
        return self.mapping

    def pick(self) -> Dict[FNode, bool]:
        """Returns a model of the encoded formula"""
        raise NotImplementedError()
        return {}

    def pick_all(self) -> List[Dict[FNode, bool]]:
        """returns a list of all the models in the encoded formula"""
        raise NotImplementedError()
        if self.root.is_false():
            return []
        return []
