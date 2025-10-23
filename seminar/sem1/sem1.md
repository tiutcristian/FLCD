# Seminar 1

Metalanguage
- used to describe another language
- BNF and EBNF

## BNF
### Constructs:
- meta-linguistic variables = **non-terminals** - written in angle brackets <...>
- **terminals** - written as they are (digits, characters)
- meta-linguistic connectives:
  - `::=` equals "by definition"
  - `|` alternative (OR)

### General shape of a BNF
`<construct> ::= <component1> | <component2> | ... | <componentN>`

### Examples: BNF for a simple arithmetic expression
#### 1. Even and odd digits
```
<even_digit> ::= 0 | 2 | 4 | 6 | 8
<odd_digit> ::= 1 | 3 | 5 | 7 | 9
```
#### 2. Letter sequences
```
<letter> ::= a | b | c | ... | z | A | B | C | ... | Z
<letter_sequence> ::= <letter> | <letter> <letter_sequence>
```

#### 3. Integer numbers
```
<digit> ::= 0 | 1 | ... | 9
<number> ::= 0 | <sign> <non_zero_number> | <non_zero_number>
<sign> ::= + | -
<non_zero_number> ::= <non_zero_digit> | <non_zero_digit> <digit_sequence>
<non_zero_digit> ::= 1 | 2 | ... | 9
<digit_sequence> ::= <digit> | <digit> <digit_sequence>
```

## EBNF
Changes compared to BNF:
1. Nonterminals lose <...> => written without angle brackets
2. Terminals are written in double quotes "..."
3. ::= becomes =
4. Rules end with a period .

New constructs:
- `{...}` = repetition (0 or more times)
- `[...]` = optional (0 or 1 time)
- `(...)` = grouping
- `(*...*)` = comment

### Examples: EBNF for a simple arithmetic expression
#### 1. Define numbers
```
non_zero_digit = "1" | ... | "9".
number = "0" | ["+" | "-"] non_zero_digit {"0" | non_zero_digit}.
```

## Mini-language

special tokens:
- separators: space, `;`, newline
- operators: `+`, `-`, `*`, `:=`, `=`, `<`, `>`, `<=`, `>=`, `<>`, `(`
- reserved keywords: `if`, `then`, `else`, `while`, `do`, `begin`, `end`, `var`, `integer`


### Examples
#### 1. Identifiers
```
letter = "a" | ... | "z" | "A" | ... | "Z".
digit = "0" | ... | "9".
identifier = letter {letter | digit | "_"}.
```
#### 2. Constant strings
```
letter = "a" | ... | "z" | "A" | ... | "Z".
digit = "0" | ... | "9".
char = letter | digit
string = {char}.
const_string = '"' string '"'.
```
