"""interface that all solvers must implement."""

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List

from pysmt.fnode import FNode
from theorydd.constants import SAT, UNSAT
from theorydd.formula import get_normalized, get_atom_partitioning, get_true_given_atoms


class SMTEnumerator(ABC):
    """interface that all solvers must implement.

    This interface must be implemented by all the solvers that are used to compute all-SMT.
    """

    def __init__(self):
        self._tlemmas = []
        pass

    @abstractmethod
    def check_all_sat(self, phi: FNode, boolean_mapping: Dict | None = None) -> bool:
        """check T-satisfiability of a formula"""
        pass

    @abstractmethod
    def get_theory_lemmas(self) -> List[FNode]:
        """return the list of theory lemmas"""
        pass

    @abstractmethod
    def get_converter(self) -> object:
        """return the converter for normalization of T-atoms"""
        pass

    @abstractmethod
    def get_models(self) -> List:
        """return the list of models"""
        pass

    def enumerate_true(self, phi: FNode, stop_at_unsat: bool = False) -> bool:
        """enumerate all lemmas on the formula phi

        Args:
            phi (FNode): a pysmt formula
            stop_at_unsat (bool) [False]: if True, the enumeration stops as soon as an UNSAT partition is found

        Returns:
            bool: SAT or UNSAT, depending on satisfiability of phi
        """
        # normalize phi
        phi = get_normalized(phi, self.get_converter())

        # compute partitioning over the atoms of phi
        partitions = get_atom_partitioning(phi)

        complessive_sat_result = SAT

        all_lemmas = set()

        for partition in partitions:
            # compute true formula of partition
            partition_phi = get_true_given_atoms(partition)

            # check if partition is SAT and extract lemmas
            partition_sat_result = self.check_all_sat(partition_phi, boolean_mapping=None)

            # add lemmas to the set of all lemmas
            for lemma in self.get_theory_lemmas():
                all_lemmas.add(lemma)

            # if partition is UNSAT, the whole formula is UNSAT
            # therefore mark result as UNSAT

            # notice that partitions should never be UNSAT
            # since it is always possible to find a T-model
            # for a partition
            if partition_sat_result == UNSAT:
                complessive_sat_result = UNSAT
                # should I continue enumerating lemmas?
                if stop_at_unsat:
                    return UNSAT
        
        # store all lemmas
        self._tlemmas = list(all_lemmas)

        return complessive_sat_result
