from theorydd.theory_ldd import TheoryLDD
from pysmt.shortcuts import And, Implies, Or, Iff, LT, Int, Symbol, INT, Plus


def main():
    # BUILD YOUR T-FORMULA FROM THE PYSMT LIBRARY
    phi = And(
        Implies(
            LT(Symbol("x", INT), Symbol("y", INT)),
            LT(Plus(Symbol("x", INT), Symbol("z", INT)), Int(0)),
        ),
        Or(LT(Int(-1), Symbol("z", INT)), LT(Symbol("y", INT), Symbol("z", INT))),
        Iff(
            LT(Symbol("x", INT), Symbol("y", INT)),
            LT(Symbol("z", INT), Symbol("y", INT)),
        ),
    )

    logger = {}

    # BUILD YOUR DD WITH THE CONSTRUCTOR
    ldd = TheoryLDD(
        phi,
        theory="TVPI",
        computation_logger=logger,
        verbose=True
    )

    # USE YOUR DD

    # MODEL COUNTING
    print("Models: ", ldd.count_models())

    # SIZE
    print("Size in nodes: ", ldd.count_nodes())

    # DUMP YOUR DD ON A SVG FILE
    ldd.dump("ldd_example.svg")

    # CHECK YOUR LOGGER
    print(logger)


if __name__ == "__main__":
    main()
