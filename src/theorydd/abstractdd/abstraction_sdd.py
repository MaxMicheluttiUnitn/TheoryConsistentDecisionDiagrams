"""abstraction SDD module"""

import logging
import os
from typing import Dict
from pysmt.fnode import FNode
from pysdd.sdd import SddManager, Vtree
from theorydd.solvers.solver import SMTEnumerator
from theorydd import formula
from theorydd.tdd.theory_sdd import (
    TheorySDD,
    vtree_load_from_folder as _vtree_load_from_folder)
from theorydd.util._utils import get_solver as _get_solver


class AbstractionSDD(TheorySDD):
    """Python class to generate and handle abstraction SDDs.

    Abstraction SDDs are SDDs of the boolean abstraction of a normalized
    T-formula. They represent all the models of the abstraction
    of the formula i. e. all the truth assignments to boolean atoms and
    T-atoms that satisfy the formula in the boolean domain. These
    SDDs may however present T-inconsistencies.
    """

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTEnumerator = "total",
        vtree_type: str = "balanced",
        use_vtree: Vtree | None = None,
        use_abstraction: Dict[FNode, int] | None = None,
        computation_logger: Dict = None,
        folder_name: str | None = None,
    ):
        """
        builds an AbstractionSDD

        Args:
            phi (FNode): a pysmt formula
            solver (str | SMTEnumerator) ["total"]: used for T-atoms normalization, can be set to "total", "partial" or "extended_partial"
                or a SMTEnumerator instance can be provided
            vtree_type (str) ["balanced"]: used for Vtree generation. Available values in theorydd.constants.VALID_VTREE
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
            folder_name (str | None) [None]: the path to a folder where data to load the AbstractionSDD is stored.
                If this is not None, then all other parameters are ignored
        """
        
        self.logger = logging.getLogger("theorydd_abstraction_sdd")
        self.structure_name = "Abstraction SDD"
        if folder_name is not None:
            self._load_from_folder(folder_name, normalization_solver=solver)
            return
        super().__init__(
            phi,
            solver=solver,
            tlemmas=[formula.top()],
            load_lemmas=None,
            sat_result=None,
            vtree_type=vtree_type,
            use_vtree=use_vtree,
            use_abstraction=use_abstraction,
            folder_name=None,
            computation_logger=computation_logger,
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
        formula.save_abstraction_function(
            self.abstraction, folder_path + "/abstraction.json"
        )
        # save sdd
        self.root.save(str.encode(folder_path + "/sdd.sdd"))

    def _load_from_folder(self, folder_path: str, normalization_solver: SMTEnumerator | str = "total") -> None:
        """
        Load an AbstractionSDD from a folder

        Args:
            folder_path (str): the path to the folder where the data is stored
            normalization_solver (SMTEnumerator | str) ["total"]: the solver used to normalize the T-atoms
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(
                f"Cannot load Abstraction SDD: Folder {folder_path} does not exist"
            )
        if not os.path.isfile(f"{folder_path}/abstraction.json"):
            raise FileNotFoundError(
                f"Cannot load Abstraction SDD: File {folder_path}/abstraction.json does not exist"
            )
        if not os.path.isfile(f"{folder_path}/sdd.sdd"):
            raise FileNotFoundError(
                f"Cannot load Abstraction SDD: File {folder_path}/sdd.sdd does not exist"
            )
        if isinstance(normalization_solver, str):
            smt_solver = _get_solver(normalization_solver)
        else:
            smt_solver = normalization_solver
        self.vtree = _vtree_load_from_folder(folder_path)
        self.manager = SddManager.from_vtree(self.vtree)
        self.root = self.manager.read_sdd_file(str.encode(f"{folder_path}/sdd.sdd"))
        abstraction = formula.load_abstraction_function(folder_path + "/abstraction.json")
        self.abstraction = {formula.get_normalized(k, smt_solver.get_converter()): v for k, v in abstraction.items()}
        self.refinement = {v: k for k, v in self.abstraction.items()}
        self.qvars = []
        sdd_literals = [
            self.manager.literal(i) for i in range(1, len(self.abstraction) + 1)
        ]
        self.atom_literal_map = self._get_atom_literal_map(sdd_literals)


def abstraction_sdd_load_from_folder(folder_path: str, normalizer_solver: SMTEnumerator | str = "total") -> AbstractionSDD:
    """
    Load an AbstractionSDD from a folder

    Args:
        folder_path (str): the path to the folder where the data is stored
        normalizer_solver (SMTEnumerator | str) ["total"]: the solver used to normalize the T-atoms
    """
    return AbstractionSDD(None, folder_name=folder_path, solver=normalizer_solver)
