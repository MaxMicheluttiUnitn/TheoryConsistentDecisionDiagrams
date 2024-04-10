'''this module defines a Walker that takes a pysmt formula and converts it into a LDD formula'''

from dataclasses import dataclass
from typing import List
from dd import ldd as ldd_lib
from pysmt.fnode import FNode
from pysmt.shortcuts import BOOL
from pysmt.walkers import DagWalker, handles
import pysmt.operators as op

from theorydd.custom_exceptions import UnsupportedNodeException

@dataclass
class ConstraintObject:
    """a data object used to build constraints"""
    constr_index: int
    constr_mult: int

    def is_const(self):
        """tells if this constrint object is actually a constanrt value"""
        return self.constr_index == 0

class LDDWalker(DagWalker):
    '''A walker to translate the DAG formula quickly with memoization into the LDD'''

    def __init__(self, bool_mapping: dict[FNode,str],
                 theory_mapping: dict[FNode,int],
                 manager: ldd_lib.LDD, env=None, invalidate_memoization=False):
        DagWalker.__init__(self, env, invalidate_memoization)
        self.bool_mapping = bool_mapping
        self.theory_mapping = theory_mapping
        self.manager = manager
        self.theory_amount = len(self.theory_mapping.keys())
        return

    def _apply_mapping(self, arg: FNode,is_bool: bool):
        '''applies the mapping when possible, returns None othrwise'''
        if is_bool:
            # return a piece of the formula with a boolean variable
            return self.manager.bool_var(self.bool_mapping[arg])
        # return the index of the mapped variable
        return self.theory_mapping[arg]

    def walk_and(self, formula: FNode, args, **kwargs):
        '''translate AND node'''
        # pylint: disable=unused-argument
        nodes: List = list(args)
        while len(nodes) > 1:
            first = nodes.pop(0)
            second = nodes.pop(0)
            nodes.append(first & second)
        return nodes[0]

    def walk_or(self, formula: FNode, args, **kwargs):
        '''translate OR node'''
        # pylint: disable=unused-argument
        nodes: List = list(args)
        while len(nodes) > 1:
            first = nodes.pop(0)
            second = nodes.pop(0)
            nodes.append(first | second)
        return nodes[0]

    def walk_not(self, formula: FNode, args, **kwargs):
        '''translate NOT node'''
        # pylint: disable=unused-argument
        return ~ args[0]

    def walk_symbol(self, formula: FNode, args, **kwargs):
        '''translate SYMBOL node'''
        # pylint: disable=unused-argument
        if formula.get_type() == BOOL:
            return self._apply_mapping(formula, True)
        return [ConstraintObject(self._apply_mapping(formula, False),1)]

    def walk_bool_constant(self, formula: FNode, args, **kwargs):
        '''translate BOOL const node'''
        # pylint: disable=unused-argument
        value = formula.constant_value()
        if value:
            return self.manager.true
        return self.manager.false

    def walk_iff(self, formula, args, **kwargs):
        '''translate IFF node'''
        # pylint: disable=unused-argument
        return (args[0] & args[1]) | ((~ args[0]) & (~ args[1]))

    def walk_implies(self, formula, args, **kwargs):
        '''translate IMPLIES node'''  # a -> b === (~ a) v b
        # pylint: disable=unused-argument
        return (~ args[0]) | args[1]

    def walk_ite(self, formula, args, **kwargs):
        '''translate ITE node'''
        # pylint: disable=unused-argument
        return ((~ args[0]) | args[1]) & (args[0] | args[2])

    def walk_forall(self, formula, args, **kwargs):
        '''translate For-all node'''
        # pylint: disable=unused-argument
        raise UnsupportedNodeException('Quantifiers are yet to be supported')

    def walk_exists(self, formula, args, **kwargs):
        '''translate Exists node'''
        # pylint: disable=unused-argument
        raise UnsupportedNodeException('Quantifiers are yet to be supported')

    @handles(op.TIMES)
    def walk_times(self, formula, args, **kwargs):
        '''translate * node'''
        # pylint: disable=unused-argument
        c_obj_1 : ConstraintObject= args[0][0]
        c_obj_2 : ConstraintObject= args[1][0]
        if c_obj_1.is_const() and c_obj_2.is_const():
            return [ConstraintObject(0,c_obj_1.constr_mult*c_obj_2.constr_mult)]
        if c_obj_1.is_const():
            return [ConstraintObject(c_obj_2.constr_index,c_obj_1.constr_mult*c_obj_2.constr_mult)]
        if c_obj_2.is_const():
            return [ConstraintObject(c_obj_1.constr_index,c_obj_1.constr_mult*c_obj_2.constr_mult)]
        raise UnsupportedNodeException("Variable Multiplication: "+str(formula))

    @handles(op.MINUS)
    def walk_minus(self, formula, args, **kwargs):
        '''translate - node'''
        # pylint: disable=unused-argument
        if len(args)==1:
            c_obj: ConstraintObject = args[0]
            return [ConstraintObject(c_obj.constr_index,-c_obj.constr_mult)]
        else:
            left_c_obj : ConstraintObject = args[0][0]
            right_c_obj: ConstraintObject = args[1][0]
            return [left_c_obj,ConstraintObject[right_c_obj.constr_index,-right_c_obj.constr_mult]]

    @handles(op.PLUS)
    def walk_plus(self, formula, args, **kwargs):
        '''translate + node'''
        # pylint: disable=unused-argument
        res : List[ConstraintObject] = []
        for arg in args:
            for c_obj in arg:
                res.append(c_obj)
        return res

    @handles(op.LE)
    def walk_le(self, formula, args, **kwargs):
        '''translate <= node'''
        # pylint: disable=unused-argument
        # args[0] is the tuple describing the constraint [tuple[int]]
        # args[1] is the constant on the right [int]
        left_c_objs : List[ConstraintObject] = args[0]
        right_c_objs : List[ConstraintObject] = args[1]
        const_c_obj = ConstraintObject(0,0)
        var_list = [0] * self.theory_amount
        # LEFT PART OF THE INEQ
        for c_obj in left_c_objs:
            if c_obj.is_const():
                const_c_obj = ConstraintObject(0,const_c_obj.constr_mult-c_obj.constr_mult)
            else:
                var_list[c_obj.constr_index-1] = var_list[c_obj.constr_index-1] + c_obj.constr_mult
        # RIGHT PART OF THE INEQ
        for c_obj in right_c_objs:
            if c_obj.is_const():
                const_c_obj = ConstraintObject(0,const_c_obj.constr_mult+c_obj.constr_mult)
            else:
                var_list[c_obj.constr_index-1] = var_list[c_obj.constr_index-1] - c_obj.constr_mult
        res = tuple([tuple(var_list),False,const_c_obj.constr_mult])
        return self.manager.constraint(res)

    @handles(op.LT)
    def walk_lt(self, formula, args, **kwargs):
        '''translate < node'''
        # pylint: disable=unused-argument
        left_c_objs : List[ConstraintObject] = args[0]
        right_c_objs : List[ConstraintObject] = args[1]
        const_c_obj = ConstraintObject(0,0)
        var_list = [0] * self.theory_amount
        # LEFT PART OF THE INEQ
        for c_obj in left_c_objs:
            if c_obj.is_const():
                const_c_obj = ConstraintObject(0,const_c_obj.constr_mult-c_obj.constr_mult)
            else:
                var_list[c_obj.constr_index-1] = var_list[c_obj.constr_index-1] + c_obj.constr_mult
        # RIGHT PART OF THE INEQ
        for c_obj in right_c_objs:
            if c_obj.is_const():
                const_c_obj = ConstraintObject(0,const_c_obj.constr_mult+c_obj.constr_mult)
            else:
                var_list[c_obj.constr_index-1] = var_list[c_obj.constr_index-1] - c_obj.constr_mult
        res = tuple([tuple(var_list),True,const_c_obj.constr_mult])
        return self.manager.constraint(res)

    @handles(op.INT_CONSTANT)
    def walk_int_constant(self, formula, args, **kwargs):
        '''translate int const node'''
        # pylint: disable=unused-argument
        return [ConstraintObject(0,formula.constant_value())]
    
    @handles(op.REAL_CONSTANT)
    def walk_real_constant(self, formula, args, **kwargs):
        '''translate int const node'''
        # pylint: disable=unused-argument
        return [ConstraintObject(0,formula.constant_value())]

    @handles(op.EQUALS)
    def walk_equals(self, formula, args, **kwargs):
        '''translate * node'''
        # pylint: disable=unused-argument
        left_c_objs: List[ConstraintObject] = args[0]
        right_c_objs: List[ConstraintObject] = args[1]
        const_c_obj = ConstraintObject(0,0)
        var_list = [0] * self.theory_amount
        # LEFT PART OF THE INEQ
        for c_obj in left_c_objs:
            if c_obj.is_const():
                const_c_obj = ConstraintObject(0,const_c_obj.constr_mult-c_obj.constr_mult)
            else:
                var_list[c_obj.constr_index-1] = var_list[c_obj.constr_index-1] + c_obj.constr_mult
        # RIGHT PART OF THE INEQ
        for c_obj in right_c_objs:
            if c_obj.is_const():
                const_c_obj = ConstraintObject(0,const_c_obj.constr_mult+c_obj.constr_mult)
            else:
                var_list[c_obj.constr_index-1] = var_list[c_obj.constr_index-1] - c_obj.constr_mult
        res1 = tuple([tuple(var_list),False,const_c_obj.constr_mult])
        minus_const_c_obj = ConstraintObject(const_c_obj.constr_index,-const_c_obj.constr_mult)
        minus_var_list = [-x for x in var_list]
        res2 = tuple([tuple(minus_var_list),False,minus_const_c_obj.constr_mult])
        return self.manager.constraint(res1) & self.manager.constraint(res2)

    @handles(*op.BV_OPERATORS, *op.STR_OPERATORS, *op.BV_RELATIONS, *op.STR_RELATIONS, op.STR_CONSTANT, op.BV_CONSTANT)
    def walk_theory(self, formula, args, **kwargs):
        '''translate theory node'''
        # pylint: disable=unused-argument
        raise UnsupportedNodeException(formula)
