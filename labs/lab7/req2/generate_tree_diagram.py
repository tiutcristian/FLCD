import pandas as pd
import io
import matplotlib.pyplot as plt

data = """Idx   Symbol      Father      Sibling   
0     program           -1          -1        
1     statement_list  0           -1        
2     statement       1           3         
3     statement_list  1           -1        
4     assignment_stmt 2           -1        
5     ID              4           6         
6     ASSIGN          4           7         
7     STRING          4           -1        
8     statement       3           9         
9     statement_list  3           -1        
10    load_stmt       8           -1        
11    LOAD            10          12        
12    ID              10          -1        
13    statement       9           14        
14    statement_list  9           -1        
15    split_stmt      13          -1        
16    SPLIT           15          17        
17    BY              15          18        
18    STRING          15          -1        
19    statement       14          20        
20    statement_list  14          -1        
21    join_stmt       19          -1        
22    JOIN            21          23        
23    WITH            21          24        
24    STRING          21          -1        
25    statement       20          26        
26    statement_list  20          -1        
27    assignment_stmt 25          -1        
28    ID              27          29        
29    ASSIGN          27          30        
30    STRING          27          -1        
31    statement       26          32        
32    statement_list  26          -1        
33    save_stmt       31          -1        
34    SAVE            33          35        
35    ID              33          -1"""

# Parse
df = pd.read_csv(io.StringIO(data), sep='\s+')

# Build Tree Structure
children = {i: [] for i in df['Idx']}
labels = {row['Idx']: row['Symbol'] for _, row in df.iterrows()}
root = None

for _, row in df.iterrows():
    idx = row['Idx']
    father = row['Father']
    if father == -1:
        root = idx
    else:
        children[father].append(idx)

# Compute Layout
coords = {}
leaf_counter = 0

def get_coords(node, depth=0):
    global leaf_counter
    
    # Process children first (Post-Order) to determine X based on children
    child_nodes = children.get(node, [])
    
    if not child_nodes:
        # Leaf node
        x = leaf_counter
        leaf_counter += 1.5 # Spacing
    else:
        # Internal node
        child_xs = [get_coords(child, depth + 1) for child in child_nodes]
        x = sum(child_xs) / len(child_xs)
    
    coords[node] = (x, -depth) # Negative depth for top-down
    return x

get_coords(root)

# Plot
plt.figure(figsize=(14, 8))
ax = plt.gca()

# Draw Edges
for parent, kids in children.items():
    if parent in coords:
        px, py = coords[parent]
        for kid in kids:
            if kid in coords:
                kx, ky = coords[kid]
                plt.plot([px, kx], [py, ky], color='gray', zorder=1)

# Draw Nodes
for node, (x, y) in coords.items():
    lbl = labels[node]
    # Simple logic to shorten long labels if needed, or adjust box size
    # Check if it's a "terminal" (leafish) or non-terminal
    style = 'round,pad=0.3'
    fc = '#e0f7fa' # light cyan
    if not children[node]:
         fc = '#fff9c4' # light yellow for leaves
         
    plt.text(x, y, lbl, ha='center', va='center', 
             bbox=dict(boxstyle=style, facecolor=fc, edgecolor='gray'), 
             zorder=2, fontsize=9)

plt.axis('off')
plt.title("Syntax Tree Reconstruction")
plt.tight_layout()
plt.savefig('syntax_tree_mpl.png', dpi=150)