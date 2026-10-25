#!/usr/bin/env python3
"""Generate a representation of a GDScript solution."""

import argparse
import json
import pathlib
import sys

import gdtoolkit.parser
from lark import Token, Tree


def load_config(input_path: pathlib.Path) -> dict | None:
    """Return the contents of .meta/config.json if it exists, or None."""
    config_path = input_path / ".meta/config.json"
    if not config_path.exists():
        return None
    return json.loads((input_path / ".meta/config.json").read_text())


def solution_files(slug: str, input_path: pathlib.Path) -> list[pathlib.Path]:
    """Return the solution files, based on the config.json if available, or the slug."""
    config = load_config(input_path)
    if config:
        files = config.get("files", {}).get("solution", [])
        if files:
            return [input_path / file for file in files]
    return [(input_path / slug.replace("-", "_")).with_suffix(".gd")]


def load_ast(slug: str, input_path: pathlib.Path) -> list[Tree]:
    """Return the AST Trees for each solution file."""
    return [
        gdtoolkit.parser.parser.parse(file.read_text())
        for file in solution_files(slug, input_path)
    ]


def drop_docstr(trees: list[Tree]) -> list[Tree]:
    """Remove module docstrings and string-statements from the AST."""

    def skip(t: Tree | Token) -> bool:
        """Return if a node should be skipped."""
        if isinstance(t, Tree) and t.data == "docstr_stmt":
            return True
        if (
            isinstance(t, Tree)
            and t.data == "expr_stmt"
            and len(t.children) == 1
            and isinstance(t.children[0], Tree)
            and t.children[0].data == "expr"
            and len(t.children[0].children) == 1
            and isinstance(t.children[0].children[0], Tree)
            and t.children[0].children[0].data == "string"
        ):
            return True
        return False

    def translate(t: Tree | Token) -> Tree | Token:
        """Return a node, removing docstrings."""
        if isinstance(t, Token):
            return t
        elif isinstance(t, Tree):
            return Tree(t.data, [translate(i) for i in t.children if not skip(i)])
        else:
            raise ValueError(t)

    return [translate(tree) for tree in trees]


def replace_func_names(trees: list[Tree]) -> tuple[list[Tree], dict[str, str]]:
    """Replace custom function names with placeholders."""
    varmap = {}
    for tree in trees:
        func_names = [
            next(i.find_token("NAME"))
            for i in tree.find_data(Token("RULE", "func_header"))
        ]
        for var in func_names:
            if var.value not in varmap:
                varmap[var.value] = f"FUNC_{len(varmap) + 1:03d}"

    def translate(t):
        if isinstance(t, Token):
            return Token(t.type, varmap.get(t.value, t.value))
        elif isinstance(t, Tree):
            return Tree(t.data, [translate(i) for i in t.children])
        else:
            raise ValueError(t)

    revmap = {v: k for k, v in varmap.items()}

    trees = [translate(tree) for tree in trees]
    return trees, revmap


def replace_var_names(trees: list[Tree]) -> tuple[list[Tree], dict[str, str]]:
    """Replace function variables with placeholders.

    This does not handle constants and module level variables.
    """
    varmap = {}
    for tree in trees:
        func_vars = [
            next(i.find_token("NAME"))
            for token_type in ["func_var_stmt", "func_arg_typed", "func_arg_regular"]
            for i in tree.find_data(Token("RULE", token_type))
        ]
        func_vars.sort(key=lambda x: x.line)
        for var in func_vars:
            if var.value not in varmap:
                varmap[var.value] = f"FUNCVAR_{len(varmap) + 1:03d}"

    def translate(t):
        if isinstance(t, Token):
            return Token(t.type, varmap.get(t.value, t.value))
        elif isinstance(t, Tree):
            return Tree(t.data, [translate(i) for i in t.children])
        else:
            raise ValueError(t)

    revmap = {v: k for k, v in varmap.items()}

    trees = [translate(tree) for tree in trees]
    return trees, revmap


def write_output(output_path: pathlib.Path, trees: list[Tree], varmap: dict[str, str]) -> None:
    """Write the representer files."""
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    (output_path / "representation.json").write_text(json.dumps({"version": 1}, indent=2) + "\n")
    (output_path / "mapping.json").write_text(json.dumps(varmap, indent=2, sort_keys=True) + "\n")
    (output_path / "representation.txt").write_text("\n\n".join(tree.pretty() for tree in trees))



def arg_parser() -> argparse.ArgumentParser:
    """Return an ArgumentParser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    return parser


def main() -> None:
    """Generate a representation."""
    args = arg_parser().parse_args()
    input_path = pathlib.Path(args.input_dir)
    output_path = pathlib.Path(args.output_dir)

    print(f"== Creating representation for {args.slug!r} ==")
    trees = load_ast(args.slug, input_path)
    trees = drop_docstr(trees)
    trees, varmap = replace_var_names(trees)
    trees, funcmap = replace_func_names(trees)
    write_output(output_path, trees, varmap | funcmap)
    print(f"== Done with {args.slug!r} ==")


if __name__ == "__main__":
    main()
