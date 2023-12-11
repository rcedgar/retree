## retree

Newick tree format parser and [Robinson-Foulds metric](https://en.wikipedia.org/wiki/Robinson%E2%80%93Foulds_metric) calculator, implemented as Python learning exercise.

### Newick format

See [Wikipedia article on Newick format](https://en.wikipedia.org/wiki/Newick_format). This format is notoriously difficult to parse because of varying implementations and because labels and/or branch lengths may be omitted for any node, e.g. `(,(,));` is a valid tree specification with the same topology as `(A,(,));`, `(,(,))A;`, `(A,(B,C));`, `(A:0.1,(B:0.2,C:0.3));` and so on.

### Python language and style
The code exercises modules, classes, `@dataclass` decorator, docstrings, f-string formatting, type hints, default arguments, `Enum`, the `argparse` module.

The module code passes `pylint` with no warnings, using the Google `pylint.rc` file (downloaded from [here](https://google.github.io/styleguide/pylintrc) and included in the repo).

### newick_dump.py
<pre>
Usage:
  newick_dump.py [-h] [--short] [filename]

Description:
  Show human-readable summary of Tree object from Newick input file on stdout.

positional arguments:
  filename    tree filename in Newick format

optional arguments:
  -h, --help  show this help message and exit
  --short     show short summary only

</pre>

### robinson_foulds.py
<pre>
Usage:
  robinson_foulds.py [-h] filename1 filename2

  Calculate Robinson-Foulds distance between two trees. See
  https://en.wikipedia.org/wiki/Robinson%E2%80%93Foulds_metric

positional arguments:
  filename1   first tree in Newick format
  filename2   second tree in Newick format

optional arguments:
  -h, --help  show this help message and exit
</pre>

### Unit tests
The `newicklexer.py` and `newicktree.py` modules run self-tests if run as the main script. These tests use a list of valid Newick strings found in the `newickstrings.py` module.

The `trees/` directory has some example tree files, `example1.tree` is similar to `example2.tree` (ditto `example[34].tree`).

<pre>
# example usage
py/robinson_foulds.py trees/example3.tree trees/example4.tree
tree1 ../trees/example3.tree
tree2 ../trees/example4.tree
148 subtrees in 1
148 subtrees in 2
34 subtrees in 1 not in 2
34 subtrees in 2 not in 1
R-F metric distance = 68
Normalized distance (range 0 to 1) = 0.2297
</pre>

