#!/usr/bin/python3

from newicktree import Tree
import argparse

Usage = \
(
"Dump summary of Tree object from Newick input file"
)

ap = argparse.ArgumentParser(description = Usage)
ap.add_argument("filename", nargs="?", help="tree filename in Newick format")
ap.add_argument("--short", action='store_true', help="show short summary only")
args = ap.parse_args()
with open(args.filename, "r", encoding="utf-8") as f:
    data = f.read()

tree = Tree()
tree.from_data(data)
if not args.short:
    tree.pretty_print()
nleaf = tree.leaf_count()
nbinary = tree.binary_internal_node_count()
nnonbinary = tree.non_binary_internal_node_count()
nnode = tree.node_count()
s = f"{args.filename}"
s += f"{nnode} nodes, {nleaf} leaves,"
s += f" {nbinary} binary nodes, {nnonbinary}"
s += f" non-binary internal nodes"
print(s)