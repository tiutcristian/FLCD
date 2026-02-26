# Documentation

## 1. Build Process
To run the scanner, use the provided bash script:
```bash
./run_scanner.sh <program.txt>
```

which automatically creates an output folder such as `output_<program_name_no_ext>` which contains:
- pif.txt
- st.txt
- lex_errors.txt

## 2. Tools

| Tool	| Purpose
|-------|--------
|Lex	| Generates the lexical analyzer (scanner) from a .lxi specification file.
|GCC	| Compiles the generated C code into an executable (scanner).
|Bash (`run_scanner.sh` / `cleanup.sh`)	| Automates the build and cleanup processes.
|C Language	| Provides data structures and logic for the Symbol Table, Program Internal Form, and error handling.

## 3. Lexical Tokens Detection

The scanner identifies and categorizes the following lexical tokens:

- keywords:
    - LOAD
    - SAVE
    - REPLACE
    - WITH
    - SPLIT
    - BY
    - JOIN
    - TRIM
    - UPPERCASE
    - LOWERCASE
- operators:
    - = (assignment operator)
- identifiers:
    - user-defined variable names
- constants:
    - string constants enclosed in double quotes
- separators:
    - whitespace and newline characters


### 3.1 Keywords

Each reserved word is matched by a single regular expression:

```
KEYWORD     LOAD|REPLACE|WITH|SPLIT|BY|JOIN|TRIM|UPPERCASE|LOWERCASE|SAVE
```

and handled as:

```C
{KEYWORD}   { TokenCode c = keyword_code(yytext);
            pif_push(&Pif, c, -1, -1); }
```

### 3.2 Identifiers

Identifiers match:

```
ID  [a-z][a-z0-9]*
```

and are processed as:

```C
{ID} { STNode *n = st_insert(&ST, yytext);
       pif_push(&Pif, T_ID, n->bucket_index, n->order_index); }
```

Each new identifier is inserted in the Symbol Table and referenced in the PIF by its (bucket, index) position.

### 3.3 String Constants

String constants are defined as:

```C
{STRING} { STNode *n = st_insert(&ST, yytext);
           pif_push(&Pif, T_STRING, n->bucket_index, n->order_index); }
```
```
STRING  \"([^"\n])*\"
```

and inserted into the Symbol Table similarly to identifiers.


### 3.4 Operators and Delimiters

The assignment operator is recognized directly:

```
"="   { pif_push(&Pif, T_ASSIGN, -1, -1); }
```

Whitespace and newlines are ignored.

### 3.5 Lexical Errors

Any unrecognized character produces an error entry:

```C
.  { char buf[256];
     snprintf(buf, sizeof(buf), "Unrecognized character: '%s'", yytext);
     err_push(yylineno, buf); }
```

All errors are stored and later written to lex_errors.txt.


## 4. Data Structures

### 4.1 Symbol Table
Structure:
```C
typedef struct STNode {
    char *lexeme;
    struct STNode *next;
    int bucket_index;
    int order_index;
} STNode;

typedef struct {
    STNode *buckets[211];
    int bucket_sizes[211];
} SymbolTable;
```

**Operations:**

| Function     | Description                                     |
|--------------|-------------------------------------------------|
| st_init()    | Initializes the hash table.                     |
| st_hash()    | Computes hash of a string.                      |
| st_lookup()  | Checks if a lexeme already exists.              |
| st_insert()  | Inserts new lexeme and returns its node.        |
| st_dump()    | Writes the full content of the ST to st.txt.    |

Each entry has a (bucket_index, order_index) used to uniquely identify it in the PIF.


### 4.2 Program Internal Form
Structure:
```C
typedef struct {
    TokenCode code;
    int st_bucket;
    int st_index;
} PIFEntry;

typedef struct {
  PIFEntry *v;
  int size, cap;
} PIF;
```

**Operations:**

| Function     | Description                                            |
|--------------|--------------------------------------------------------|
| pif_init()   | Allocates initial vector of entries.                   |
| pif_push()   | Adds a new token reference.                            |
| pif_dump()   | Writes all tokens and their ST positions to pif.txt.   |

### 4.3 Error List
Structure:
```C
typedef struct {
    int line;
    char what[1024];
} LexErr;
```