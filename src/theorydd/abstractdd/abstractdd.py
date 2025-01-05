"""interface for Abstract DDs"""

from abc import ABC, abstractmethod
import logging
import time
from typing import Dict

from pysmt.fnode import FNode

from theorydd.formula import get_atoms
from theorydd.util._string_generator import SequentialStringGenerator


class AbstractDD(ABC):
    """interface for Abstract DDs

    This interface must be implemented by all the Abstract DDs that are used to compute all-SMT.
    """

    def __init__(self):
        self.logger = logging.getLogger("thoerydd_abstractdd")

    def _compute_mapping(
        self, phi: FNode, computation_logger: dict
    ) -> Dict[FNode, str]:
        """computes the mapping"""
        start_time = time.time()
        self.logger.info("Creating mapping...")
        atoms = get_atoms(phi)
        string_generator = SequentialStringGenerator()
        mapping = {}
        for atom in atoms:
            mapping[atom] = string_generator.next_string()
        elapsed_time = time.time() - start_time
        self.logger.info("Mapping created in %s seconds", str(elapsed_time))
        computation_logger["variable mapping creation time"] = elapsed_time
        return mapping

    @abstractmethod
    def _load_from_folder(self, folder_path: str):
        """loads the DD from a folder"""
        pass

    @abstractmethod
    def save_to_folder(self, folder_path: str):
        """saves the DD to a folder"""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """returns the number of nodes in the DD"""
        pass

    @abstractmethod
    def count_nodes(self) -> int:
        """Returns the number of nodes in the DD"""
        pass

    @abstractmethod
    def count_vertices(self) -> int:
        """Returns the number of nodes in the DD"""
        pass

    @abstractmethod
    def count_models(self) -> int:
        """Returns the amount of models in the DD"""
        pass

    @abstractmethod
    def graphic_dump(self, output_file: str):
        """dumps the DD graphically"""
        pass

    @abstractmethod
    def get_mapping(self) -> Dict[FNode, str]:
        """returns the mapping"""
        pass
