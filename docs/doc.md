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

This package allows you to compile SMT formulas into Decision Diagrams and dDNNF equivalent formulas. <br>
This package was developed for **python version 3.10**, compatibility with different versions of python is not guaranteed. <br>
This package also expects to be used in a Linux environment, therefore compatibility with any other OS is not guaranteed: this package is currently **Linux only**. <br>
Currently, this package allows compilation into **BDD**s, **SDD**s and **d-DNNF**, but compilation into different target languages can be achieved by extending the correct interface. <br>
A limitation of this package is that the **[pysmt](https://pypi.org/project/PySMT/)** package is used for managing SMT formulas, which means that this package is only compatible with SMT formulas that are supported by pysmt.

## Installing

This package uses some dependencies that require cython compilation before being ready to use. This makes the installation process slightly harder than simply installing the package through a pip one-liner. <br>
To install the package, first install the **dd** dependency as follows:

```
    pip install --upgrade wheel cython
    export DD_FETCH=1 DD_CUDD=1
    pip install dd=0.5.7 -vvv --use-pep517 --no-build-isolation
```

You can check that the dependency is installed correctly if the following command does not give you ant errors:

```
    python -c 'import dd.cudd'
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

All **constants** for this package are defined inside the _constants.py_ module.<br>
The constant list _VALID_SOLVERS_ contains all valid strings refering to a solver contained in this package.<br>
The constant list _VALIC_VTREE_ contains all valid configuration type for building V-trees for SDDs.<br>


## SMT Enumerators

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

Defined in the _[mathsat_total.py](../src/theorydd/solvers/mathsat_total.py)_ module. <br>
The **MathSATTotalEnumerator** is an implementation of [SMTEnumerator](#smtenumerator) which always enumerates **total truth assignments** through the [MathSAT](https://mathsat.fbk.eu/) SMT solver. <br>
This enumerator allows enumeration over a **boolean mapping** of the atoms. <br>

### MathSATPartialEnumerator

Defined in the _[mathsat_partial.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
The **MathSATPartialEnumerator** is an implementation of [SMTEnumerator](#smtenumerator) which always enumerates **partial truth assignments** through the [MathSAT](https://mathsat.fbk.eu/) SMT solver. <br>
This enumerator **never** enumerates over a **boolean mapping** of the atoms. <br>

### MathSATExtendedPartialEnumerator

Defined in the _[mathsat_partial_extended.py](../src/theorydd/solvers/mathsat_partial_extended.py)_ module. <br>
The **MathSATExtendedPartialEnumerator** is an implementation of [SMTEnumerator](#smtenumerator) which always enumerates **totaltruth assignments** through the [MathSAT](https://mathsat.fbk.eu/) SMT solver. <br> 
The enumeration is computed as follows:
- first, **partial enumeration** is computed and all partial assignments are stored in memory
- then all incomplete partial assignments are **extended to total assignments** through **incremental
calls** to the solver

This enumerator **never** enumerates over a **boolean mapping** of the atoms. <br>

### TabularSMTSolver

Defined in the _[tabular.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
The **TabularSMTSolver** is an implementation of [SMTEnumerator](#smtenumerator) which can both enumerate **partial and total truth assignments** through the [tabularAllSMT](https://github.com/giuspek/tabularAllSMT) SMT solver. <br>
This enumerator **never** enumerates over a **boolean mapping** of the atoms. <br>
The constructor for this SMTsolver has an optional parameter **_is_partial_** which defaults to _False_.
If this parameter is set to _True_, than the instance of **TabularSMTSolver** will enumerate **partial truth assignments**, while it will enumerate **total truth assignments** otherwise.

### TabularTotalSMTSolver

Defined in the _[tabular.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
A wrapper for the **TabularSMTSolver** which always enumerates **total truth assignments**.

### TabularPartialSMTSolver

Defined in the _[tabular.py](../src/theorydd/solvers/mathsat_partial.py)_ module. <br>
A wrapper for the **TabularSMTSolver** which always enumerates **partial truth assignments**.

### Lemma Extractor

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
- _original_phi_<br>
    **TYPE**: _FNode_<br>
    **DESCRIPTION**: the formula without the conjunction with the theory lemmas
- _phi_and_lemmas_<br>
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

The submodule [tdd](../src/theorydd/tdd/) contains all Desision Diagrams compilers that **require computation of AllSMT** for compilation into the target language. <br>
All such compilers inherit from the interface class [TheoryDD](#theorydd) and implement all its abstract methods.

### TheoryDD

The [_TheoryDD_](../src/theorydd/tdd/theory_dd.py) abstract class requires implementation of the following abstract methods:<br>
- **[_enumerate_qvars()](#_enumerate_qvars)**
- **[_load_from_folder()](#_load_from_folder)**
- **[save_to_folder()](#save_to_folder)**
- **[\_\_len\_\_()](#__len__)**
- **[count_nodes()](#count_nodes)**
- **[count_vertices()](#count_vertices)**
- **[count_models()](#count_models)**
- **[graphic_dump()](#graphics_dump)**
- **[pick()](#pick)**
- **[pick_all()](#pick_all)**
- **[pick_all_iter()](#pick_all_iter)**
- **[is_sat()](#is_sat)**
- **[is_valid()](#is_valid)**
#
#### _enumerate_qvars()
Args:
- _self_
- _tlemmas_dd_: <br>
**TYPE**: _object_
**DESCRIPTION**: the _T-DD_ built from the big and of the theory lemmas
- _mapped_qvars_: <br>
**TYPE**: _List[object]_ <br>
**DESCRIPTION**: a list of all the labels over which to enumerate

Returns:
- _object_: <br>
**DESCRIPTION**: the root of the _tlemma_dd_ enumerated over the quantified variables

Method description:
- transforms argument _tlemma_dd_ in _{ Exists(quantified variables) tlemma_dd }_ and returns the root of the result of the transformation. This method is used to remove fresh atoms that may be generated by the solver inside the theory lemmas which are not present in the original formula.
#
#### _load_from_folder()
Args:
- _self_
- _folder_path_: <br>
**TYPE**: _str_ <br>
**DESCRIPTION**: the path to the folder where the _T-DD_ is stored. Notice that different _T-DDs_ may have different formats for serialization. 

Method Description:
- Loads all the data for the _T-DD_ from the specified folder. This function is usually called inside the constructor to load a pre-built _T-DD_ instead of recompiling the same formula.
#
#### save_to_folder()
Args:
- _self_
- _folder_path_: <br>
**TYPE**: _str_ <br>
**DESCRIPTION**: the path to the folder where the _T-DD_ must be stored

Method description:
- Serializes the _T-DD_ into the folder specified in _folder_path_, creating the folder if necessary. If a _T-DD_ is already saved in that folders, its files may be overwritten. 
#
#### \_\_len\_\_()
Args:
- _self_

Returns:
- _int_: <br>
**DESCRIPTION**: the number of the nodes of the _T-DD_

Method description:
- returns the amount of nodes in the _T-DD_.
#
#### count_nodes()
Args:
- _self_

Returns:
- _int_: <br>
**DESCRIPTION**: the number of the nodes of the _T-DD_

Method description:
- returns the amount of nodes in the _T-DD_ (same as [\_\_len\_\_()](#__len__)).
#
#### count_vertices()
Args:
- _self_

Returns:
- _int_: <br>
**DESCRIPTION**: the number of links between the nodes of the _T-DD_.

Method description:
- returns the amount of vertices in the _T-DD_.
#
#### count_models()
Args:
- _self_

Returns:
- int: <br>
**DESCRIPTION**: the amount of models encoded in the _T-DD_.

Method description:
- returns the amount of models encoded in the _T-DD_.
#
#### graphics_dump()
Args:
- _self_
- _output_file_: <br>
**TYPE**: _str_<br>
**DESCRIPTION**: the path to a file where a graphical representation of the _T-DD_ will be saved.

Method description:
- A graphical representation of _T-DD_ is saved inside _output_file_. This method may raise errors if [GraphViz](https://www.graphviz.org/) is not installed on the user's machine or if the size of the _T-DD_ is high. 
#
#### pick()
Args:
- _self_

Returns:
- _Dict[FNode, bool] | None_: <br>
**DESCRIPTION**: a model of the encoded DD, _None_ if the DD has no models.

Method description:
- returns a model of the encoded DD, _None_ if the DD has no models.
#
#### pick_all()
Args:
- _self_

Returns:
- _List[Dict[FNode, bool]]_: <br>
**DESCRIPTION**: a list of all the models of the DD

Method description:
- returns a list of all the models encoded in the DD, if the encoded formula is _TRUE_ or unsatisfiable, an empty list will be returned.
#
#### pick_all_iter()
Args:
- _self_

Returns:
- _Iterator[Dict[FNode, bool]]_: <br>
**DESCRIPTION**: an iterator that enumerates all encoded models

Method description:
- this method returns an iterator which yields the models encoded in the DD one at a time as _Dict[FNode,bool]_.
#
#### is_sat()
Args:
- _self_

Returns:
- _bool_: <br>
**DESCRIPTION**: _True_ if the encoded formula is satisfiable, _False_ otherwise

Method description:
- this method checks the satisfiability of the compiled formula.
#
#### is_valid()
Args:
- _self_

Returns:
- _bool_: <br>
**DESCRIPTION**: _True_ if the encoded formula is valid, _False_ otherwise

Method description:
- this method checks the validity of the compiled formula.
#

The [_theory_dd_](../src/theorydd/tdd/theory_dd.py) class also implements some useful private methods for the construction of _T-DDs_:

- **[_normalize_input()](#_normalize_input)**
- **[_load_lemmas()](#_load_lemmas)**
- **[_build()](#_build)**
- **[_build_unsat()](#_build_unsat)**

#
#### _normalize_input()
Args:
- _self_
- _phi_: <br>
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula that has to be encoded into a _T-DD_
- _solver_: <br>
    **TYPE**: _SMTEnumerator_ <br>
    **DESCRIPTION**: an _SMTEnumerator_ that is only used for normalization
- _computation_logger_: <br>
    **TYPE**: _Dict_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation

Returns:
- _FNode_: <br>
**DESCRIPTION**: the normalized input formula

Method description:
- Normalizes the input formula _phi_ using the converter that _solver_ owns and logs the time elapsed during this operation in the _computation_logger_.
#
#### _load_lemmas()
Args:
- _self_
- _phi_: <br>
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula that has to be encoded into a _T-DD_
- _smt_solver_: <br>
    **TYPE**: _SMTEnumerator_: <br>
    **DESCRIPTION**: an _SMTEnumerator_ that is used for normalization of the theory lemmas and theory lemma extraction if necessary
- _tlemmas_: <br>
    **TYPE**: _List[FNode] | None_ <br>
    **DESCRIPTION**: the theory lemmas of _phi_, or _None_ if the theory lemmas are not available in memory yet
- _load_lemmas_: <br>
    **TYPE**: _str | None_ <br>
    **DESCRIPTION**: the path to a .smt2 file where the theory lemmas are stored, _None_ if such a file is not available
- _sat_result_: <br>
    **TYPE**: _bool | None_ <br>
    **DESCRIPTION**: the T-satisfiability of _phi_ if known, _None_ otherwise
- _computation_logger_: <br>
    **TYPE**: _Dict_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation

Returns:
- _List[FNode]_: <br>
**DESCRIPTION**: the theory lemmas of the input formula, already normalized.
- _bool | None_: <br>
**DESCRIPTION**: the T-satisfiability of _phi_ if available, _None_ otherwise 

Method description:
- Loads the theory lemmas fro the correct source and logs the time elapsed during this operation in the _computation_logger_. If the theory lemmas are provided in the _tlemmas_ argument, then those lemmas are normalized and returned. If the _load_lemmas_ argument is not _None_ and the theory lemmas are not provided, then the theory lemmas are loaded from the specified file. If both _tlemmas_ and _load_leamms_ are _None_, the theory lemmas are extracted from the formula by computing AllSMT with the provided _smt_solver_.
#
#### _build()
Args:
- _self_
- _phi_: <br>
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula that has to be encoded in the _T-DD_
- _tlemmas_: <br>
    **TYPE**: _List[FNode]_ <br>
    **DESCRIPTION**: the list of the theory lemmas of _phi_
- _walker_: <br>
    **TYPE**: _DagWalker_ <br>
    **DESCRIPTION**: a walker that walks over _phi_ in order to call the correct apply function of the _T-DD_
- _computation_logger_: <br>
    **TYPE**: _Dict_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation
Returns:
- _object_:
**DESCIPTION**: the root of the _T-DD_ of _phi_

Method description:
- builds the _T-DD_ for _phi_ and _tlemmas_ which only encodes consistent truth assignments and returns its root
#
#### _build_unsat()
Args:
- _self_
- _walker_: <br>
    **TYPE**: _DagWalker_ <br>
    **DESCRIPTION**: a walker that walks over an FNode in order to call the correct apply function of the _T-DD_
- _computation_logger_: <br>
    **TYPE**: _Dict_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation
Returns:
- _object_:
**DESCIPTION**: the root of the _T-DD_ of the SMT formuala _FALSE_

Method description:
- builds the _T-DD_ for an unsatisfiable SMT formula in an efficient way and returns its root
#

Finally, the [_TheoryDD_](../src/theorydd/tdd/theory_dd.py) class implements the following public methods that are available to all its children classes:
- **[get_mapping()](#get_mapping)**
- **[get_abstraction()](#get_abstraction)**
- **[get_refinement()](#get_refinement)**

#
#### get_mapping()
Method description:
Same as [_get_abstraction()_](#get_abstraction).
#
#### get_abstraction()
Args:
- _self_

Returns:
- _Dict[FNode,object]_:
**DECRIPTION**: a dictionary defining the abstraction function used when building the DD

Method description:
- Returns a dictionary which describes the abstraction function that the DD uses.
# 
#### get_refinement()
Args:
- _self_

Returns:
- _Dict[object,FNode]_:
**DECRIPTION**: a dictionary defining the refinement function 

Method description:
- Returns a dictionary which describes the abstraction function that the DD uses, which is used to decode the models of the DD when [_pick()_](#pick), [_pick_all()](#pick_all) or [_pick_all_iter()_](#pick_all_iter) are called.
#

### TheoryBDD

A  [_TheoryBDD_](../src/theorydd/tdd/theory_bdd.py) instance is an instance of a [_TheoryDD_](#theorydd) which implements all abstract methods and builds the DD through the [CUDD library](https://largo.lip6.fr/trac/verif_tools/export/8/vis_dev/glu-2.1/src/cuBdd/doc/cudd.ps) wrapper provided by the [dd](https://github.com/tulip-control/dd) Python package.

Constructor parameters:
- _self_
- _phi_: <br>
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula that has to be compiled into a _T-BDD_
- _solver_: <br>
    **TYPE**: _SMTEnumerator | str_ <br>
    **DEFAULT VALUE**: _"total"_ <br>
    **DESCRIPTION**: if a string is provided, a new [_SMTEnumerator_](#smtenumerator) of the type specified from the string will be used during construction, otherwise the provided enumerator will be used. This parameter is used to compute enumeration (if necessary) and to apply normalization to theory atoms while building the DD.
- _tlemmas_: <br>
    **TYPE**: _List[FNode] | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a list of FNode is provided, the theory lemmas will not be enumerated and the procided lemmas will be used instead, skipping enumeration
- _load_lemmas_: <br>
    **TYPE**: _str | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a string is provided, the theory lemmas will be loaded from the SMT file located at the path specified in that string, skipping enumeration. If the _tlemmas_ parameter for this function is not None, this parameter is ignored.
- _sat_result_:
    **TYPE**: _bool | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: provide one of the boolean constant _SAT_ or _UNSAT_ defined in the [constants](../src/theorydd/constants) module to signal to the constructor that it is dealing with a satisfiable/unsatisfiable formula in order to speed up compilation time. If _None_ is provided, than the constructor does not assume that the formula is either satisfiable or unsatisfiable.
- _use_ordering_: <br>
    **TYPE**: _List[FNode] | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a list of FNode is provided, this class will respect the provided ordering of variables when building the DD
- _folder_name_: <br>
    **TYPE**: _str | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a string is provided, all other parameters except for _solver_ will be ignored and the _TheoryBDD_ will be loaded from the specified path
- _computation_logger_: <br>
    **TYPE**: _Dict | None_ <br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation


In addition to implemnting all abstract methods from the [_TheoryDD_](#theorydd) interfece, this class also provides these public methods:
- **[get_ordering()](#get_ordering)**<br>
- **[condition()](#condition)**<br>
#
#### get_ordering()
Args:
- _self_

Returns:
- _List[FNode]_: <br>
**DESCRIPTION**: the ordering of atoms used while building the _T-BDD_

Method description:
- The ordering used for building the DD is returned
#
#### condition()
Args:
- _self_
- _condition_: <br>
    **TYPE**: _str_ <br>
    **DESCRIPTION**: a string contained in the values of the abstraction dictionary which corresponds to the abstraction of the atom that you want to condition over. Start the string with a ```-``` symbol in order to indicate a negation of the atom (condition over Not atom).<br>

Method description:
- Transform the _TheoryBDD_ of phi into the _ThoeryBDD_ of phi | _condition_.
#


### TheorySDD

A  [_TheorySDD_](../src/theorydd/tdd/theory_sdd.py) instance is an instance of a [_TheoryDD_](#theorydd) which implements all abstract methods and builds the DD through the [SDD library](http://reasoning.cs.ucla.edu/sdd/) wrapper provided by the [PySDD](https://github.com/ML-KULeuven/PySDD) Python package.

Constructor parameters:
- _self_
- _phi_: <br>
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula that has to be compiled into a _T-SDD_
- _solver_: <br>
    **TYPE**: _SMTEnumerator | str_ <br>
    **DEFAULT VALUE**: _"total"_ <br>
    **DESCRIPTION**: if a string is provided, a new [_SMTEnumerator_](#smtenumerator) of the type specified from the string will be used during construction, otherwise the provided enumerator will be used. This parameter is used to compute enumeration (if necessary) and to apply normalization to theory atoms while building the DD.
- _tlemmas_: <br>
    **TYPE**: _List[FNode] | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a list of FNode is provided, the theory lemmas will not be enumerated and the procided lemmas will be used instead, skipping enumeration
- _load_lemmas_: <br>
    **TYPE**: _str | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a string is provided, the theory lemmas will be loaded from the SMT file located at the path specified in that string, skipping enumeration. If the _tlemmas_ parameter for this function is not None, this parameter is ignored.
- _sat_result_:
    **TYPE**: _bool | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: provide one of the boolean constant _SAT_ or _UNSAT_ defined in the [constants](../src/theorydd/constants) module to signal to the constructor that it is dealing with a satisfiable/unsatisfiable formula in order to speed up compilation time. If _None_ is provided, than the constructor does not assume that the formula is either satisfiable or unsatisfiable.
- _vtree_type_: <br>
    **TYPE**: _str_<br>
    **DEFAULT VALUE**: _"balanced"_ <br>
    **DESCRIPTION**: an indication of the shape of the V-Tree used for the construction of the SDD. Valid values for this parameter are specified in the _VALID_VTREE_ constant in the [constants](../src/theorydd/constants) module.
- _use_vtree: <br>
    **TYPE**: _Vtree | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a Vtree is provided, the specified V-Tree will be used and the _vtree_type_ parameter will be ignored. It is important to use this parameter together with the _use_abstraction_ parameter since the Vtree ordering in the resulting structure may be shuffled otherwise.
- _use_abstraction_: <br>
    **TYPE**: _Dict[Fnode,int] | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a _Dict[FNode,int]_ is provided, the specified abstraction function will be used while building the DD. It is important to use this parameter together with the _use_vtree_ parameter since the Vtree ordering in the resulting structure may be shuffled otherwise.
- _folder_name_: <br>
    **TYPE**: _str | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a string is provided, all other parameters except for _solver_ will be ignored and the _TheorySDD_ will be loaded from the specified path
- _computation_logger_: <br>
    **TYPE**: _Dict | None_ <br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation

In addition to implemnting all abstract methods from the [_TheoryDD_](#theorydd) interfece, this class also provides these public methods:
- **[graphic_dump_vtree()](#graphic_dump_vtree)**<br>
- **[condition()](#condition-1)**<br>
- **[get_vtree()](#get_vtree)**
#
#### graphic_dump_vtree()
Args:
- _self_
- _output_file_: <br>
**TYPE**: _str_<br>
**DESCRIPTION**: a path where a graphical representation of the Vtree will be dumped

Method description:
- A graphical representation of the Vtree is dumped in the specified _output_file_.
#
#### condition()
Args:
- _self_
- _condition_: <br>
    **TYPE**: _int_ <br>
    **DESCRIPTION**: an integer contained in the values of the abstraction dictionary which corresponds to the abstraction of the atom that you want to condition over. Provide the opposite integer of the abstraction index in order to indicate a negation of the atom (condition over Not atom).<br>

Method description:
- Transform the _TheorySDD_ of phi into the _ThoerySDD_ of phi | _condition_.
# 
#### get_vtree()
Args:
- _self_

Returns:
- _Vtree_: <br>
**DESCRIPTION**: the Vtree used for the construction of the _T-SDD_

Method description:
- Returns the Vtree used for the construction of the _T-SDD_.
#

## Abstract Decision Diagrams

The submodule **abstractdd** contains all Desision Diagrams compilers that **do not require computation of AllSMT** for compilation into the target language, whic are [AbstractionBDD](#abstractionbdd) and [AbstractionSDD](#abstractionsdd).

### AbstractionBDD

The [AbstractionBDD](../src/theorydd/abstractdd/abstraction_bdd.py) class inherits from [TheoryBDD](#theorybdd) and describes the _BDD_ of an SMT formula without adding any theory lemmas.

Constructor parameters:
- _self_
- _phi_: <br>
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula that has to be compiled into an _AbstractionBDD_
- _solver_: <br>
    **TYPE**: _SMTEnumerator | str_ <br>
    **DEFAULT VALUE**: _"total"_ <br>
    **DESCRIPTION**: if a string is provided, a new [_SMTEnumerator_](#smtenumerator) of the type specified from the string will be used during construction, otherwise the provided enumerator will be used. This parameter is only used to apply normalization to theory atoms while building the DD.
- _use_ordering_: <br>
    **TYPE**: _List[FNode] | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a list of FNode is provided, this class will respect the provided ordering of variables when building the DD
- _folder_name_: <br>
    **TYPE**: _str | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a string is provided, all other parameters except for _solver_ will be ignored and the _AbstractionBDD_ will be loaded from the specified path
- _computation_logger_: <br>
    **TYPE**: _Dict | None_ <br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation

### AbstractionSDD

The [AbstractionSDD](../src/theorydd/abstractdd/abstraction_bdd.py) class inherits from [TheorySDD](#theorysdd) and describes the _SDD_ of an SMT formula without adding any theory lemmas.

Constructor parameters:
- _self_
- _phi_: <br>
    **TYPE**: _FNode_ <br>
    **DESCRIPTION**: the formula that has to be compiled into an _AbstractionSDD_
- _solver_: <br>
    **TYPE**: _SMTEnumerator | str_ <br>
    **DEFAULT VALUE**: _"total"_ <br>
    **DESCRIPTION**: if a string is provided, a new [_SMTEnumerator_](#smtenumerator) of the type specified from the string will be used during construction, otherwise the provided enumerator will be used. This parameter is only used to apply normalization to theory atoms while building the DD.
- _vtree_type_: <br>
    **TYPE**: _str_<br>
    **DEFAULT VALUE**: _"balanced"_ <br>
    **DESCRIPTION**: an indication of the shape of the V-Tree used for the construction of the SDD. Valid values for this parameter are specified in the _VALID_VTREE_ constant in the [constants](../src/theorydd/constants) module.
- _use_vtree: <br>
    **TYPE**: _Vtree | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a Vtree is provided, the specified V-Tree will be used and the _vtree_type_ parameter will be ignored. It is important to use this parameter together with the _use_abstraction_ parameter since the Vtree ordering in the resulting structure may be shuffled otherwise.
- _use_abstraction_: <br>
    **TYPE**: _Dict[Fnode,int] | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a _Dict[FNode,int]_ is provided, the specified abstraction function will be used while building the DD. It is important to use this parameter together with the _use_vtree_ parameter since the Vtree ordering in the resulting structure may be shuffled otherwise.
- _folder_name_: <br>
    **TYPE**: _str | None_<br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: if a string is provided, all other parameters except for _solver_ will be ignored and the _AbstractionSDD_ will be loaded from the specified path
- _computation_logger_: <br>
    **TYPE**: _Dict | None_ <br>
    **DEFAULT VALUE**: _None_ <br>
    **DESCRIPTION**: a _Dict_ passed by reference which will be updated with details from the computation

## d-DNNF

d-DNNF compilers

## Utility

General utility