#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <stdexcept>
#include <iomanip>

using namespace std;

static const string EPSILON = "epsilon";
static const string ENDMARK = "$";

struct Grammar {
    unordered_set<string> nonterminals;
    unordered_set<string> terminals;
    string start_symbol;
    unordered_map<string, vector<vector<string>>> productions; // A -> [rhs1, rhs2, ...]

    static string trim(const string& s) {
        size_t b = s.find_first_not_of(" \t\r\n");
        if (b == string::npos) return "";
        size_t e = s.find_last_not_of(" \t\r\n");
        return s.substr(b, e - b + 1);
    }

    static vector<string> split_ws(const string& s) {
        vector<string> out;
        istringstream iss(s);
        string tok;
        while (iss >> tok) out.push_back(tok);
        return out;
    }

    static Grammar from_file(const string& path) {
        Grammar g;
        string section;

        ifstream in(path);
        if (!in) throw runtime_error("Cannot open grammar file: " + path);

        string line;
        while (getline(in, line)) {
            line = trim(line);
            if (line.empty()) continue;

            if (line.rfind("# NonTerminals", 0) == 0) { section = "NonTerminals"; continue; }
            if (line.rfind("# Terminals", 0) == 0)     { section = "Terminals"; continue; }
            if (line.rfind("# StartSymbol", 0) == 0)   { section = "StartSymbol"; continue; }
            if (line.rfind("# Productions", 0) == 0)   { section = "Productions"; continue; }

            if (line == "---") { section.clear(); continue; }

            if (section == "NonTerminals") {
                g.nonterminals.insert(line);
            } else if (section == "Terminals") {
                g.terminals.insert(line);
            } else if (section == "StartSymbol") {
                g.start_symbol = line;
            } else if (section == "Productions") {
                auto pos = line.find("->");
                if (pos == string::npos) throw runtime_error("Malformed production line: " + line);
                string left = trim(line.substr(0, pos));
                string right = trim(line.substr(pos + 2));
                vector<string> rhs = split_ws(right);
                if (rhs.empty()) rhs = {EPSILON};
                g.productions[left].push_back(rhs);
            }
        }

        if (g.start_symbol.empty()) {
            throw runtime_error("Grammar start symbol is empty (missing # StartSymbol section?)");
        }
        return g;
    }

    bool is_terminal(const string& s) const { return terminals.find(s) != terminals.end(); }
    bool is_nonterminal(const string& s) const { return nonterminals.find(s) != nonterminals.end(); }
};

using SetSS = unordered_set<string>;
using FirstFollow = unordered_map<string, SetSS>;
using LL1Table = unordered_map<string, unordered_map<string, vector<string>>>;

static bool insert_all(SetSS& dst, const SetSS& src) {
    bool changed = false;
    for (const auto& x : src) {
        if (dst.insert(x).second) changed = true;
    }
    return changed;
}

static FirstFollow compute_first_sets(const Grammar& g) {
    FirstFollow first;

    for (const auto& t : g.terminals) first[t] = {t};
    for (const auto& nt : g.nonterminals) first[nt] = {};
    first[EPSILON] = {EPSILON};

    bool changed = true;
    while (changed) {
        changed = false;
        for (const auto& kv : g.productions) {
            const string& A = kv.first;
            const auto& prods = kv.second;

            for (const auto& rhs : prods) {
                bool nullable_prefix = true;

                if (rhs.size() == 1 && rhs[0] == EPSILON) {
                    if (first[A].insert(EPSILON).second) changed = true;
                    continue;
                }

                for (const auto& X : rhs) {
                    if (first.find(X) == first.end()) {
                        // If X wasn't declared as terminal/nonterminal, treat it as a terminal.
                        first[X] = {X};
                    }

                    for (const auto& a : first[X]) {
                        if (a != EPSILON) {
                            if (first[A].insert(a).second) changed = true;
                        }
                    }

                    if (first[X].find(EPSILON) == first[X].end()) {
                        nullable_prefix = false;
                        break;
                    }
                }

                if (nullable_prefix) {
                    if (first[A].insert(EPSILON).second) changed = true;
                }
            }
        }
    }

    return first;
}

static SetSS first_of_sequence(const vector<string>& seq, const FirstFollow& first_sets) {
    if (seq.empty() || (seq.size() == 1 && seq[0] == EPSILON)) return {EPSILON};

    SetSS result;
    bool nullable_prefix = true;

    for (const auto& X : seq) {
        auto it = first_sets.find(X);
        SetSS sym_first = (it == first_sets.end()) ? SetSS{X} : it->second;

        for (const auto& a : sym_first) if (a != EPSILON) result.insert(a);

        if (sym_first.find(EPSILON) == sym_first.end()) {
            nullable_prefix = false;
            break;
        }
    }

    if (nullable_prefix) result.insert(EPSILON);
    return result;
}

static FirstFollow compute_follow_sets(const Grammar& g, const FirstFollow& first_sets) {
    FirstFollow follow;
    for (const auto& nt : g.nonterminals) follow[nt] = {};
    follow[g.start_symbol].insert(ENDMARK);

    bool changed = true;
    while (changed) {
        changed = false;
        for (const auto& kv : g.productions) {
            const string& A = kv.first;
            const auto& prods = kv.second;

            for (const auto& rhs : prods) {
                SetSS trailer = follow[A];

                for (auto it = rhs.rbegin(); it != rhs.rend(); ++it) {
                    const string& X = *it;

                    if (g.is_nonterminal(X)) {
                        size_t before = follow[X].size();
                        insert_all(follow[X], trailer);
                        if (follow[X].size() > before) changed = true;

                        auto fx_it = first_sets.find(X);
                        SetSS first_X = (fx_it == first_sets.end()) ? SetSS{} : fx_it->second;

                        if (first_X.find(EPSILON) != first_X.end()) {
                            SetSS add;
                            for (const auto& a : first_X) if (a != EPSILON) add.insert(a);
                            insert_all(trailer, add);
                        } else {
                            trailer.clear();
                            for (const auto& a : first_X) if (a != EPSILON) trailer.insert(a);
                        }
                    } else {
                        trailer.clear();
                        trailer.insert(X);
                    }
                }
            }
        }
    }

    return follow;
}

static LL1Table build_ll1_table(const Grammar& g, const FirstFollow& first_sets, const FirstFollow& follow_sets) {
    LL1Table table;
    for (const auto& nt : g.nonterminals) table[nt] = {};

    for (const auto& kv : g.productions) {
        const string& A = kv.first;
        const auto& prods = kv.second;

        for (const auto& rhs : prods) {
            auto first_rhs = first_of_sequence(rhs, first_sets);

            for (const auto& a : first_rhs) {
                if (a == EPSILON) continue;
                if (table[A].count(a)) {
                    throw runtime_error("LL(1) conflict at table[" + A + "][" + a + "]");
                }
                table[A][a] = rhs;
            }

            if (first_rhs.find(EPSILON) != first_rhs.end()) {
                auto it = follow_sets.find(A);
                if (it != follow_sets.end()) {
                    for (const auto& b : it->second) {
                        if (table[A].count(b)) {
                            throw runtime_error("LL(1) conflict at table[" + A + "][" + b + "]");
                        }
                        table[A][b] = rhs;
                    }
                }
            }
        }
    }

    return table;
}

struct Node {
    int index;
    string symbol;
    int father;   // -1 if none
    int sibling;  // -1 if none
};

static vector<pair<string, vector<string>>> parse_sequence(
    const Grammar& g,
    const LL1Table& table,
    vector<string> tokens
) {
    tokens.push_back(ENDMARK);
    vector<string> st = {ENDMARK, g.start_symbol};

    size_t i = 0;
    vector<pair<string, vector<string>>> productions_used;

    while (!st.empty()) {
        string top = st.back(); st.pop_back();
        string current = tokens.at(i);

        if (g.is_terminal(top) || top == ENDMARK) {
            if (top == current) i++;
            else throw runtime_error("Parsing error: expected " + top + ", got " + current);
        } else if (g.is_nonterminal(top)) {
            auto row_it = table.find(top);
            if (row_it == table.end() || row_it->second.find(current) == row_it->second.end()) {
                throw runtime_error("No rule for (" + top + ", " + current + ") in LL(1) table");
            }
            const auto& rhs = row_it->second.at(current);
            productions_used.push_back({top, rhs});

            if (!(rhs.size() == 1 && rhs[0] == EPSILON)) {
                for (auto it = rhs.rbegin(); it != rhs.rend(); ++it) st.push_back(*it);
            }
        } else {
            throw runtime_error("Unknown symbol on stack: " + top);
        }

        if (current == ENDMARK && st.empty()) break;
    }

    return productions_used;
}

static vector<Node> parse_with_tree(
    const Grammar& g,
    const LL1Table& table,
    vector<string> tokens
) {
    tokens.push_back(ENDMARK);

    vector<Node> nodes;
    nodes.push_back(Node{0, g.start_symbol, -1, -1});

    vector<pair<string,int>> st = {{ENDMARK, -1}, {g.start_symbol, 0}};

    size_t i = 0;
    while (!st.empty()) {
        auto [top_sym, top_idx] = st.back(); st.pop_back();
        string current = tokens.at(i);

        if (g.is_terminal(top_sym) || top_sym == ENDMARK) {
            if (top_sym == current) i++;
            else throw runtime_error("Parsing error at token " + to_string(i) + ": expected " + top_sym + ", got " + current);
        } else if (g.is_nonterminal(top_sym)) {
            auto row_it = table.find(top_sym);
            if (row_it == table.end() || row_it->second.find(current) == row_it->second.end()) {
                throw runtime_error("No rule for (" + top_sym + ", " + current + ") in LL(1) table");
            }
            const auto& rhs = row_it->second.at(current);

            if (!(rhs.size() == 1 && rhs[0] == EPSILON)) {
                vector<int> child_indices;
                child_indices.reserve(rhs.size());

                for (const auto& sym : rhs) {
                    int idx = (int)nodes.size();
                    nodes.push_back(Node{idx, sym, top_idx, -1});
                    child_indices.push_back(idx);
                }

                for (size_t j = 0; j + 1 < child_indices.size(); j++) {
                    nodes[child_indices[j]].sibling = child_indices[j + 1];
                }

                for (int k = (int)rhs.size() - 1; k >= 0; k--) {
                    st.push_back({rhs[(size_t)k], child_indices[(size_t)k]});
                }
            }
        } else {
            throw runtime_error("Unknown symbol on stack: " + top_sym);
        }

        if (current == ENDMARK && st.empty()) break;
    }

    return nodes;
}

static void print_parse_tree(const vector<Node>& nodes) {
    cout << left << setw(5) << "Idx" << setw(15) << "Symbol" << setw(10) << "Father" << setw(10) << "Sibling" << "\n";
    cout << string(40, '-') << "\n";
    for (const auto& n : nodes) {
        cout << left << setw(5) << n.index << setw(15) << n.symbol << setw(10) << n.father << setw(10) << n.sibling << "\n";
    }
}

static vector<string> pif_to_tokens(const string& pif_file_path) {
    unordered_map<int,string> code_to_terminal = {
        {256, "LOAD"}, {257, "REPLACE"}, {258, "WITH"}, {259, "SPLIT"},
        {260, "BY"},   {261, "JOIN"},    {262, "TRIM"}, {263, "UPPERCASE"},
        {264, "LOWERCASE"}, {265, "SAVE"}, {266, "ASSIGN"}, {267, "ID"}, {268, "STRING"},
    };

    ifstream in(pif_file_path);
    if (!in) throw runtime_error("Cannot open PIF file: " + pif_file_path);

    vector<string> tokens;
    string line;
    while (getline(in, line)) {
        line = Grammar::trim(line);
        if (line.empty()) continue;

        auto comma_idx = line.find(',');
        if (comma_idx == string::npos || line[0] != '(') {
            throw runtime_error("Malformed PIF line: " + line);
        }

        string code_str = Grammar::trim(line.substr(1, comma_idx - 1));
        int code = stoi(code_str);

        auto it = code_to_terminal.find(code);
        if (it == code_to_terminal.end()) {
            throw runtime_error("Unknown token code in PIF: " + to_string(code));
        }
        tokens.push_back(it->second);
    }
    return tokens;
}

static void usage(const char* prog) {
    cerr << "Usage:\n"
         << "  " << prog << " req1 <grammar.txt> <token1> <token2> ...\n"
         << "  " << prog << " req2 <grammar.txt> <prog_PIF.txt>\n";
}

int main(int argc, char** argv) {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    if (argc < 2) { usage(argv[0]); return 1; }
    string mode = argv[1];
    if (mode == "--help" || mode == "-h") { usage(argv[0]); return 0; }

    try {
        if (mode == "req1") {
            if (argc < 4) { usage(argv[0]); return 1; }
            string grammar_path = argv[2];

            vector<string> sequence;
            for (int i = 3; i < argc; i++) sequence.push_back(argv[i]);

            Grammar g = Grammar::from_file(grammar_path);
            auto first_sets = compute_first_sets(g);
            auto follow_sets = compute_follow_sets(g, first_sets);
            auto table = build_ll1_table(g, first_sets, follow_sets);

            auto prods = parse_sequence(g, table, sequence);
            cout << "Productions used:\n";
            for (const auto& pr : prods) {
                cout << pr.first << " -> ";
                for (size_t i = 0; i < pr.second.size(); i++) {
                    if (i) cout << ' ';
                    cout << pr.second[i];
                }
                cout << "\n";
            }
        } else if (mode == "req2") {
            if (argc < 4) { usage(argv[0]); return 1; }
            string grammar_path = argv[2];
            string pif_path = argv[3];

            Grammar g = Grammar::from_file(grammar_path);
            auto first_sets = compute_first_sets(g);
            auto follow_sets = compute_follow_sets(g, first_sets);
            auto table = build_ll1_table(g, first_sets, follow_sets);

            auto tokens = pif_to_tokens(pif_path);
            auto nodes = parse_with_tree(g, table, tokens);
            print_parse_tree(nodes);
        } else {
            usage(argv[0]);
            return 1;
        }
    } catch (const exception& e) {
        cerr << "Error: " << e.what() << "\n";
        return 2;
    }

    return 0;
}
