'''this module builds and handles DDs from pysmt formulas'''
from typing import List
from pysmt.fnode import FNode
from theorydd.formula import get_phi
from theorydd.theory_bdd import compute_bdd_cudd
from theorydd.theory_sdd import compute_sdd as _compute_sdd
from theorydd.theory_xsdd import compute_xsdd as _compute_xsdd
from theorydd.theory_ldd import compute_ldd as _compute_ldd


def compute_xsdd(phi: FNode, computation_logger: any = {}):
    '''computing xsdd'''
    _compute_xsdd(phi, computation_logger)


def compute_sdd(phi: FNode,
                vtree_type: str = None,
                output_file: str = None,
                vtree_output: str = None,
                dump_abstraction: bool = False,
                print_mapping: bool = False,
                count_models: bool = False,
                count_nodes: bool = False,
                count_vertices: bool = False,
                qvars: List[FNode] = [],
                computation_logger: any = {}) -> None:
    ' ' 'Computes the SDD for the boolean formula phi and saves it on a file' ' '
    _compute_sdd(phi, vtree_type=vtree_type, output_file=output_file, vtree_output=vtree_output, dump_abstraction=dump_abstraction,
                 print_mapping=print_mapping, count_vertices=count_vertices,
                 count_models=count_models, count_nodes=count_nodes, qvars=qvars, computation_logger=computation_logger)


def compute_bdd(phi: FNode,
                     output_file: str = None,
                     dump_abstraction: bool = False,
                     print_mapping: bool = False,
                     count_models: bool = False,
                     count_nodes: bool = False,
                     count_vertices: bool = False,
                     qvars: List[FNode] = [],
                     computation_logger: any = {}) -> None:
    '''Computes the BDD for the boolean formula phi and saves it on a file using dd.autoref'''
    # For now always use compute_bdd_cudd
    return compute_bdd_cudd(phi, 
                            output_file=output_file, 
                            dump_abstraction=dump_abstraction, 
                            print_mapping=print_mapping, 
                            computation_logger=computation_logger,
                            count_models=count_models,
                            count_nodes=count_nodes,
                            count_vertices=count_vertices,
                            qvars=qvars)

def compute_ldd(phi: FNode,
                     output_file: str | None = None,
                     count_nodes:bool = False,
                     count_vertices:bool = False,
                     count_models:bool = False,
                     computation_logger: any = {}):
    '''Computes the LDD for the boolean formula phi and saves it on a file'''
    _compute_ldd(phi,
                 output_file=output_file,
                 count_nodes=count_nodes,
                 computation_logger=computation_logger,
                 count_vertices=count_vertices,
                 count_models=count_models)

if __name__ == "__main__":
    test_phi = get_phi()
    # compute_bdd(test_phi)
    # compute_sdd(test_phi)
