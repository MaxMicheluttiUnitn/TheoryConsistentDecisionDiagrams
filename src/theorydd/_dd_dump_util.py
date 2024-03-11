"""util functions for ddS"""

import re
import pydot
from pysmt.formula import FNode
from theorydd._utils import get_string_from_atom as _get_string_from_atom
from theorydd.constants import *


def change_bbd_dot_names(output_file, mapping):
    """changes the name in the dot file with the actual names of the atoms"""
    dot_file = open(output_file, "r", encoding="utf8")
    dot_lines = dot_file.readlines()
    dot_output = """"""
    for line in dot_lines:
        found = re.search(BDD_DOT_LINE_REGEX, line)
        if not found is None:
            key_start_location = re.search(BDD_DOT_KEY_START_REGEX, line).start() + 1
            key_end_location = re.search(BDD_DOT_KEY_END_REGEX, line).start()
            line = re.sub(
                BDD_DOT_REPLACE_REGEX,
                '[label="'
                + _get_string_from_atom(
                    mapping[line[key_start_location:key_end_location]]
                )
                + '"]',
                line,
            )
        dot_output += line
    dot_file.close()
    with open(output_file, "w", encoding="utf8") as out:
        print(dot_output, file=out)


def change_svg_names(output_file, mapping):
    """Changes the names into the svg to match theory atoms' names"""
    svg_file = open(output_file, "r", encoding="utf8")
    svg_lines = svg_file.readlines()
    svg_output = """"""
    for line in svg_lines:
        found = re.search(BDD_LINE_REGEX, line)
        if not found is None:
            key_start_location = re.search(BDD_KEY_START_REGEX, line).start()
            key_end_location = re.search(BDD_KEY_END_REGEX, line).start()
            line = re.sub(
                BDD_REPLECE_REGEX,
                ">"
                + _get_string_from_atom(
                    mapping[line[key_start_location:key_end_location]]
                )
                + "<",
                line,
            )
        svg_output += line
    svg_file.close()
    with open(output_file, "w", encoding="utf8") as out:
        print(svg_output, file=out)


def translate_vtree_vars(original_dot: str, mapping: dict[str, FNode]) -> str:
    """translates variables in the dot representation
    of the VTree into their original names in phi"""
    result = """"""
    original_dot = original_dot.replace("width=.25", "width=.75")
    for line in original_dot.splitlines():
        found = re.search(VTREE_LINE_REGEX, line)
        if not found is None:
            key_start_location = re.search(VTREE_KEY_START_REGEX, line).start()
            key_end_location = re.search(VTREE_KEY_END_REGEX, line).start()
            line = re.sub(
                VTREE_REPLECE_REGEX,
                _get_string_from_atom(
                    mapping[line[key_start_location:key_end_location]]
                )
                + '",fontname=',
                line,
            )
        result += (
            line
            + """
"""
        )
    return result


def translate_sdd_vars(original_dot: str, mapping: dict[str, FNode]) -> str:
    """translates variables in the dot representation of the SDD into their original names in phi"""
    result = """"""
    original_dot = original_dot.replace("fixedsize=true", "fixedsize=false")
    for line in original_dot.splitlines():
        new_line = line
        # ONLY LEFT
        found = re.search(SDD_LINE_LEFT_REGEX, line)
        if not found is None:
            key_start_location = re.search(SDD_KEY_START_LEFT_REGEX, line).start()
            key_end_location = re.search(SDD_KEY_END_LEFT_REGEX, line).start()
            new_line = re.sub(
                SDD_REPLACE_LEFT_REGEX,
                _get_string_from_atom(
                    mapping[line[key_start_location:key_end_location]]
                )
                + "|",
                new_line,
            )
        # ONLY RIGHT
        found = re.search(SDD_LINE_RIGHT_REGEX, line)
        if not found is None:
            key_start_location = re.search(SDD_KEY_START_RIGHT_REGEX, line).start()
            key_end_location = re.search(SDD_KEY_END_RIGHT_REGEX, line).start()
            new_line = re.sub(
                SDD_REPLACE_RIGHT_REGEX,
                _get_string_from_atom(
                    mapping[line[key_start_location:key_end_location]]
                )
                + '",',
                new_line,
            )
        # BOTH SIDES
        found = re.search(SDD_LINE_BOTH_REGEX, line)
        if not found is None:
            key_start_location = re.search(SDD_KEY_START_LEFT_REGEX, line).start()
            key_end_location = re.search(SDD_KEY_END_LEFT_REGEX, line).start()
            new_line = re.sub(
                SDD_REPLACE_LEFT_REGEX,
                _get_string_from_atom(
                    mapping[line[key_start_location:key_end_location]]
                )
                + "|",
                new_line,
            )
            key_start_location = re.search(SDD_KEY_START_RIGHT_REGEX, line).start()
            key_end_location = re.search(SDD_KEY_END_RIGHT_REGEX, line).start()
            new_line = re.sub(
                SDD_REPLACE_RIGHT_REGEX,
                _get_string_from_atom(
                    mapping[line[key_start_location:key_end_location]]
                )
                + '",',
                new_line,
            )
        result += (
            new_line
            + """
"""
        )
    return result


def save_sdd_object(
    sdd_object,
    output_file: str,
    mapping: dict[str, FNode],
    kind: str,
    dump_abstraction=False,
) -> bool:
    """saves an SDD object on a file"""
    dot_content = sdd_object.dot()
    if kind == "VTree":
        dot_content = translate_vtree_vars(dot_content, mapping)
    elif kind == "SDD" and not dump_abstraction:
        dot_content = translate_sdd_vars(dot_content, mapping)
    tokenized_output_file = output_file.split(".")
    if tokenized_output_file[len(tokenized_output_file) - 1] == "dot":
        with open(output_file, "w", encoding="utf8") as out:
            print(dot_content, file=out)
    elif tokenized_output_file[len(tokenized_output_file) - 1] == "svg":
        (graph,) = pydot.graph_from_dot_data(dot_content)
        graph.write_svg(output_file)
    else:
        return False
    return True
