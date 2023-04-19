# Matrix Graph Generator

Instead of proving a matrix wasn't reachable with only row operations the smart way, I just made this script to generate ALL reachable matrices.

## Usage

Run `python matrix_graph_gen.py --help` for usage info.

Matrices can be provided in any of the following forms:

- Pythonic
```python
[[1,2,3],[4,5,6],[7,8,9]]
```
- Lazy Pythonic
```python
[1,2,0][2,0,1][1,1,1]
```
- Latex
```latex
1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1
```

Just remember: you're entering these on the command line, so you probably need to wrap these in "quotes" to have them load properly.

## Analysis
From experience, the graphs this script generates are far too large for Plantuml or Graphviz to handle directly.

I have found the most success using [Gephi](https://gephi.org/) to analyze the dot file output.