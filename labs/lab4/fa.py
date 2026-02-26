from dataclasses import dataclass
from typing import List

from grammar import Grammar


@dataclass
class FA:
    grammar: Grammar

    num_states: int
    start_state: int
    num_terminals: int

    terminal_names: List[str]
    accepting: List[int]
    transitions: List[List[int]]


    @staticmethod
    def from_grammar(g: Grammar) -> "FA":
        n_nt = len(g.nonterminals)
        final_state = n_nt

        num_states = n_nt + 1
        start_state = g.start_nt
        num_terminals = len(g.terminals)

        terminal_names = list(g.terminals)

        accepting = [0] * num_states
        transitions = [
            [0 for _ in range(num_terminals)]
            for _ in range(num_states)
        ]

        accepting[final_state] = 1

        for p in g.prods:
            from_state = p.left_nt

            if p.is_epsilon:
                accepting[from_state] = 1
            elif p.has_terminal and p.has_right_nt:
                term = p.terminal
                to_state = p.right_nt
                transitions[from_state][term] |= (1 << to_state)
            elif p.has_terminal and not p.has_right_nt:
                term = p.terminal
                transitions[from_state][term] |= (1 << final_state)

        return FA(
            grammar=g,
            num_states=num_states,
            start_state=start_state,
            num_terminals=num_terminals,
            terminal_names=terminal_names,
            accepting=accepting,
            transitions=transitions,
        )

    def toString(self) -> str:
        lines: List[str] = [
            "=== FA ===",
            f"States 0..{self.num_states - 1}:"
        ]

        for s in range(self.num_states):
            if s < len(self.grammar.nonterminals):
                state_name = f"q{s} = {self.grammar.nonterminals[s]}"
            else:
                state_name = f"q{s} = FINAL"
            if s == self.start_state:
                state_name += " [START]"
            lines.append("  " + state_name)

        lines.append("")
        lines.append("Accepting states:")
        for s in range(self.num_states):
            if self.accepting[s]:
                lines.append(f"  q{s}")

        lines.append("")
        lines.append("Transitions:")
        for s in range(self.num_states):
            for t in range(self.num_terminals):
                mask = self.transitions[s][t]
                if mask == 0:
                    continue
                dests = [
                    f"q{dst}"
                    for dst in range(self.num_states)
                    if mask & (1 << dst)
                ]
                lines.append(
                    f"  q{s} --{self.terminal_names[t]}--> {{ {' '.join(dests)} }}"
                )

        lines.append("=== END FA ===")
        return "\n".join(lines)