"""tests for module formula"""

import random
import string
import theorydd.util._utils as utils


def test_is_valid_solver():
    """test for utils.is_valid_solver()"""
    assert utils.is_valid_solver("total"), "total should be a valid solver"
    assert utils.is_valid_solver("partial"), "partial should be a valid solver"
    rand_str = "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(10)
    )
    assert not utils.is_valid_solver(rand_str), "random string sare not valid solvers"
    assert not utils.is_valid_solver(""), "Empty string is not a valid solver"
