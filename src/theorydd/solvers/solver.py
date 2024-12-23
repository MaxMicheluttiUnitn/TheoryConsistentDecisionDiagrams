"""interface that all solvers must implement."""

from abc import ABC, abstractmethod

from pysmt.fnode import FNode


class SMTEnumerator(ABC):
    """interface that all solvers must implement.

    This interface must be implemented by all the solvers that are used to compute all-SMT.
    """

    def __init__(self):
        pass

    @abstractmethod
    def check_all_sat(self, phi: FNode, boolean_mapping: dict) -> bool:
        """check T-satisfiability of a formula"""
        pass

    @abstractmethod
    def get_theory_lemmas(self) -> list:
        """return the list of theory lemmas"""
        pass

    @abstractmethod
    def get_converter(self) -> dict:
        """return the converter for normalization of T-atoms"""
        pass

    @abstractmethod
    def get_models(self) -> list:
        """return the list of models"""
        pass
