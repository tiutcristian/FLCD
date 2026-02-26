#!/bin/bash

if [ $# -lt 1 ]; then
  echo "Usage: $0 <source_file>"
  echo "Example: $0 program.src"
  exit 1
fi

SRC_FILE="$1"
BASENAME=$(basename "$SRC_FILE")
NAME_NO_EXT="${BASENAME%.*}"
OUT_DIR="output_${NAME_NO_EXT}"
mkdir -p "$OUT_DIR"

lex text_transform.lxi

gcc lex.yy.c -o scanner

PIF_OUT="$OUT_DIR/pif.txt"
ST_OUT="$OUT_DIR/st.txt"
ERR_OUT="$OUT_DIR/lex_errors.txt"

./scanner "$SRC_FILE" "$PIF_OUT" "$ST_OUT" "$ERR_OUT"

echo
echo "Output files generated in: $OUT_DIR"
echo "  - $PIF_OUT"
echo "  - $ST_OUT"
echo "  - $ERR_OUT"