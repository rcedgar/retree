#!/usr/bin/python3

from newicktree import Tree, TreeNode
import argparse

Usage = \
(
"Calculate Robinson-Foulds distance between two trees.\n"
"See https://en.wikipedia.org/wiki/Robinson%E2%80%93Foulds_metric"
)

ap = argparse.ArgumentParser(description = Usage)
ap.add_argument("filename1", help="first tree in Newick format")
ap.add_argument("filename2", help="second tree in Newick format")
args = ap.parse_args()

with open(args.filename1, "r", encoding="utf-8") as f:
    data1 = f.read()
with open(args.filename2, "r", encoding="utf-8") as f:
    data2 = f.read()

tree1 = Tree()
tree2 = Tree()
tree1.from_data(data1)
tree2.from_data(data2)

def get_subtree_leaf_set(tree, idx):
    subtree_leaf_set = set()
    node = tree.get_node_by_idx(idx)
    if node.child_idxs is None:
        return subtree_leaf_set
    n = len(node.child_idxs)
    if n == 0:
        subtree_leaf_set.add(node.label)
    else:
        for child_idx in node.child_idxs:
            subtree_leaf_set |= get_subtree_leaf_set(tree, child_idx)
    return subtree_leaf_set

def get_partitions(tree):
    partitions = set()
    for idx in tree.idxs:
        leaf_set = get_subtree_leaf_set(tree, idx)
        frozen_leaf_set = frozenset(leaf_set)
        partitions.add(frozen_leaf_set)
    return partitions

parts1 = get_partitions(tree1)
parts2 = get_partitions(tree2)

n_in1_notin2 = 0
n_in2_notin1 = 0
for part in parts1:
    if not part in parts2:
        n_in1_notin2 += 1

for part in parts2:
    if not part in parts1:
        n_in2_notin1 += 1

rf = n_in1_notin2 + n_in2_notin1
rf_normalized = (n_in1_notin2 + n_in2_notin1)/(len(parts1) + len(parts2))

print(f"tree1 {args.filename1}")
print(f"tree2 {args.filename2}")

print(f"{len(parts1)} subtrees in 1")
print(f"{len(parts2)} subtrees in 2")

print(f"{n_in1_notin2} subtrees in 1 not in 2")
print(f"{n_in2_notin1} subtrees in 2 not in 1")

print(f"R-F metric distance = {rf}")
print(f"Normalized distance (range 0 to 1) = {rf_normalized:6.4}")

