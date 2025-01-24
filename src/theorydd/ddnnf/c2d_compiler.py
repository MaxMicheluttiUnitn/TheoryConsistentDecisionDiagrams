"""midddleware for pysmt-c2d compatibility"""

import logging
import os
import time
from typing import Dict, List, Tuple
from pysmt.shortcuts import (
    read_smtlib,
    And,
    Or,
    get_atoms,
    TRUE,
    FALSE,
    Not,
)
from pysmt.fnode import FNode
from allsat_cnf.label_cnfizer import LabelCNFizer
from theorydd.formula import save_refinement, load_refinement, get_phi_and_lemmas as _get_phi_and_lemmas
from theorydd.constants import (
    UNSAT,
    C2D_COMMAND as _C2D_COMMAND
)
from theorydd.formula import get_normalized
from theorydd.solvers.mathsat_total import MathSATTotalEnumerator

from theorydd.ddnnf.ddnnf_compiler import DDNNFCompiler

class C2DCompiler(DDNNFCompiler):
    """an object responsible for compiling pysmt formulas in dDNNF format through the c2d compiler"""

    def __init__(self):
        # check if c2d is available and executable
        if not os.path.isfile(_C2D_COMMAND):
            raise FileNotFoundError(
                "The binary for the c2d compiler is missing. Please run \"theorydd_install --c2d\" to install or install manually.")
        if not os.access(_C2D_COMMAND, os.X_OK):
            raise PermissionError(
                "The c2d binary is not executable. Please check the permissions for the file and grant execution rights.")

        super().__init__()
        self.logger = logging.getLogger("c2d_ddnnf_compiler")
        self.normalizing_solver = MathSATTotalEnumerator()


    def from_smtlib_to_dimacs_file(
        self,
        phi: FNode,
        dimacs_file: str,
        tlemmas: List[FNode] | None = None,
        sat_result: bool | None = None,
        quantify_tseitsin: bool = False,
        do_not_quantify: bool = False,
        quantification_file: str = "quantification.exist",
    ) -> None:
        """
        translates an SMT formula in DIMACS format and saves it on file.
        All fresh variables are saved inside quantification_file.

        This function also resets the abstraction and refinement functions.

        Args:
            phi (FNode) -> the pysmt formula to be translated
            dimacs_file (str) -> the path to the file where the dimacs output need to be saved
            tlemmas (List[FNode] | None) -> a list of theory lemmas to be added to the formula
            sat_result (bool | None) -> the result of the SAT check on the formula
            quantify_tseitsin (bool) -> if True, the compiler will quantify over the tseitsin fresh variables
            do_not_quantify (bool) -> if True, the compiler will not quantify over the fresh variables
            quantification_file (str) -> the path to the file where the quantified variables
                need to be saved
        """
        # solver to normalize phi
        if tlemmas is None:
            phi_and_lemmas = phi
        else:
            phi_and_lemmas = _get_phi_and_lemmas(phi, tlemmas)
        # normalize phi and lemmas
        phi_and_lemmas = get_normalized(phi_and_lemmas, self.normalizing_solver.get_converter())
        phi_cnf: FNode = LabelCNFizer().convert_as_formula(phi_and_lemmas)
        phi_atoms: frozenset = get_atoms(phi)
        phi_cnf_atoms: frozenset = get_atoms(phi_cnf)
        if do_not_quantify:
            fresh_atoms: List[FNode] = []
        elif quantify_tseitsin:
            fresh_atoms: List[FNode] = list(phi_cnf_atoms.difference(phi_atoms))
        else:
            phi_and_lemmas_atoms: frozenset = get_atoms(phi_and_lemmas)
            fresh_atoms: List[FNode] = list(phi_and_lemmas_atoms.difference(phi_atoms))

        count = 1
        self.abstraction = {}
        self.refinement = {}
        for atom in phi_cnf_atoms:
            self.abstraction[atom] = count
            self.refinement[count] = atom
            count += 1

        # SAVE QUANTIFICATION FILE
        self._save_quantification_file(quantification_file, fresh_atoms)

        # check if formula is top
        if phi_cnf.is_true():
            self.write_dimacs_true(dimacs_file)
            return

        # check if formula is bottom
        if phi_cnf.is_false() or sat_result == UNSAT:
            self.write_dimacs_false(dimacs_file)
            return

        # CONVERTNG IN DIMACS FORMAT AND SAVING ON FILE
        self.write_dimacs(dimacs_file, phi_cnf)

    def _save_quantification_file(self, quantification_file: str, fresh_atoms: List[FNode]) -> None:
        with open(quantification_file, "w", encoding="utf8") as quantification_out:
            quantified_indexes = [str(self.abstraction[atom])
                                  for atom in fresh_atoms]
            quantified_indexes_str: str = " ".join(quantified_indexes)
            quantification_out.write(
                f"{len(quantified_indexes)} {quantified_indexes_str}")

    def from_nnf_to_pysmt(self, nnf_file: str) -> Tuple[FNode, int, int]:
        """
        Translates the formula contained in the file c2d_file from nnf format to a pysmt FNode

        Args:
            c2d_file (str) -> the path to the file where the dimacs output need to be saved

        Returns:
            (FNode,int,int) -> the pysmt formula, the total nodes and the total edges of the formula
        """
        with open(nnf_file, "r", encoding="utf8") as data:
            contents = data.read()
        lines: List[str] = contents.split("\n")
        lines = list(filter(lambda x: x != "", lines))
        pysmt_nodes: List[FNode] = []
        total_nodes = 0
        total_edges = 0
        for line in lines:
            if line.startswith("nnf "):
                # I DO NOT CARE ABOUT THIS DATA FOR PARSING
                continue
            elif line.startswith("A "):
                # AND node
                total_nodes += 1
                if line.startswith("A 0"):
                    pysmt_nodes.append(TRUE())
                    continue
                tokens = line.split(" ")[2:]
                and_nodes = [pysmt_nodes[int(t)] for t in tokens]
                total_edges += len(and_nodes)
                if len(and_nodes) == 1:
                    pysmt_nodes.append(and_nodes[0])
                    continue
                pysmt_nodes.append(And(*and_nodes))
            elif line.startswith("O "):
                # OR node
                total_nodes += 1
                tokens = line.split(" ")[1:]
                _j = tokens[0]
                tokens = tokens[1:]
                c = tokens[0]
                tokens = tokens[1:]
                if c == "0":
                    pysmt_nodes.append(FALSE())
                    continue
                or_nodes = [pysmt_nodes[int(t)] for t in tokens]
                total_edges += len(or_nodes)
                if len(or_nodes) == 1:
                    pysmt_nodes.append(or_nodes[0])
                    continue
                pysmt_nodes.append(Or(*or_nodes))
            elif line.startswith("L "):
                # LITERAL
                total_nodes += 1
                tokens = line.split(" ")[1:]
                variable = int(tokens[0])
                if variable > 0:
                    pysmt_nodes.append(self.refinement[variable])
                else:
                    pysmt_nodes.append(Not(self.refinement[abs(variable)]))
        return pysmt_nodes[len(pysmt_nodes) - 1], total_nodes, total_edges

    def count_nodes_and_edges_from_nnf(self, nnf_file: str) -> Tuple[int, int]:
        """
        Counts nodes and edges of the formula contained in the file c2d_file from nnf format to a pysmt FNode

        Args:
            nnf_file (str) -> the path to the file where the dimacs output needs to be saved

        Returns:
            (int,int) -> the total nodes and edges of the formula (#nodes,#edges)
        """
        total_nodes = 0
        total_edges = 0
        with open(nnf_file, "r", encoding="utf8") as data:
            contents = data.read()
        lines: List[str] = contents.split("\n")
        lines = list(filter(lambda x: x != "", lines))
        for line in lines:
            if line.startswith("nnf "):
                # I DO NOT CARE ABOUT THIS DATA FOR PARSING
                continue
            elif line.startswith("A "):
                # AND node
                total_nodes += 1
                if line.startswith("A 0"):
                    continue
                tokens = line.split(" ")[2:]
                and_nodes = [int(t) for t in tokens]
                total_edges += len(and_nodes)
            elif line.startswith("O "):
                # OR node
                total_nodes += 1
                tokens = line.split(" ")[1:]
                _j = tokens[0]
                tokens = tokens[1:]
                c = tokens[0]
                tokens = tokens[1:]
                if c == "0":
                    continue
                or_nodes = [int(t) for t in tokens]
                total_edges += len(or_nodes)
            elif line.startswith("L "):
                # LITERAL
                total_nodes += 1
        return (total_nodes, total_edges)

    def compile_dDNNF(
        self,
        phi: FNode,
        tlemmas: List[FNode] | None = None,
        save_path: str | None = None,
        back_to_fnode: bool = False,
        sat_result: bool | None = None,
        quantify_tseitsin: bool = False,
        do_not_quantify: bool = False,
        computation_logger: Dict | None = None,
        timeout: int = 3600,
    ) -> Tuple[FNode | None, int, int]:
        """
        Compiles an FNode in dDNNF through the c2d compiler

        Args:
            phi (FNode) -> a pysmt formula
            tlemmas (List[FNode] | None) -> a list of theory lemmas to be added to the formula
            save_path (str | None) -> the path where the dDNNF will be saved
            back_to_fnode (bool) -> if True, the function returns the pysmt formula
            sat_result (bool | None) -> the result of the SAT check on the formula
            quantify_tseitsin (bool) -> if True, the compiler will quantify over the tseitsin fresh variables
            do_not_quantify (bool) -> if True, the compiler will not quantify over the fresh variables
            computation_logger (Dict | None) -> a dictionary to store the computation time
            timeout (int) -> the maximum time allowed for the computation

        Returns:
            (FNode | None) -> the input pysmt formula in dDNNF, or None if back_to_fnode is False
            (int) -> the number of nodes in the dDNNF
            (int) -> the number of edges in the dDNNF
        """

        # failsafe for computation_logger
        if computation_logger is None:
            computation_logger = {}

        computation_logger["dDNNF compiler"] = "c2d"

        # choose temporary folder
        tmp_folder = self._choose_tmp_folder(save_path)

        # translate to CNF DIMACS and get mapping used for translation
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        start_time = time.time()
        self.logger.info("Translating to DIMACS...")
        phi = get_normalized(phi, self.normalizing_solver.get_converter())
        self.from_smtlib_to_dimacs_file(
            phi,
            f"{tmp_folder}/dimacs.cnf",
            tlemmas,
            sat_result=sat_result,
            quantify_tseitsin=quantify_tseitsin,
            do_not_quantify=do_not_quantify,
            quantification_file=f"{tmp_folder}/quantification.exist"
        )
        elapsed_time = time.time() - start_time
        computation_logger["DIMACS translation time"] = elapsed_time
        self.logger.info("DIMACS translation completed in %s seconds", str(elapsed_time))

        # save mapping for refinement
        start_time = time.time()
        if not os.path.exists(f"{tmp_folder}/mapping"):
            os.mkdir(f"{tmp_folder}/mapping")
        self.logger.info("Saving refinement...")
        save_refinement(self.refinement, f"{tmp_folder}/mapping/mapping.json")
        elapsed_time = time.time() - start_time
        self.logger.info("Refinement saved in %s seconds", str(elapsed_time))
        computation_logger["refinement serialization time"] = elapsed_time

        # call c2d for compilation
        # output should be in file temp_folder/test_dimacs.cnf.nnf
        start_time = time.time()
        self.logger.info("Compiling dDNNF...")
        timeout_string = ""
        if timeout > 0:
            timeout_string = f"timeout {timeout}s "
        result = os.system(
            f"{timeout_string}{_C2D_COMMAND} -in {tmp_folder}/dimacs.cnf -exist {tmp_folder}/quantification.exist -smooth -reduce > /dev/null"
        )
        if result != 0:
            # clean if necessary
            if save_path is None:
                self._clean_tmp_folder(tmp_folder)
            raise TimeoutError("c2d compilation failed: timeout")
        elapsed_time = time.time() - start_time
        computation_logger["dDNNF compilation time"] = elapsed_time
        self.logger.info("dDNNF compilation completed in %s seconds", str(elapsed_time))

        # return if not back to fnode
        if not back_to_fnode:
            nodes, edges = self.count_nodes_and_edges_from_nnf(
                f"{tmp_folder}/dimacs.cnf.nnf")
            return None, nodes, edges

        # translate to pysmt
        start_time = time.time()
        self.logger.info("Translating to pysmt...")
        result, nodes, edges = self.from_nnf_to_pysmt(
            f"{tmp_folder}/dimacs.cnf.nnf")
        # clean if necessary
        if save_path is None:
            self._clean_tmp_folder(tmp_folder)
        elapsed_time = time.time() - start_time
        computation_logger["pysmt translation time"] = elapsed_time
        self.logger.info("Pysmt translation completed in %s seconds", str(elapsed_time))
        return result, nodes, edges

    def load_dDNNF(self, nnf_path: str, mapping_path: str) -> FNode:
        """
        Load a dDNNF from file and translate it to pysmt

        Args:
            nnf_path (str) ->       the path to the file containing the dDNNF in 
                                    NNF format provided by the c2d compiler
            mapping_path (str) ->   the path to the file containing the mapping,
                                    which describes the refinement function

        Returns:
            (FNode) -> the pysmt formula translated from the dDNNF
        """
        self.refinement = load_refinement(mapping_path)
        self.abstraction = {v: k for k, v in self.refinement.items()}
        return self.from_nnf_to_pysmt(nnf_path)


if __name__ == "__main__":
    test_phi = read_smtlib("test.smt2")

    print(test_phi.serialize())

    c2d_compiler = C2DCompiler()

    phi_ddnnf, _a, _b = c2d_compiler.compile_dDNNF(
        test_phi, back_to_fnode=True)

    print(phi_ddnnf.serialize())
