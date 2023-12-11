"""Newick trees.

Provides two classes: TreeNode and Tree.

Usage:
  str = "(A,(B,C));"
  tree = NewickTree(str)

  with open("example.tree") as f:
    data = f.read()
  tree = NewickTree(data)
"""

import sys
from dataclasses import dataclass
from newicklexer import NewickLexer, NewickToken, NewickTokenType
from newickstrings import newick_strs

@dataclass
class TreeNode():
    """Newick tree node.

    idx
        Non-negative integer index which uniquely identifies the node.
        Indexes are used as dictionary keys in Tree and may be sparse, e.g.
          when tree nodes are deleted.

    parent_idx
        Parent index. Must be None for exactly one node (the root).

    label
        Name of node, or None if there is no label.

    child_idxs
        List of child node idx's.

    Unrooted trees are represented by assigning an arbitrary node
      to be the (pseudo-) root (https://en.wikipedia.org/wiki/Newick_format),
      thus **Newick does not distinguish rooted from unrooted**.
    """

    idx: int
    parent_idx: int
    child_idxs: list
    label: str
    edge_length: float  # length of edge from this node to its parent

class Tree():
    """Newick tree.

    Following properties are those relevant for most users.

    nodes
        Dictionary with key=idx, value=TreeNode.

    labels
        Set of label names.

    label_to_idx
        Dictionary key=label, value=idx.

    idxs
        Set of idx's.

    root
        idx of root, or pseudo-root if tree is unrooted (root is never None).

    Typical usage:
      str = "(A,(B,C));"
      lexer = NewickLexer(str)
      tokens = lexer.get_tokens()
      tree = NewickTree()
      tree.from_tokens(tokens)
    """

    nodes: dict  # key is TreeNode.idx, value is TreeNode

    def __init__(self):
        self.nodes = {}
        self.labels = set()
        self.label_to_idx = {}
        self.idxs = set()
        self.next_idx = 0
        self.root = None
        self.rooted = True  # False if root is psuedo

    def assign_new_idx(self):
        idx = self.next_idx
        self.next_idx += 1
        assert not idx in self.idxs
        return idx

    def insert_node(self,
                    label,
                    parent_idx,
                    child_idxs,
                    edge_length):
        if not parent_idx is None:
            assert parent_idx in self.idxs
        for child_idx in child_idxs:
            assert child_idx in self.idxs
        if not label is None:
            if label in self.labels:
                sys.stderr.write(f"\nError: duplicate label '{label}'\n")
                assert False
        idx = self.assign_new_idx()
        if not label is None:
            self.label_to_idx[label] = idx
        node = TreeNode(idx, parent_idx, child_idxs, label, edge_length)
        self.labels.add(label)
        self.nodes[idx] = node
        self.idxs.add(idx)
        return idx

    def pretty_print(self):
        s = "  idx"
        s += "  parent"
        s += "  %8.8s" % "length"
        s += "  children"
        print(s)
        for idx in range(self.next_idx):
            if not idx in self.nodes:
                continue
            node = self.nodes[idx]
            s = f"{idx:5}"
            if node.parent_idx is None:
                s += "        "
            else:
                s += f"  {node.parent_idx:6}"
            if node.edge_length is None:
                s += "  %8.8s" % "-"
            else:
                s += "  %8.8s" % node.edge_length
            child_count = 0
            if node.child_idxs is not None:
                t = ""
                child_count = len(node.child_idxs)
                for child_idx in node.child_idxs:
                    if t == "":
                        t = " "
                    else:
                        t += ","
                    t += " %d" % child_idx
                s += t
            if child_count == 0:
                s += "  -"
            if node.parent_idx is None:
                s += " (ROOT)"
            print(s)

    def validate_node(self, node):
        assert node.idx in self.nodes
        if not node.child_idxs is None:
            for idx in node.child_idxs:
                assert idx in self.nodes
        if not node.label is None:
            assert node.label in self.labels
        if not node.parent_idx is None:
            parent_node = self.get_node_by_idx(node.parent_idx)
            parent_child_idxs = parent_node.child_idxs
            assert node.idx in parent_child_idxs

    def validate(self):
        for idx in range(self.next_idx):
            if not idx in self.nodes:
                continue
            node = self.nodes[idx]
            self.validate_node(node)
        # print("validated ok")

    def get_node_by_idx(self, idx):
        return self.nodes[idx]

    def get_idx_by_label(self, label):
        idx = self.label_to_idx[label]
        return idx

    def connect(self, parent_idx, child_idx):
        parent_node = self.get_node_by_idx(parent_idx)
        child_node = self.get_node_by_idx(child_idx)
        assert ((child_node.parent_idx == child_node.parent_idx) or
                (child_node.parent_idx is None))
        assert not child_node.idx in parent_node.child_idxs
        child_node.parent_idx = parent_idx
        parent_node.child_idxs.append(child_idx)

    def get_pending_token(self):
        if self.next_token_index == len(self.tokens):
            return self.eof_token
        return self.tokens[self.next_token_index]

    def get_next_token(self, end_of_file_ok=True):
        if self.next_token_index == len(self.tokens):
            if end_of_file_ok:
                return self.eof_token
            sys.stderr.write("\ntree.get_next_token() end-of-file")
            assert False
        next_token = self.tokens[self.next_token_index]
        self.next_token_index += 1
        return next_token

    def get_label(self):
        pending_token = self.get_pending_token()
        if pending_token.toktype == NewickTokenType.LABEL:
            self.next_token_index += 1
            return pending_token.tokstr
        elif pending_token.toktype == NewickTokenType.COMMA:
            return ""
        else:
            return None

    def get_edge_length(self):
        pending_token = self.get_pending_token()
        if pending_token.toktype == NewickTokenType.COLON:
            self.next_token_index += 1
            token = self.get_next_token()
            assert token.toktype == NewickTokenType.FLOAT
            return token.tokstr
        else:
            return None

    def get_label_and_length(self):
        label = self.get_label()
        edge_length = self.get_edge_length()
        return label, edge_length

    def dotrace(self, msg):
        try:
            if self.trace:
                print(msg)
        # ensure that exceptions not thrown from inside tracing
        # pylint: disable=bare-except
        except:
            sys.stderr.write(
                "\nWarning: tree.dotrace(), self.trace undefined\n")
        return

    def from_lists(self, label_list, parent_idx_list,
                   edge_length_list, trace=False):
        n = len(label_list)
        assert len(parent_idx_list) == n
        assert len(edge_length_list) == n
        idxs = []
        for i in range(n):
            label = label_list[i]
            edge_length = edge_length_list[i]
            parent_idx = parent_idx_list[i]
            child_idxs = []
            if trace:
                msg = f"insert_node(label={label}"
                if parent_idx is None:
                    msg += " <ROOT>"
                else:
                    msg += f" parent_idx={parent_idx}"
                print(msg)
            idx = self.insert_node(label, parent_idx, child_idxs, edge_length)
            idxs.append(idx)

        for i in range(n):
            idx = idxs[i]
            parent_idx = parent_idx_list[i]
            if parent_idx is None:
                assert self.root is None
                self.root = idx
            else:
                self.connect(parent_idx, idx)

    def trace_lists(self, label_list, parent_idx_list, edge_length_list):
        n = len(label_list)
        assert len(parent_idx_list) == n
        assert len(edge_length_list) == n
        for i in range(n):
            label = label_list[i]
            parent_idx = parent_idx_list[i]
            edge_length = edge_length_list[i]
            msg = f"{i:5}"
            if label is None:
                label = "."
            msg += f"  {label:8}"
            if parent_idx is None:
                msg += "<ROOT>"
            else:
                msg += f"  {parent_idx:5}"
            if not edge_length is None:
                msg += " -> " + edge_length
            print(msg)

    def from_data(self, data, trace=False):
        lexer = NewickLexer(data)
        tokens = lexer.get_tokens()
        self.from_tokens(tokens, trace)

    def from_tokens(self, tokens, trace=False):
        self.tokens = tokens
        self.next_token_index = 0
        self.eof_token = NewickToken()
        self.eof_token.toktype = NewickTokenType.EOF
        self.trace = trace

        # Track nesting in a stack to avoid deep recursion for large trees,
        #   I don't know how stack limits/overflow is handled in Python...
        #   search for "stack overflow python" goes to stackoverflow.com :-(
        stack = []
        stack.append(None)
        label = None
        edge_length = None

        # variable name e.g. labels_list to emphasize local
        #   in from_tokens() rather than object property self.labels.
        label_list = []
        parent_idx_list = []
        edge_length_list = []

        while True:
            token = self.get_next_token()
            depth = len(stack)
            self.dotrace(
                f"while {self.next_token_index}/{len(tokens)}"
                " depth={depth} {token}")

            if token.toktype == NewickTokenType.SEMICOLON:
                if depth != 1 or self.next_token_index != len(tokens):
                    # TODO: improve error-handling, decide on return code/exception throwing
                    sys.stderr.write("Unexpected semi-colon in Newick data\n")
                    assert False
                break

            elif token.toktype == NewickTokenType.LPAREN:
                assert len(stack) > 0
                parent_idx = stack[-1]
                group_index = len(label_list)
                stack.append(group_index)
                label_list.append(None)
                edge_length_list.append(None)
                parent_idx_list.append(parent_idx)

            elif token.toktype == NewickTokenType.RPAREN:
                if self.next_token_index-2 >= 0:
                    prev_token = self.tokens[self.next_token_index-2]
                    if prev_token.toktype == NewickTokenType.COMMA:
                        assert len(stack) > 0
                        parent_idx = stack[-1]
                        label = None
                        edge_length = None
                        label_list.append(label)
                        edge_length_list.append(edge_length)
                        parent_idx_list.append(parent_idx)
                assert len(stack) > 0
                group_index = stack.pop()
                label, edge_length = self.get_label_and_length()
                label_list[group_index] = label
                edge_length_list[group_index] = edge_length

            elif token.toktype == NewickTokenType.COMMA:
                if self.next_token_index-2 >= 0:
                    prev_token = self.tokens[self.next_token_index-2]
                    if (prev_token.toktype == NewickTokenType.COMMA or
                            prev_token.toktype == NewickTokenType.LPAREN):
                        assert len(stack) > 0
                        parent_idx = stack[-1]
                        label = None
                        edge_length = None
                        label_list.append(label)
                        edge_length_list.append(edge_length)
                        parent_idx_list.append(parent_idx)

            elif token.toktype == NewickTokenType.COLON:
                assert len(stack) > 0
                parent_idx = stack[-1]
                next_token = self.get_next_token()
                if next_token.toktype != NewickTokenType.FLOAT:
                    # TODO: improve error-handling, decide on return code/exception throwing
                    sys.stderr.write(
                        f"Expected edge length after colon, got"
                        " '{token.tokstr}'\n")
                    assert False
                try:
                    edge_length = next_token.tokstr
                    _ = float(edge_length)
                # TODO: better error handing style
                # pylint: disable=bare-except
                except:
                    sys.stderr.write(
                        # TODO: improve error-handling, decide on return code/exception throwing
                        f"Invalid edge length '{next_token.tokstr}'\n")
                    assert False

                label_list.append(None)
                parent_idx_list.append(parent_idx)
                edge_length_list.append(edge_length)

            elif token.toktype == NewickTokenType.LABEL:
                assert len(stack) > 0
                parent_idx = stack[-1]
                label = token.tokstr
                edge_length = self.get_edge_length()
                label_list.append(label)
                edge_length_list.append(edge_length)
                parent_idx_list.append(parent_idx)

            else:
                # TODO: improve error-handling, decide on return code/exception throwing
                sys.stderr.write(f"Unexpected token {token}'\n")
                assert False

        if trace:
            self.trace_lists(label_list, parent_idx_list, edge_length_list)

        self.from_lists(label_list, parent_idx_list, edge_length_list, trace)
        self.validate()

    def node_to_str(self, idx):
        node = self.nodes[idx]
        label = node.label
        if label is None:
            label = ""
        if node.child_idxs is None or len(node.child_idxs) == 0:
            s = label
        else:
            s = "("
            n = len(node.child_idxs)
            for i in range(n):
                child_idx = node.child_idxs[i]
                s += self.node_to_str(child_idx)
                if i + 1 < n:
                    s += ","
            s += ")"
            s += label
        edge_length = node.edge_length
        if not edge_length is None:
            s += ":" + edge_length
        return s
    
    def node_count(self):
        return len(self.idxs)

    def leaf_count(self):
        n = 0
        for idx in self.nodes:
            node = self.nodes[idx]
            child_idxs = node.child_idxs
            # TODO: learn more about boolean conversions, 
            #   can simplify this condition?
            if child_idxs is None or len(child_idxs) == 0:
                n += 1
        return n

    def non_binary_internal_node_count(self):
        n = 0
        for idx in self.nodes:
            node = self.nodes[idx]
            child_idxs = node.child_idxs
            # TODO: learn more about boolean conversions, 
            #   can simplify this condition?
            if child_idxs is not None:
                k = len(child_idxs)
                if k != 0 and k != 2:
                    n += 1
        return n

    def binary_internal_node_count(self):
        n = 0
        for idx in self.nodes:
            node = self.nodes[idx]
            child_idxs = node.child_idxs
            # TODO: learn more about boolean conversions, 
            #   can simplify this condition?
            if child_idxs is not None and len(child_idxs) == 2:
                n += 1
        return n

    def __str__(self):
        assert not self.root is None
        s = self.node_to_str(self.root)
        s += ";"
        return s

if __name__ == '__main__':
    simple_test = False
    if simple_test:
        tree = Tree()
        for node_label in ["root", "A", "B", "C"]:
            tree.insert_node(label=node_label,
                             parent_idx=None,
                             child_idxs=[],
                             edge_length=None)

        root_idx = tree.get_idx_by_label("root")
        a_idx = tree.get_idx_by_label("A")
        b_idx = tree.get_idx_by_label("B")
        c_idx = tree.get_idx_by_label("C")

        tree.connect(root_idx, a_idx)
        tree.connect(root_idx, b_idx)
        tree.connect(root_idx, c_idx)
        tree.validate()
        tree.pretty_print()

    def test(newick_str, trace=False):
        if trace:
            print("\n\n_________________________\nnewick_str =", newick_str)
        lexer = NewickLexer(newick_str)
        tokens = lexer.get_tokens()
        tree2 = Tree()
        tree2.from_tokens(tokens, trace)
        if trace:
            tree2.pretty_print()
        return tree2

    same_count = 0
    diff_count = 0
    trace_tests = False
    for test_newick_str in newick_strs:
        tree = test(test_newick_str, trace=trace_tests)
        test_newick_str = test_newick_str.replace(" ", "")
        print(tree)
        if str(tree) == test_newick_str:
            same_count += 1
        else:
            diff_count += 1
    print("same", same_count, "diff", diff_count)
    if diff_count == 0:
        print("Test PASSED")
    else:
        print("Test FAILED")
