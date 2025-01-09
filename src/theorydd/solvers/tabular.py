"""this module handles interactions with the mathsat solver"""

import os
import re
import subprocess

import sys
from typing import List, Dict
from pysmt.fnode import FNode

# from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from theorydd.constants import (
    SAT,
    UNSAT,
    TABULAR_ALLSMT_COMMAND as _TABULAR_ALLSMT_COMMAND,
    TLEMMAS_FILE_REGEX as _TLEMMAS_FILE_REGEX,
)

# only used for normalization
from theorydd.solvers.mathsat_total import MathSATTotalEnumerator as _Enumerator
from theorydd.solvers.solver import SMTEnumerator
from theorydd.formula import get_normalized, save_phi, read_phi


class TabularSMTSolver(SMTEnumerator):
    """A wrapper for the tabular T-solver

    is_partial: bool [False]:   if True, the solver will only compute partial assignments,
                                which may have theory inconsistent extensions, but are
                                guaranteed to have at least one theory consistent extension
    """

    def __init__(self, is_partial: bool = False) -> None:
        if not os.path.isfile(_TABULAR_ALLSMT_COMMAND):
            raise FileNotFoundError(
                'The binary for the tabular AllSMT solver is missing. Please run "theorydd_install --tabular" to install or install manually.'
            )
        if not os.access(_TABULAR_ALLSMT_COMMAND, os.X_OK):
            raise PermissionError(
                "The binary for the tabular AllSMT solver is not executable. Please check the permissions and grant execution rights."
            )
        super().__init__()
        self.normalizer_solver = _Enumerator()
        self._tlemmas = []
        self._models = []
        self._converter = self.normalizer_solver.get_converter()
        self._atoms = []
        self._is_partial = is_partial

    def check_all_sat(
        self, phi: FNode, boolean_mapping: Dict[FNode, FNode] = None
    ) -> bool:
        """Computes All-SMT for the SMT-formula phi using partial assignment and Tsetsin CNF-ization

        Args:
            phi (FNode): a pysmt formula
            boolean_mapping (Dict[FNode, FNode]) [None]: unused, for compatibility with SMTSolver
        """
        # there may be some previously saved t-lemmas from a crashed run
        _clear_tlemmas()

        if boolean_mapping is not None:
            boolean_mapping = None
        self._tlemmas = []
        self._models = []
        self._atoms = []

        self._atoms = phi.get_atoms()

        normal_phi = get_normalized(phi, self.get_converter())

        # cannot use CNF-ization because it changes the important atoms of the formula
        # phi_tsetsin = PolarityCNFizer(nnf=True, mutex_nnf_labels=True).convert_as_formula(normal_phi)

        # save normalized phi on temporary smt file
        phi_file = "temp_phi.smt"
        # save_phi(phi_tsetsin, phi_file)
        save_phi(normal_phi, phi_file)

        if self._is_partial:
            minimize_models = "true"
        else:
            minimize_models = "false"

        # run solver with one hour timeout
        options = f"--debug.dump_theory_lemmas=true --dpll.store_tlemmas=true --theory.la.split_rat_eq=false --preprocessor.simplification=0 --preprocessor.toplevel_propagation=false --dpll.allsat_minimize_model={minimize_models}"

        command = f"timeout 3600 {_TABULAR_ALLSMT_COMMAND} {options} < {phi_file}"
        try:
            output_data = subprocess.check_output(command, shell=True, text=True)
        except subprocess.CalledProcessError as e:
            result = e.returncode
            _clear_tlemmas()
            if result == 124:
                print("Timeout")
                sys.exit(124)
            elif result == 1:
                print("Tabular Solver Error")
                sys.exit(1)
            elif result != 0:
                print("Error")
                sys.exit(result)

        for item in os.listdir():
            if re.search(_TLEMMAS_FILE_REGEX, item):
                tlemma = read_phi(item)
                normal_tlemma = get_normalized(tlemma, self.get_converter())
                self._tlemmas.append(normal_tlemma)

        # remove temporary files
        # lemmas
        _clear_tlemmas()
        # phi
        os.remove(phi_file)

        # read model
        # output syntax:
        # [MODELS] s MODEL COUNT <models>
        try:
            if not self._is_partial:
                total_models_tokenized = output_data.split("MODEL COUNT")
            else:
                total_models_tokenized = output_data.split(
                    "NUMBER OF PARTIAL ASSIGNMENTS"
                )
            if len(total_models_tokenized) != 2:
                raise ValueError
            total_models_string = total_models_tokenized[1].strip()
            total_models = int(total_models_string)
        except ValueError:
            total_models = 0

        # placeholder in order to ignore models but return a count
        self._models = [0] * total_models

        # remove temporary output file
        # os.remove(output_file)

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


class TabularTotalSMTSolver(TabularSMTSolver):
    """A wrapper for the tabular the TabularSMTSOlver 
    that always computyes total enumeration"""

    def __init__(self) -> None:
        super().__init__(is_partial=False)

class TabularPartialSMTSolver(TabularSMTSolver):
    """A wrapper for the tabular the TabularSMTSOlver 
    that always computes partial enumeration"""

    def __init__(self) -> None:
        super().__init__(is_partial=True)

def _clear_tlemmas():
    for item in os.listdir():
        if re.search(_TLEMMAS_FILE_REGEX, item):
            os.remove(item)


if __name__ == "__main__":
    _clear_tlemmas()
