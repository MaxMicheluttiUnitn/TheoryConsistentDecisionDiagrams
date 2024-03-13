'''this module defines a Walker that takes a pysmt formula and normalizes its atoms'''

from pysmt.walkers import DagWalker, handles
import pysmt.operators as op
from pysmt.fnode import FNode

from pysmt.shortcuts import And, Or, Iff, Implies, TRUE, FALSE, Not, Ite

from theorydd.custom_exceptions import UnsupportedNodeException


class NormalizerWalker(DagWalker):
    '''A walker to normalize smt formulas acccording to a converter'''

    def __init__(self, converter, env=None, invalidate_memoization=False):
        DagWalker.__init__(self, env, invalidate_memoization)
        self._converter = converter
        return

    def walk_and(self, formula: FNode, args, **kwargs):
        '''translate AND node'''
        # pylint: disable=unused-argument
        return And(*args)

    def walk_or(self, formula: FNode, args, **kwargs):
        '''translate OR node'''
        # pylint: disable=unused-argument
        return Or(*args)

    def walk_not(self, formula: FNode, args, **kwargs):
        '''translate NOT node'''
        # pylint: disable=unused-argument
        return Not(args[0])

    def walk_symbol(self, formula: FNode, args, **kwargs):
        '''translate SYMBOL node'''
        # pylint: disable=unused-argument
        return self._convert(formula)

    def walk_bool_constant(self, formula: FNode, args, **kwargs):
        '''translate BOOL const node'''
        # pylint: disable=unused-argument
        value = formula.constant_value()
        if value:
            return TRUE()
        return FALSE()

    def walk_iff(self, formula, args, **kwargs):
        '''translate IFF node'''
        # pylint: disable=unused-argument
        return Iff(args[0], args[1])

    def walk_implies(self, formula, args, **kwargs):
        '''translate IMPLIES node'''  # a -> b === (~ a) v b
        # pylint: disable=unused-argument
        return Implies(args[0], args[1])

    def walk_ite(self, formula, args, **kwargs):
        '''translate ITE node'''
        # pylint: disable=unused-argument
        return Ite(args[0], args[1], args[2])

    def _convert(self, formula):
        msat_term = self._converter.convert(formula)
        return self._converter.back(msat_term)

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
        return self._convert(formula)

    @handles(*op.THEORY_OPERATORS, *op.BV_RELATIONS, *op.IRA_RELATIONS,
             *op.STR_RELATIONS, op.REAL_CONSTANT, op.BV_CONSTANT, op.INT_CONSTANT)
    def walk_theory(self, formula, args, **kwargs):
        '''translate theory node'''
        # pylint: disable=unused-argument
        return self._convert(formula)
