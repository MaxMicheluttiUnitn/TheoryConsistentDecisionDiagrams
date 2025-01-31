"""abstraction BDD module"""

import logging
import os
from typing import Dict, List
from pysmt.fnode import FNode
from dd import cudd as cudd_bdd
from theorydd import formula
from theorydd.tdd.theory_bdd import TheoryBDD
from theorydd.solvers.solver import SMTEnumerator
from theorydd.util._utils import (
    cudd_dump as _cudd_dump,
    cudd_load as _cudd_load,
    get_solver as _get_solver,
)


class AbstractionBDD(TheoryBDD):
    """Python class to generate and handle abstraction BDDs.

    Abstraction BDDs are BDDs of the boolean abstraction of a normalized
    T-formula. They represent all the models of the abstraction
    of the formula i. e. all the truth assignments to boolean atoms and
    T-atoms that satisfy the formula in the boolean domain. These
    BDDs may however present T-inconsistencies.
    """

    def __init__(
        self,
        phi: FNode,
        solver: str | SMTEnumerator = "total",
        use_ordering: List[FNode] | None = None,
        computation_logger: Dict = None,
        folder_name: str | None = None,
    ):
        """
        builds an AbstractionBDD

        Args:
            phi (FNode): a pysmt formula
            solver (str | SMTEnumerator) ["total"]: used for T-atoms normalization, can be set to total,
                partial or extended_partial or a SMTEnumerator can be provided
            use_ordering (List[FNode] | None) [None]: a list of FNodes that will be used to order the BDD variables
            computation_logger (Dict) [None]: a dictionary that will be updated to store computation info
            folder_name (str | None) [None]: the path to a folder where data to load the AbstractionBDD is stored.
                If this is not None, then all other parameters are ignored
        """
        self.logger = logging.getLogger("abstraction_bdd")
        self.structure_name = "Abstraction BDD"
        if folder_name is not None:
            self._load_from_folder(folder_name, normalization_solver=solver)
            return
        super().__init__(
            phi,
            solver=solver,
            tlemmas=[formula.top()],
            load_lemmas=None,
            sat_result=None,
            use_ordering=use_ordering,
            computation_logger=computation_logger,
            folder_name=None,
        )

    def save_to_folder(self, folder_path: str) -> None:
        """Saves the Abstraction BDD to a folder

        Args:
            folder_path (str): the path to the folder where the BDD will be saved
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # SAVE MAPPING
        formula.save_abstraction_function(
            self.abstraction, f"{folder_path}/abstraction.json"
        )
        # SAVE BDD
        _cudd_dump(self.root, f"{folder_path}/abstraction_bdd_data")

    def _load_from_folder(
        self, folder_path: str, normalization_solver: SMTEnumerator | str = "total"
    ) -> None:
        """Loads an Abstraction BDD from a folder

        Args:
            folder_name (str): the path to the folder where the BDD is stored
            normalization_solver (SMTEnumerator | str) ["total"]: the solver used to normalize the T-atoms
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Cannot load Abstraction BDD: Folder {folder_path} does not exist")
        if not os.path.isfile(f"{folder_path}/abstraction.json"):
            raise FileNotFoundError(
                f"Cannot load Abstraction BDD: File {folder_path}/abstraction.json does not exist"
            )
        if isinstance(normalization_solver, str):
            smt_solver = _get_solver(normalization_solver)
        else:
            smt_solver = normalization_solver
        abstraction = formula.load_abstraction_function(
            f"{folder_path}/abstraction.json"
        )
        # apply normalization to the abstraction
        self.abstraction = {
            formula.get_normalized(k, smt_solver.get_converter()) : v
            for k, v in abstraction.items()
        }
        self.refinement = {v: k for k, v in self.abstraction.items()}
        self.bdd = cudd_bdd.BDD()
        self.root, ordering_dict = _cudd_load(
            f"{folder_path}/abstraction_bdd_data", self.bdd
        )
        self.ordering = [0] * len(ordering_dict)
        for k, v in ordering_dict.items():
            self.ordering[v] = self.refinement[k]
        self.qvars = []


def abstraction_bdd_load_from_folder(
    folder_path: str, normalizer_solver: SMTEnumerator | str = "total"
) -> AbstractionBDD:
    """Loads an Abstraction BDD from a folder

    Args:
        folder_path (str): the path to the folder where the BDD is saved
        normalizer_solver (SMTEnumerator | str) ["total"]: the solver used to normalize the T-atoms

    Returns:
        (AbstractionBDD) -> the Abstraction BDD loaded from the folder
    """
    return AbstractionBDD(None, folder_name=folder_path, solver=normalizer_solver)
