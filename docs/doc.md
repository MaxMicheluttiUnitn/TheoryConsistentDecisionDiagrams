# TheoryDD

This is the documentation for the **theorydd** python package.

#

- **[Overview](#overview)** <br>
- **[Installing](#installing)** <br>
- **[SMT Enumerators](#smt-enumerators)** <br>
- **[Theory Decision Diagrams](#theory-decision-diagrams)** <br>
- **[Abstrtact Decision Diagrams](#abstract-decision-diagrams)** <br>
- **[d-DNNF](#d-dnnf)** <br>

#

## Overview
#
This package allows you to compile SMT formulas into Decision Diagrams and dDNNF equivalent formulas. <br>
This package was developed for **python version 3.10**, compatibility with different versions of python is not guaranteed. <br>
This package also expects to be used in a Linux environment, therefore compatibility with any other OS is not guaranteed: this package is currently **Linux only**. <br>
Currently, this package allows compilation into **BDD**s, **SDD**s and **d-DNNF**, but compilation into different target languages can be achieved by extending the correct interface. <br>
A limitation of this package is that the **[pysmt](https://pypi.org/project/PySMT/)** package is used for managing SMT formulas, which means that this package is only compatible with SMT formulas that are supported by pysmt.

## Installing
#
This package uses some dependencies that require cython compilation before being ready to use. This makes the installation process slightly harder than simply installing the package through a pip one-liner. <br>
To install the package, first install the **dd** dependency as follows:

```
    pip install --upgrade wheel cython
    export DD_FETCH=1 DD_CUDD=1 DD_LDD=1
    pip install git+https://github.com/masinag/dd.git@main -vvv --use-pep517 --no-build-isolation
```

The dd package cannot be installed directly from pip's package repository since this package depends on a fork of the dd package which allows for compilation into the LDD target language. The fork is publicly available [here](https://github.com/masinag/dd).<br>
You can check that the dependency is installed correctly if the following command does not raise any errors:

```
    python -c 'from dd import ldd; ldd.LDD(ldd.TVPI,0,0)'
```

Now you can install the theorydd package (this package) directly from this repository using pip:

```
    pip install theorydd@git+https://github.com/MaxMicheluttiUnitn/TheoryConsistentDecisionDiagrams@main
```

After the package and all the depemdencies have been installed, use the **pysmt-install** tool to install the MathSAT SMT-solver. This tool is automatically installed when pysmt is first installed on your machine. <br>
**IMPORTANT**: In case you are installing this package inside a **python virtual environment**, install the solver in a subfolder of the virtual environment by adding the option _--install-path YOUR_VENV_FOLDER/solvers_

```
    pysmt-install --msat
```

Now the installation process should be complete, and you can check that everything is installed correctly with the following command:

```
    python -c "from theorydd.theory_bdd import TheoryBDD as TBDD; import theorydd.formula as f; TBDD(f.default_phi())"
```

If this command does not raise any error, than the package is ready for use.

### Installing binaries
#
Some modules of this package require a binary to be executed to work correctly. These binaries do not come with the package at installation time and must be installed by the user. <br> 
To facilitate this operation, this package comes with a command **theorydd_install** which allows for easy installing of the required binaries. <br>
The **theorydd_install** command takes 3 optional arguments:

- **--tabular**: installs the **[tabularSMT](https://github.com/giuspek/tabularAllSMT)** solver binary and grants it execution permissions
- **--c2d**: installs the **[c2d](http://reasoning.cs.ucla.edu/c2d/)** d-DNNF compiler and grants it execution permissions
- **--d4**: installs the **[D4](https://github.com/crillab/d4)** d-DNNF compiler and grants it execution permissions

The following example will try to install all the binaries on your machine:

```
theorydd_install --tabular --c2d --d4
```

In alternative, the binaries can be **manually installed** in the correct location by the user. The folder structure must be as shown below, otherwise the binaries will not be found during execution. <br>
Remember to grant execution privileges (_chmod +x_) to the binaries before using them.

```
-theorydd
 |-abstractdd
 | L...
 |-bin
 | |-c2d
 | | L-c2d_linux
 | |-d4
 | | L-d4.bin
 | |-tabular
 | L L-tabularAllSMT.bin
 |-ddnnf
 | L...
 L ...
```

## Constants
#
All **constants** for this package are defined inside the _constants.py_ module.

## SMT Enumerators
#
SMTEnumerators are classes that inherit from the abstract class **SMTEnumerator** and override all the abstract methods defined into it. These classes are defined [here](../src/theorydd/solvers/).<br>
Furthermore, a module _[lemma extractor](#lemma-extractor)_ containing some useful functions for enumeration is also defined there. <br>
Available classes and modules:
- **[SMTEnumerator](#smtenumerator)**<br>
- **[MathSATTotalEnumerator](#mathsattotalenumerator)**<br>
- **[MathSATExtendedPartialEnumerator](#mathsatextendedpartialenumerator)**<br>
- **[TabularSMTSolver](#tabularsmtsolver)**<br>
- **[TabularTotalSMTSolver](#tabulartotalsmtsolver)**<br>
- **[TabularPartialSMTSolver](#tabularpartialsmtsolver)**<br>
- **[Lemma Extractor](#lemma-extractor)**<br>

### SMTEnumerator
#
Defined in the _[solver.py](../src/theorydd/solvers/solver.py)_ module. <br>
By extending this interface and implementing all its abstract methods, it is possible to define custom SMTEnumerators that are compatible with the rest of the package.<br>

The abstract methods are:

- **[check_all_sat()](#check_all_sat)**<br>
- **[get_theory_lemmas()](#get_theory_lemmas)**<br>
- **[get_converter()](#get_converter)**<br>
- **[get_models()](#get_models)**<br>

# 
#### check_all_sat()
Args:
- _self_
- _phi_: <br> 
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula over which the solver must compute enumeration
- _boolean_mapping_: <br>
    **TYPE**: _Dict[FNode,FNode]_ _|_ _None_ <br>
    **DEFAULT VALUE**: _None_
    **DESCRIPTION**: a mapping that associates to each fresh boolean variable (keys) a atom that appears in _phi_ (values). When a solver is provided a boolean mapping it will enumerate over the fresh boolean variables instead of the original atoms. Some enumerators may ignore this argument.

Returns:
- _bool_: <br>
**DESCRIPTION**: the boolean constant _SAT_ if _phi_ is T-satisfiable, the boolean constant _UNSAT_ otherwise

Method description: <br>
- When this method is called the enumerator must compute AllSMT on _phi_ in order to extract all theory lemmas that allow the solver to trim all T-inconsistent assignments during enumeration and return a boolean constant that describes the satisfiability of _phi_.
#
#### get_theory_lemmas()
Args:
- _self_

Returns:
- _List[FNode]_:<br>
**DESCRIPTION**: the T-lemmas that were extracted during allSMT computation

Method description: <br>
- When this method is called the enumerator returns a list of theory lemmas.
#
#### get_converter()
Args:
- _self_

Returns:
- _object_:<br>
**DESCRIPTION**: the solver's converter which allows for normalization of formulas

Method description: <br>
- When this method is called the enumerator returns its converter object.
#
#### get_models()
Args:
- _self_

Returns:
- _List_:<br>
**DESCRIPTION**: the list of the models that were extracted during allSMT computation

Method description: <br>
- When this method is called the enumerator returns a list of T-consistent models.
#

The SMTEnumerator interface also implements a non-abstract method which is inherited by all its children classes.
#
#### enumerate_true()
Args:
- _self_
- _phi_: <br> 
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula over which the solver must compute enumeration

Returns:
- _bool_: <br>
**DESCRIPTION**: always returns the boolean constant _SAT_, since the boolean formula **True** is always T-satisfiable (but may not be T-valid depending on which atoms it is defined over!)

Method description: <br>
- When this method is called, the enumerator computes AllSMT on a set of formulas that are booleanly equivalent to True by repeatedly calling _[check_all_sat](#check_all_sat)_. These formulas are defined on partitions of the atoms that are present in _phi_. Atoms that share free variables (even if only transitively) are always in the put in the same partition.
#

### MathSATTotalEnumerator
#
Defined in the _[mathsat_total.py](../src/theorydd/solvers/mathsat_total.py)_ module. <br>
The **MathSATTotalEnumerator** is an implementation of [SMTEnumerator](#smtenumerator) which always enumerates **total truth assignments** through the [MathSAT](https://mathsat.fbk.eu/) SMT solver. <br>
This enumerator allows enumeration over a **boolean mapping** of the atoms. <br>

### MathSATPartialEnumerator
#
Defined in the _[mathsat_partial.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
The **MathSATPartialEnumerator** is an implementation of [SMTEnumerator](#smtenumerator) which always enumerates **partial truth assignments** through the [MathSAT](https://mathsat.fbk.eu/) SMT solver. <br>
This enumerator **never** enumerates over a **boolean mapping** of the atoms. <br>

### MathSATExtendedPartialEnumerator
#
Defined in the _[mathsat_partial_extended.py](../src/theorydd/solvers/mathsat_partial_extended.py)_ module. <br>
The **MathSATExtendedPartialEnumerator** is an implementation of [SMTEnumerator](#smtenumerator) which always enumerates **totaltruth assignments** through the [MathSAT](https://mathsat.fbk.eu/) SMT solver. <br> 
The enumeration is computed as follows:
- first, **partial enumeration** is computed and all partial assignments are stored in memory
- then all incomplete partial assignments are **extended to total assignments** through **incremental
calls** to the solver

This enumerator **never** enumerates over a **boolean mapping** of the atoms. <br>

### TabularSMTSolver
#
Defined in the _[tabular.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
The **TabularSMTSolver** is an implementation of [SMTEnumerator](#smtenumerator) which can both enumerate **partial and total truth assignments** through the [tabularAllSMT](https://github.com/giuspek/tabularAllSMT) SMT solver. <br>
This enumerator **never** enumerates over a **boolean mapping** of the atoms. <br>
The constructor for this SMTsolver has an optional parameter **_is_partial_** which defaults to _False_.
If this parameter is set to _True_, than the instance of **TabularSMTSolver** will enumerate **partial truth assignments**, while it will enumerate **total truth assignments** otherwise.

### TabularTotalSMTSolver
#
Defined in the _[tabular.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
A wrapper for the **TabularSMTSolver** which always enumerates **total truth assignments**.

### TabularPartialSMTSolver
#
Defined in the _[tabular.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
A wrapper for the **TabularSMTSolver** which always enumerates **partial truth assignments**.

### Lemma Extractor
#
Defined in the _[lemma_extractor.py](../src/theorydd/solvers/lemma_extractor.py)_ module are these 2 functions: <br>
- **[extract()](#extract)** <br>
- **[find_qvars()](#find_qvars)** <br>

#
#### extract()
Args:
- _phi_: <br> 
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula from which to extract theory lemmas
- _smt_solver_: <br> 
    **TYPE**: _SMTEnumerator_ <br>
    **DESCRIPTION**: the _SMTEnumerator_ on which _check_all_sat_ will be called in order to extract theory lemmas
- _enumerate_true: <br>
    **TYPE**: _bool_ <br>
    **DEFAULT VALUE**: _False_ <br>
    **DESCRIPTION**: if set to _True_, _enumerate_true_ will be called on _smt_solver_ instead of _check_all_sat_
- _use_boolean_mapping_: <br>
    **TYPE**: _bool_ <br>
    **DEFAULT VALUE**: _True_ <br>
    **DESCRIPTION**: if set to _True_, the solver that extracts lemmas for _phi_ will be provided with a boolean mapping
- _computation_logger_: <br>
    **TYPE**: _Dict | None_ <br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation

Returns (Tuple):
- _bool_: <br>
**DESCRIPTION**: the boolean constant _SAT_ if _phi_ is T-satisfiable, the boolean constant _UNSAT_ otherwise
- _List[FNode]_: <br>
**DESCRIPTION**: a list of the extracted theory lemmas
- _Dict[FNode,FNode] | None_: <br>
**DESCRIPTION** a dictionary representing a boolean mapping between fresh boolean atoms (keys) and the atoms of _phi_ (values) if _use_boolean_mapping_ is set to _True_, _None_ otherwise

Method description: <br>
- When this method is called, the provided _smt_solver_ is used in order to extract theory lemmas form the formula _phi_. These lemmas are then returned together with the satisfiability of _phi_ as a boolean constant and an optional dictionary representing a boolean mapping over the atoms of _phi_.
#
#### find_qvars()
Args:
- original_phi:<br>
    **TYPE**: _FNode_<br>
    **DESCRIPTION**: the formula without the conjunction with the theory lemmas
- phi_and_lemmas:<br>
    **TYPE**: _FNode_<br>
    **DESCRIPTION**: the formula after the conjunction with the theory lemmas
- _computation_logger_: <br>
    **TYPE**: _Dict | None_ <br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation

Returns:
- _List[FNode]_: <br>
**DESCRIPTION** a list of the fresh atoms introduced in the formula from the conjunction with the theory lemmas

Method description:
- This method takes as input the formula before and after the conjunction with the lemmas and finds which fresh atoms this conjunction introduced, returning them inside a _List_.
#

## Theory Decision Diagrams
#
The submodule **tdd** contains all compilers that **require computation of AllSMT** for compilation into the target language.

## Abstract Decision Diagrams
#
The submodule **abstractdd** contains all compilers that **do not require computation of AllSMT** for compilation into the target language.

## d-DNNF
#
d-DNNF compilers

## Utility
#
General utility