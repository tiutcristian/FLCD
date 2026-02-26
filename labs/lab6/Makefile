PARSER = minidsl.y
SCANNER = text_transform.lxi

PARSER_C = minidsl.tab.c
PARSER_H = minidsl.tab.h
SCANNER_C = lex.yy.c

EXEC = minidsl

OUTPUT = parser_out.txt

CC = gcc

# Build rules

all: $(EXEC)

$(PARSER_C) $(PARSER_H): $(PARSER)
	bison -d -o $(PARSER_C) $(PARSER)

$(SCANNER_C): $(SCANNER)
	flex $(SCANNER)

$(EXEC): $(PARSER_C) $(SCANNER_C)
	$(CC) $(PARSER_C) $(SCANNER_C) -o $(EXEC)

clean:
	rm -f $(PARSER_C) $(PARSER_H) $(SCANNER_C) $(EXEC) $(OUTPUT)

clean-gen:
	rm -f $(PARSER_C) $(PARSER_H) $(SCANNER_C) $(OUTPUT)

rebuild: clean all

run: $(EXEC)
	./$(EXEC)

.PHONY: all clean clean-gen rebuild run