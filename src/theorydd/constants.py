"""constants for theorydd"""

import os
import re

# VALID ITEMS

VALID_VTREE = ["left", "right", "balanced", "vertical", "random"]

VALID_LDD_THEORY = ["TVPI", "TVPIZ", "UTVPIZ", "BOX", "BOXZ"]

VALID_SOLVER = ["partial", "total","extended_partial","tabular_total","tabular_partial"]

# SAT / UNSAT

SAT = True
UNSAT = False

# DD GRAPHICAL DUMPING

BDD_DOT_LINE_REGEX = r'[\[]label="[a-z]*-[0-9]*"[]]'
BDD_DOT_TRUE_LABEL = '[label="True-1"]'
BDD_DOT_KEY_START_REGEX = r'"[a-z]*-[0-9]*"]'
BDD_DOT_KEY_END_REGEX = r'-[0-9]*"]'
BDD_DOT_REPLACE_REGEX = BDD_DOT_LINE_REGEX

BDD_LINE_REGEX = r">[a-z]+&#45;[0-9]+</text>"
BDD_KEY_START_REGEX = r"[a-z]+&#45;[0-9]+<"
BDD_KEY_END_REGEX = r"&#45;[0-9]+<"
BDD_REPLECE_REGEX = r">[a-z]+&#45;[0-9]+<"

VTREE_LINE_REGEX = r'n[0-9]+ [\[]label="[A-Z]+",fontname='
VTREE_KEY_START_REGEX = r'[A-Z]+",fontname='
VTREE_KEY_END_REGEX = r'",fontname='
VTREE_REPLECE_REGEX = VTREE_KEY_START_REGEX

SDD_LINE_LEFT_REGEX = (
    r'[\[]label= "<L>(&not;)?([A-Z]+|[0-9]+)[|]<R>(&#8869;|&#8868;)?",'
)
SDD_LINE_RIGHT_REGEX = r'[\[]label= "<L>[|]<R>(&not;)?([A-Z]+|[0-9]+)",'
SDD_LINE_BOTH_REGEX = (
    r'[\[]label= "<L>(&not;)?([A-Z]+|[0-9]+)[|]<R>(&not;)?([A-Z]+|[0-9]+)",'
)
SDD_KEY_START_LEFT_REGEX = r"([A-Z]+|[0-9]+)[|]"
SDD_KEY_END_LEFT_REGEX = r"[|]<R>"
SDD_KEY_START_RIGHT_REGEX = r'([A-Z]+|[0-9]+)",'
SDD_KEY_END_RIGHT_REGEX = r'",'
SDD_REPLACE_LEFT_REGEX = SDD_KEY_START_LEFT_REGEX
SDD_REPLACE_RIGHT_REGEX = SDD_KEY_START_RIGHT_REGEX

LIBRARY_PATH = os.path.dirname(os.path.realpath(__file__))

C2D_COMMAND = "." + LIBRARY_PATH + "/bin/c2d/c2d_linux"
D4_COMMAND = "." + LIBRARY_PATH + "/bin/d4/d4.bin"
TABULAR_ALLSMT_COMMAND = "." + LIBRARY_PATH + "/bin/tabular/tabularAllSMT.bin"

# regex for tlemmas files
TLEMMAS_FILE_REGEX = "tlemma_[0-9]+.smt2"

# D4 NODES
D4_AND_NODE = 0
D4_OR_NODE = 1
D4_TRUE_NODE = 2
D4_FALSE_NODE = 3

# D4 REGEX
RE_NNF_EDGE = re.compile(r"(\d+) (\d+)( .+)? 0")
