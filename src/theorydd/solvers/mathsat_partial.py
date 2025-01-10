"""this module handles interactions with the mathsat solver"""

from typing import List, Dict
from pysmt.shortcuts import Solver
from pysmt.fnode import FNode
import mathsat
from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from theorydd.constants import SAT, UNSAT
from theorydd.solvers.solver import SMTEnumerator


def _allsat_callback(model, converter, models):
    """callback for all-sat"""
    py_model = {converter.back(v) for v in model}
    models.append(py_model)
    return 1


class MathSATPartialEnumerator(SMTEnumerator):
    """A wrapper for the mathsat T-solver

    Computes all-SMT by only computing partial assignments without extending them.
    This always guarantees at least one T-SAT extension of each partial assignment,
    but some T-inconsistent extension may not be ruled out by the computed T-lemmas."""

    def __init__(self) -> None:
        super().__init__()
        solver_options_dict = {
            "dpll.allsat_minimize_model": "true",  # - partial truth assignments
            # "theory.pure_literal_filtering": "true",
            # "dpll.allsat_allow_duplicates": "false", # - to produce not necessarily disjoint truth assignments.
            #                                          # can be set to true only if minimize_model=true.
            # - necessary to disable some processing steps
            "preprocessor.toplevel_propagation": "false",
            "preprocessor.simplification": "0",  # from mathsat
            "dpll.store_tlemmas": "true",  # - necessary to obtain t-lemmas
            "theory.la.split_rat_eq": "false",
        }
        self.solver = Solver("msat", solver_options=solver_options_dict)
        self._last_phi = None
        self._tlemmas = []
        self._models = []
        self._converter = self.solver.converter
        self._atoms = []

    def check_all_sat(
        self, phi: FNode, boolean_mapping: Dict[FNode, FNode] | None = None
    ) -> bool:
        """Computes All-SMT for the SMT-formula phi generating partial assignments and using Tsetsin CNF-ization

        Args:
            phi (FNode): a pysmt formula
            boolean_mapping (Dict[FNode, FNode]) [None]: unused, for compatibility with SMTSolver
        """
        if boolean_mapping is not None:
            boolean_mapping = None

        self._last_phi = phi
        self._tlemmas = []
        self._models = []
        self._atoms = []

        self._atoms = phi.get_atoms()

        self.solver.reset_assertions()
        phi_tsetsin = PolarityCNFizer(
            nnf=True, mutex_nnf_labels=True
        ).convert_as_formula(phi)
        self.solver.add_assertion(phi_tsetsin)

        self._models = []
        mathsat.msat_all_sat(
            self.solver.msat_env(),
            self.get_converted_atoms(self._atoms),
            # self.get_converted_atoms(
            #    list(boolean_mapping.keys())),
            callback=lambda model: _allsat_callback(
                model, self._converter, self._models
            ),
        )

        self._tlemmas = [
            self._converter.back(l)
            for l in mathsat.msat_get_theory_lemmas(self.solver.msat_env())
        ]

        # phi_plus_lemmas = And(phi, *self._tlemmas)
        # self.solver_total.add_assertion(phi_plus_lemmas)

        if len(self._models) == 0:
            return UNSAT
        return SAT

    def get_theory_lemmas(self) -> List[FNode]:
        """Returns the theory lemmas found during the All-SAT computation"""
        return self._tlemmas

    def get_models(self) -> List:
        """Returns the models found during the All-SAT computation"""
        return self._models

    def get_converter(self):
        """Returns the converter used for the normalization of T-atoms"""
        return self._converter

    def get_converted_atoms(self, atoms):
        """Returns a list of normalized atoms"""
        return [self._converter.convert(a) for a in atoms]
