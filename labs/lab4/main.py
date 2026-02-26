import sys
from grammar import parse_grammar_file
from fa import FA

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 main.py <grammar_file>", file=sys.stderr)
        sys.exit(1)

    grammar_path = sys.argv[1]

    g = parse_grammar_file(grammar_path)

    print("Loaded grammar:")
    print(g)
    print()

    fa = FA.from_grammar(g)
    print(fa.toString())

if __name__ == "__main__":
    main()