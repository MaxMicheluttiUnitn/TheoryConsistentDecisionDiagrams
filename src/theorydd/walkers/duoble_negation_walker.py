"""this module defines a Walker that takes a pysmt formula and removes all double negations"""

from pysmt.fnode import FNode
from pysmt.walkers import DagWalker, handles
import pysmt.operators as op


class DoubleNegWalker(DagWalker):
    """A walker to remove double negations from a pysmt FNode and its children"""

    def __init__(
        self,
        env=None,
        invalidate_memoization=False,
    ):
        DagWalker.__init__(self, env, invalidate_memoization)
        self.manager = self.env.formula_manager

    @handles(op.NOT)
    def walk_not(self, formula: FNode, args, **kwargs):
        """NOT node simplification"""
        # pylint: disable=unused-argument
        assert len(args) == 1
        args = args[0]
        if args.is_bool_constant():
            l = args.constant_value()
            return self.manager.Bool(not l)
        elif args.is_not():
            return args.arg(0)

        return self.manager.Not(args)

    @handles(op.ALL_TYPES)
    def walk_default(self, formula: FNode, args, **kwargs):
        """Default case"""
        # pylint: disable=unused-argument
        return formula
