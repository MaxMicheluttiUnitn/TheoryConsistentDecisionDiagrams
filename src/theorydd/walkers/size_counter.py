'''this module defines a Walker that takes a pysmt formula and counts its size'''

from pysmt.walkers import DagWalker, handles
import pysmt.operators as op
from pysmt.fnode import FNode

from theorydd.util.custom_exceptions import UnsupportedNodeException

class CountingWalker(DagWalker):
    '''A walker to count the size of smt formulas'''

    def __init__(self, env=None, invalidate_memoization=False):
        DagWalker.__init__(self, env, invalidate_memoization)
        self.visited = set()

    def walk_and(self, formula: FNode, args, **kwargs):
        '''translate AND node'''
        # pylint: disable=unused-argument
        if formula in self.visited:
            return 0
        self.visited.add(formula)
        total_nodes = 0
        for arg in args:
            total_nodes += arg
        return total_nodes + 1

    def walk_or(self, formula: FNode, args, **kwargs):
        '''translate OR node'''
        # pylint: disable=unused-argument
        if formula in self.visited:
            return 0
        self.visited.add(formula)
        total_nodes = 0
        for arg in args:
            total_nodes += arg
        return total_nodes + 1

    def walk_not(self, formula: FNode, args, **kwargs):
        '''translate NOT node'''
        # pylint: disable=unused-argument
        if formula in self.visited:
            return 0
        self.visited.add(formula)
        return args[0] + 1

    def walk_symbol(self, formula: FNode, args, **kwargs):
        '''translate SYMBOL node'''
        # pylint: disable=unused-argument
        return 1

    def walk_bool_constant(self, formula: FNode, args, **kwargs):
        '''translate BOOL const node'''
        # pylint: disable=unused-argument
        return 1

    def walk_iff(self, formula, args, **kwargs):
        '''translate IFF node'''
        # pylint: disable=unused-argument
        if formula in self.visited:
            return 0
        self.visited.add(formula)
        return args[0] + args[1] + 1

    def walk_implies(self, formula, args, **kwargs):
        '''translate IMPLIES node'''  # a -> b === (~ a) v b
        # pylint: disable=unused-argument
        if formula in self.visited:
            return 0
        self.visited.add(formula)
        return args[0] + args[1] + 1

    def walk_ite(self, formula, args, **kwargs):
        '''translate ITE node'''
        # pylint: disable=unused-argument
        if formula in self.visited:
            return 0
        self.visited.add(formula)
        return args[0] + args[1] + args[2] + 1

    def walk_forall(self, formula, args, **kwargs):
        '''translate For-all node'''
        # pylint: disable=unused-argument
        raise UnsupportedNodeException('Quantifiers are yet to be supported')

    def walk_exists(self, formula, args, **kwargs):
        '''translate Exists node'''
        # pylint: disable=unused-argument
        raise UnsupportedNodeException('Quantifiers are yet to be supported')

    @handles(op.EQUALS)
    def walk_equals(self, formula, args, **kwargs):
        '''translate Equals node'''
        # pylint: disable=unused-argument
        return 1

    @handles(*op.THEORY_OPERATORS, *op.BV_RELATIONS, *op.IRA_RELATIONS,
             *op.STR_RELATIONS, op.REAL_CONSTANT, op.BV_CONSTANT, op.INT_CONSTANT, op.FUNCTION)
    def walk_theory(self, formula, args, **kwargs):
        '''translate theory node'''
        # pylint: disable=unused-argument
        return 1
