from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Set, Tuple
import sys
import subprocess

EPSILON = "epsilon"
ENDMARK = "$"

class Grammar:
    def __init__(self):
        self.nonterminals: Set[str] = set()
        self.terminals: Set[str] = set()
        self.start_symbol: str = ""
        self.productions: Dict[str, List[List[str]]] = {}  # productions[nonterminal] = list of RHS (each RHS = list of symbols)

    @staticmethod
    def from_file(path: Path) -> "Grammar":
        g = Grammar()
        section = None

        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # NEW: section headers start with '#'
                if line.startswith("# NonTerminals"):
                    section = "NonTerminals"
                    continue
                if line.startswith("# Terminals"):
                    section = "Terminals"
                    continue
                if line.startswith("# StartSymbol"):
                    section = "StartSymbol"
                    continue
                if line.startswith("# Productions"):
                    section = "Productions"
                    continue

                if line == "---":
                    section = None
                    continue

                if section == "NonTerminals":
                    g.nonterminals.add(line)
                elif section == "Terminals":
                    g.terminals.add(line)
                elif section == "StartSymbol":
                    g.start_symbol = line
                elif section == "Productions":
                    left, right = map(str.strip, line.split("->"))
                    rhs_symbols = right.split()
                    g.productions.setdefault(left, []).append(rhs_symbols)

        return g


# ---------------------------
# FIRST and FOLLOW sets
# ---------------------------

def compute_first_sets(g: Grammar) -> Dict[str, Set[str]]:
    first: Dict[str, Set[str]] = {}

    # initialize
    for t in g.terminals:
        first[t] = {t}
    for nt in g.nonterminals:
        first.setdefault(nt, set())
    first[EPSILON] = {EPSILON}

    changed = True
    while changed:
        changed = False
        for A, prods in g.productions.items():
            for rhs in prods:
                # FIRST(rhs)
                nullable_prefix = True
                if rhs == [EPSILON]:
                    if EPSILON not in first[A]:
                        first[A].add(EPSILON)
                        changed = True
                    continue

                for X in rhs:
                    for a in first.setdefault(X, set()):
                        if a != EPSILON and a not in first[A]:
                            first[A].add(a)
                            changed = True
                    if EPSILON not in first.setdefault(X, set()):
                        nullable_prefix = False
                        break

                if nullable_prefix:
                    if EPSILON not in first[A]:
                        first[A].add(EPSILON)
                        changed = True

    return first


def first_of_sequence(seq: List[str],
                      first_sets: Dict[str, Set[str]]) -> Set[str]:
    if not seq or seq == [EPSILON]:
        return {EPSILON}

    result: Set[str] = set()
    nullable_prefix = True

    for X in seq:
        sym_first = first_sets.get(X, {X})
        result |= {a for a in sym_first if a != EPSILON}
        if EPSILON not in sym_first:
            nullable_prefix = False
            break

    if nullable_prefix:
        result.add(EPSILON)

    return result


def compute_follow_sets(g: Grammar,
                        first_sets: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    follow: Dict[str, Set[str]] = {nt: set() for nt in g.nonterminals}
    follow[g.start_symbol].add(ENDMARK)

    changed = True
    while changed:
        changed = False
        for A, prods in g.productions.items():
            for rhs in prods:
                trailer = follow[A].copy()
                for X in reversed(rhs):
                    if X in g.nonterminals:
                        before = len(follow[X])
                        follow[X] |= trailer
                        if len(follow[X]) > before:
                            changed = True

                        first_X = first_sets.get(X, set())
                        if EPSILON in first_X:
                            trailer = trailer | {a for a in first_X if a != EPSILON}
                        else:
                            trailer = {a for a in first_X if a != EPSILON}
                    else:
                        trailer = {X}

    return follow


# ---------------------------
# LL(1) table construction
# ---------------------------

def build_ll1_table(
    g: Grammar,
    first_sets: Dict[str, Set[str]],
    follow_sets: Dict[str, Set[str]]
) -> Dict[str, Dict[str, List[str]]]:
    table: Dict[str, Dict[str, List[str]]] = {nt: {} for nt in g.nonterminals}

    for A, prods in g.productions.items():
        for rhs in prods:
            first_rhs = first_of_sequence(rhs, first_sets)
            # for each terminal in FIRST(rhs) \ {epsilon}
            for a in (first_rhs - {EPSILON}):
                if a in table[A]:
                    raise ValueError(f"LL(1) conflict at table[{A}][{a}]")
                table[A][a] = rhs

            # if epsilon in FIRST(rhs)
            if EPSILON in first_rhs:
                for b in follow_sets[A]:
                    if b in table[A]:
                        raise ValueError(f"LL(1) conflict at table[{A}][{b}]")
                    table[A][b] = rhs

    return table


# ---------------------------
# Parse tree representation
# ---------------------------

@dataclass
class Node:
    index: int
    symbol: str
    father: int  # -1 if none
    sibling: int  # -1 if none


# ---------------------------
# Parsing algorithms
# ---------------------------

def parse_sequence(
    g: Grammar,
    table: Dict[str, Dict[str, List[str]]],
    tokens: List[str]
) -> List[Tuple[str, List[str]]]:
    """
    Requirement 1:
    Input: grammar, sequence of terminals (tokens)
    Output: list of productions used as (A, RHS)
    """
    tokens = tokens + [ENDMARK]
    stack: List[str] = [ENDMARK, g.start_symbol]
    i = 0
    productions_used: List[Tuple[str, List[str]]] = []

    while stack:
        top = stack.pop()
        current = tokens[i]

        if top in g.terminals or top == ENDMARK:
            if top == current:
                i += 1
            else:
                raise ValueError(f"Parsing error: expected {top}, got {current}")
        elif top in g.nonterminals:
            if current not in table[top]:
                raise ValueError(f"No rule for ({top}, {current}) in LL(1) table")
            rhs = table[top][current]
            productions_used.append((top, rhs))
            # push RHS in reverse order (ignore epsilon)
            if rhs != [EPSILON]:
                for sym in reversed(rhs):
                    stack.append(sym)
        else:
            raise ValueError(f"Unknown symbol on stack: {top}")

        if current == ENDMARK and not stack:
            break

    return productions_used


def parse_with_tree(
    g: Grammar,
    table: Dict[str, Dict[str, List[str]]],
    tokens: List[str]
) -> List[Node]:
    """
    Requirement 2:
    Input: grammar, sequence of tokens (e.g. from PIF, but here just raw terminals)
    Output: parse tree as a list of Nodes (father + sibling representation)
    """
    tokens = tokens + [ENDMARK]
    nodes: List[Node] = []
    # root
    root_index = 0
    nodes.append(Node(index=root_index, symbol=g.start_symbol, father=-1, sibling=-1))

    # stack elements: (symbol, node_index)
    stack: List[Tuple[str, int]] = [(ENDMARK, -1), (g.start_symbol, root_index)]
    i = 0

    while stack:
        top_sym, top_idx = stack.pop()
        current = tokens[i]

        if top_sym in g.terminals or top_sym == ENDMARK:
            if top_sym == current:
                i += 1
            else:
                raise ValueError(
                    f"Parsing error at token {i}: expected {top_sym}, got {current}"
                )
        elif top_sym in g.nonterminals:
            if current not in table[top_sym]:
                raise ValueError(f"No rule for ({top_sym}, {current}) in LL(1) table")
            rhs = table[top_sym][current]

            if rhs != [EPSILON]:
                child_indices: List[int] = []
                for sym in rhs:
                    idx = len(nodes)
                    nodes.append(Node(index=idx, symbol=sym, father=top_idx, sibling=-1))
                    child_indices.append(idx)

                # set sibling pointers
                for j in range(len(child_indices) - 1):
                    nodes[child_indices[j]].sibling = child_indices[j + 1]

                # push RHS in reverse with their node indices
                for sym, idx in reversed(list(zip(rhs, child_indices))):
                    stack.append((sym, idx))
            # epsilon -> no children
        else:
            raise ValueError(f"Unknown symbol on stack: {top_sym}")

        if current == ENDMARK and not stack:
            break

    return nodes


# ---------------------------
# Utility: print parse tree table
# ---------------------------

def print_parse_tree(nodes: List[Node]) -> None:
    print(f"{'Idx':<5} {'Symbol':<10} {'Father':<10} {'Sibling':<10}")
    print("-" * 40)
    for n in nodes:
        print(f"{n.index:<5} {n.symbol:<15} {n.father:<10} {n.sibling:<10}")


class OutputType(Enum):
    PRODUCTIONS = 1
    PARSE_TREE = 2


def PIF_to_tokens(pif_file_path: Path) -> List[str]:
    code_to_terminal = {
        256: "LOAD",
        257: "REPLACE",
        258: "WITH",
        259: "SPLIT",
        260: "BY",
        261: "JOIN",
        262: "TRIM",
        263: "UPPERCASE",
        264: "LOWERCASE",
        265: "SAVE",
        266: "ASSIGN",
        267: "ID",
        268: "STRING",
    }

    tokens: List[str] = []
    with open(pif_file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            comma_idx = line.find(",")
            if comma_idx == -1 or not line.startswith("("):
                raise ValueError(f"Malformed PIF line: {line}")
            code = int(line[1:comma_idx].strip())
            if code not in code_to_terminal:
                raise ValueError(f"Unknown token code in PIF: {code}")
            tokens.append(code_to_terminal[code])

    return tokens


def main(
        grammar_file_path: Path,
        output_type: OutputType,
        pif_file_path: Path = None,
        sequence: List[str] = None
):
    g = Grammar.from_file(grammar_file_path)

    first_sets = compute_first_sets(g)
    follow_sets = compute_follow_sets(g, first_sets)
    table = build_ll1_table(g, first_sets, follow_sets)

    if output_type == OutputType.PRODUCTIONS:
        prods = parse_sequence(g, table, sequence)
        print("Productions used:")
        for left, rhs in prods:
            print(f"{left} -> {' '.join(rhs)}")
    elif output_type == OutputType.PARSE_TREE:
        sequence = PIF_to_tokens(pif_file_path)
        nodes = parse_with_tree(g, table, sequence)
        print_parse_tree(nodes)
    

if __name__ == "__main__":
    req = sys.argv[1] if len(sys.argv) > 1 else "req1"

    if req == "req2":
        subprocess.run(["./req2/get_PIFs.sh > /dev/null"], check=True, shell=True)
        main(
            grammar_file_path=Path("req2") / "grammar.txt",
            pif_file_path=Path("req2") / "prog1_PIF.txt",
            output_type=OutputType.PARSE_TREE
        )
    else:
        main(
            grammar_file_path=Path("req1") / "seminar_grammar.txt",
            sequence=["a", "+", "a"],
            output_type=OutputType.PRODUCTIONS
        )
