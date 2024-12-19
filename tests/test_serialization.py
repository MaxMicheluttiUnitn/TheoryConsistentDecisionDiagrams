"""Serialization tests for theorydd package"""

from theorydd.abstraction_bdd import AbstractionBDD, abstraction_bdd_load_from_folder
from theorydd.abstraction_sdd import AbstractionSDD, abstraction_sdd_load_from_folder
import theorydd.formula as formula
from theorydd.theory_bdd import TheoryBDD, tbdd_load_from_folder
from theorydd.theory_sdd import TheorySDD, tsdd_load_from_folder

def test_abstraction_bdd_serialization():
    """tests abstraction BDD serialization"""
    phi = formula.default_phi()
    original_dd = AbstractionBDD(phi)
    original_dd.save_to_folder("tests/test_data/abstraction_bdd")

    loaded_dd = abstraction_bdd_load_from_folder("tests/test_data/abstraction_bdd")
    assert len(original_dd) == len(loaded_dd), "Loaded BDD has different number of nodes"
    assert original_dd.count_models() == loaded_dd.count_models(), "Loaded BDD has different number of models"

def test_abstraction_sdd_serialization():
    """tests abstraction SDD serialization"""
    phi = formula.default_phi()
    original_dd = AbstractionSDD(phi)
    original_dd.save_to_folder("tests/test_data/abstraction_sdd")

    loaded_dd = abstraction_sdd_load_from_folder("tests/test_data/abstraction_sdd")
    assert len(original_dd) == len(loaded_dd), "Loaded SDD has different number of nodes"
    assert original_dd.count_models() == loaded_dd.count_models(), "Loaded SDD has different number of models"

def test_theory_bdd_serialization():
    """tests theory BDD serialization"""
    phi = formula.default_phi()
    original_dd = TheoryBDD(phi)
    original_dd.save_to_folder("tests/test_data/theory_bdd")

    loaded_dd = tbdd_load_from_folder("tests/test_data/theory_bdd")
    assert len(original_dd) == len(loaded_dd), "Loaded BDD has different number of nodes"
    assert original_dd.count_models() == loaded_dd.count_models(), "Loaded BDD has different number of models"

def test_theory_sdd_serialization():
    """tests theory SDD serialization"""
    phi = formula.default_phi()
    original_dd = TheorySDD(phi)
    original_dd.save_to_folder("tests/test_data/theory_sdd")

    loaded_dd = tsdd_load_from_folder("tests/test_data/theory_sdd")
    assert len(original_dd) == len(loaded_dd), "Loaded SDD has different number of nodes"
    assert original_dd.count_models() == loaded_dd.count_models(), "Loaded SDD has different number of models"