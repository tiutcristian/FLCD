%{
#include <stdio.h>
#include <stdlib.h>

int yylex(void);
void yyrestart(FILE *input_file);
extern FILE *yyin;

static FILE *g_out = NULL;

void yyerror(const char *s) {
    if (g_out) {
        fprintf(g_out, "Parse error: %s\n", s);
    }
    fprintf(stderr, "Parse error: %s\n", s);
}
%}

%union {
    char *str;   /* for ID and STRING lexemes */
}

/* Tokens */
%token LOAD
%token REPLACE
%token WITH
%token SPLIT
%token BY
%token JOIN
%token TRIM
%token UPPERCASE
%token LOWERCASE
%token SAVE
%token ASSIGN
%token <str> ID
%token <str> STRING

%start program

%%

/* -------------------- Parser rules -------------------- */

program
    : statement_list
    ;

statement_list
    : /* empty */
    | statement_list statement
    ;

statement
    : load_stmt
    | replace_stmt
    | split_stmt
    | join_stmt
    | trim_stmt
    | uppercase_stmt
    | lowercase_stmt
    | save_stmt
    | assignment_stmt
    ;

load_stmt
    : LOAD ID
      {
        fprintf(g_out, "LOAD %s\n", $2);
        free($2);
      }
    ;

replace_stmt
    : REPLACE STRING WITH STRING
      {
        fprintf(g_out, "REPLACE %s WITH %s\n", $2, $4);
        free($2);
        free($4);
      }
    ;

split_stmt
    : SPLIT BY STRING
      {
        fprintf(g_out, "SPLIT BY %s\n", $3);
        free($3);
      }
    ;

join_stmt
    : JOIN WITH STRING
      {
        fprintf(g_out, "JOIN WITH %s\n", $3);
        free($3);
      }
    ;

trim_stmt
    : TRIM
      {
        fprintf(g_out, "TRIM\n");
      }
    ;

uppercase_stmt
    : UPPERCASE
      {
        fprintf(g_out, "UPPERCASE\n");
      }
    ;

lowercase_stmt
    : LOWERCASE
      {
        fprintf(g_out, "LOWERCASE\n");
      }
    ;

save_stmt
    : SAVE ID
      {
        fprintf(g_out, "SAVE %s\n", $2);
        free($2);
      }
    ;

assignment_stmt
    : ID ASSIGN STRING
      {
        fprintf(g_out, "ASSIGN %s = %s\n", $1, $3);
        free($1);
        free($3);
      }
    ;

%%

int main(int argc, char **argv) {
    const char *in_path  = NULL;
    const char *out_path = "parser_out.txt";

    if (argc >= 2) in_path  = argv[1];
    if (argc >= 3) out_path = argv[2];

    yyin = fopen(in_path, "r");
    if (!yyin) {
        fprintf(stderr, "Cannot open input file: %s\n", in_path);
        return 1;
    }

    g_out = fopen(out_path, "w");
    if (!g_out) {
        fprintf(stderr, "Cannot open output file: %s\n", out_path);
        if (yyin && yyin != stdin) fclose(yyin);
        return 1;
    }

    int rc = yyparse();

    if (rc == 0) {
        fprintf(g_out, "OK\n");
    } else {
        fprintf(g_out, "FAILED\n");
    }

    if (yyin && yyin != stdin) fclose(yyin);
    fclose(g_out);
    return rc ? 1 : 0;
}