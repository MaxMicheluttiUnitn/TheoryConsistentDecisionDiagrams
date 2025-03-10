from theorydd.tdd.theory_bdd import TheoryBDD
from pysmt.shortcuts import And, Implies, Or, Iff, LT, LE, Real, Symbol, REAL, Plus


def main():
    # BUILD YOUR T-FORMULA FROM THE PYSMT LIBRARY
    phi = And(
        Implies(
            LT(Symbol("x", REAL), Symbol("y", REAL)),
            LE(Plus(Symbol("x", REAL), Symbol("z", REAL)), Real(0)),
        ),
        Or(LE(Real(-10), Symbol("z", REAL)), LT(Symbol("y", REAL), Symbol("z", REAL))),
        Iff(
            LT(Symbol("x", REAL), Symbol("y", REAL)),
            LT(Symbol("z", REAL), Symbol("y", REAL)),
        ),
    )

    logger = {}

    # BUILD YOUR DD WITH THE CONSTRUCTOR
    bdd = TheoryBDD(
        phi,
        solver="partial",  # used to compute all-SMT and extract lemmas
        computation_logger=logger,
    )

    # USE YOUR DD

    # MODEL COUNTING
    print("Models: ", bdd.count_models())

    # SIZE
    print("Size in nodes: ", bdd.count_nodes())

    # DUMP YOUR DD ON A SVG FILE
    bdd.graphic_dump("theory_bdd_example.svg")

    # CHECK YOUR LOGGER
    print(logger)


if __name__ == "__main__":
    main()
