'''this module defines custom exceptions for this package'''


class UnsupportedNodeException(Exception):
    '''An exception for unsupported nodes'''

    def __init__(self, message):
        super().__init__(message)

class InvalidSolverException(Exception):
    """An exception for invalid solvers"""
    def __init__(self, message):
        super().__init__(message)

class UnsupportedSymbolException(Exception):
    '''An exception for unsupported symbols'''

    def __init__(self, message):
        super().__init__(message)


class InvalidLDDTheoryException(Exception):
    '''An exception for invalid LDD theories'''

    def __init__(self, message):
        super().__init__(message)

class InvalidVTreeException(Exception):
    '''An exception for invalid Vtree types'''

    def __init__(self, message):
        super().__init__(message)
