from dataclasses import dataclass
from typing import List


@dataclass
class Production:
    left_nt: int
    is_epsilon: bool
    has_terminal: bool
    terminal: int
    has_right_nt: bool
    right_nt: int


class Grammar:
    def __init__(self):
        self.nonterminals: List[str] = []
        self.terminals: List[str] = []
        self.start_nt: int = -1
        self.prods: List[Production] = []

    # --- symbol table helpers ---

    def find_nonterminal(self, name: str) -> int:
        try:
            return self.nonterminals.index(name)
        except ValueError:
            return -1

    def find_terminal(self, name: str) -> int:
        try:
            return self.terminals.index(name)
        except ValueError:
            return -1

    def add_nonterminal(self, name: str) -> int:
        if name not in self.nonterminals:
            self.nonterminals.append(name)
        return self.find_nonterminal(name)

    def add_terminal(self, name: str) -> int:
        if name not in self.terminals:
            self.terminals.append(name)
        return self.find_terminal(name)

    def add_production(
        self,
        left_nt: int,
        is_epsilon: bool,
        has_terminal: bool,
        terminal: int,
        has_right_nt: bool,
        right_nt: int,
    ):
        self.prods.append(
            Production(
                left_nt=left_nt,
                is_epsilon=is_epsilon,
                has_terminal=has_terminal,
                terminal=terminal,
                has_right_nt=has_right_nt,
                right_nt=right_nt,
            )
        )

    def __str__(self) -> str:
        out = [f"Nonterminals ({len(self.nonterminals)}): "
               + " ".join(self.nonterminals), f"Terminals ({len(self.terminals)}): "
               + " ".join(self.terminals)]
        if self.start_nt != -1:
            out.append(f"Start: {self.nonterminals[self.start_nt]}")
        else:
            out.append("Start: <UNSET>")

        out.append(f"Productions ({len(self.prods)}):")
        for p in self.prods:
            left_name = self.nonterminals[p.left_nt]
            if p.is_epsilon:
                right_str = "EPS"
            else:
                parts = []
                if p.has_terminal:
                    parts.append(self.terminals[p.terminal])
                if p.has_right_nt:
                    parts.append(self.nonterminals[p.right_nt])
                right_str = " ".join(parts)
            out.append(f"  {left_name} -> {right_str}")

        return "\n".join(out)


def _strip_comment(line: str) -> str:
    pos = line.find("#")
    if pos != -1:
        return line[:pos]
    return line


def _parse_comma_list(fragment: str) -> list[str]:
    parts = fragment.split(",")
    return [p.strip() for p in parts if p.strip() != ""]


def _handle_production_right(grammar: Grammar, left_idx: int, right_all: str):
    alts = [alt.strip() for alt in right_all.split("|")]

    for alt in alts:
        if alt == "":
            continue

        tokens = alt.split()
        if len(tokens) == 1:
            w1 = tokens[0]
            if w1 == "EPS":
                grammar.add_production(
                    left_nt=left_idx,
                    is_epsilon=True,
                    has_terminal=False,
                    terminal=-1,
                    has_right_nt=False,
                    right_nt=-1,
                )
            else: # left -> t
                t_idx = grammar.find_terminal(w1)
                if t_idx == -1:
                    raise ValueError(f"Terminal '{w1}' not declared")
                grammar.add_production(
                    left_nt=left_idx,
                    is_epsilon=False,
                    has_terminal=True,
                    terminal=t_idx,
                    has_right_nt=False,
                    right_nt=-1,
                )

        elif len(tokens) == 2: # left -> t nt
            w1, w2 = tokens
            t_idx = grammar.find_terminal(w1)
            if t_idx == -1:
                raise ValueError(f"Terminal '{w1}' not declared")
            nt_idx = grammar.find_nonterminal(w2)
            if nt_idx == -1:
                raise ValueError(f"Nonterminal '{w2}' not declared")

            grammar.add_production(
                left_nt=left_idx,
                is_epsilon=False,
                has_terminal=True,
                terminal=t_idx,
                has_right_nt=True,
                right_nt=nt_idx,
            )

        elif len(tokens) == 3 and tokens[0] =="'" and tokens[1] =="'": # space as terminal
            w2 = tokens[2]
            t_idx = grammar.find_terminal("' '")
            if t_idx == -1:
                raise ValueError(f"Terminal ' ' not declared")
            nt_idx = grammar.find_nonterminal(w2)
            if nt_idx == -1:
                raise ValueError(f"Nonterminal '{w2}' not declared")

            grammar.add_production(
                left_nt=left_idx,
                is_epsilon=False,
                has_terminal=True,
                terminal=t_idx,
                has_right_nt=True,
                right_nt=nt_idx,
            )
        else:
            raise ValueError(f"Too many symbols in alternative '{alt}'.")


def parse_grammar_file(path: str) -> Grammar:
    g = Grammar()
    in_productions = False

    with open(path, "r") as f:
        for rawline in f:
            line = _strip_comment(rawline).strip()
            if line == "":
                continue

            if not in_productions:
                if line.startswith("NONTERMINALS:"):
                    rest = line[len("NONTERMINALS:") :].strip()
                    nts = _parse_comma_list(rest)
                    for nt in nts:
                        g.add_nonterminal(nt)
                    continue

                if line.startswith("TERMINALS:"):
                    rest = line[len("TERMINALS:") :].strip()
                    ts = _parse_comma_list(rest)
                    for t in ts:
                        g.add_terminal(t)
                    continue

                if line.startswith("START:"):
                    rest = line[len("START:") :].strip()
                    idx = g.find_nonterminal(rest)
                    if idx == -1:
                        raise ValueError(
                            f"Start symbol {rest} not declared in NONTERMINALS"
                        )
                    g.start_nt = idx
                    continue

                if line.startswith("PRODUCTIONS:"):
                    in_productions = True
                    continue

            arrow_pos = line.find("->")
            if arrow_pos == -1:
                raise ValueError(f"Bad production line: {line}")

            left = line[:arrow_pos].strip()
            right_all = line[arrow_pos + 2 :].strip()

            left_idx = g.find_nonterminal(left)
            if left_idx == -1:
                raise ValueError(f"Left '{left}' not declared as nonterminal")

            _handle_production_right(g, left_idx, right_all)

    if g.start_nt == -1:
        raise ValueError("No START: found in grammar file")

    return g