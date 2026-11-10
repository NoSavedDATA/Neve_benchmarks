## Benchmarks

This repository contains multiple bercharks separated by folder. Each folder has its readme and installation steps according to the tasks frameworks and system dependencies.

## Database datasets

The [datasets/](datasets/README.md) folder contains the SQLite benchmark for
Neve, Python, C++ and C. It runs 1,000 INSERTs, UPDATEs and DELETEs per batch,
plus six groups of 1,000 SELECT queries with WHERE predicates and INNER JOINs.
Each implementation consumes and validates the results. Both in-memory and
temporary file-backed databases are tested; no external dataset download is needed.

The folder has its own Dockerfile and interactive workflow, like [net/](net/README.md):

```bash
cd datasets
docker build --platform linux/amd64 -t neve_datasets .
docker run --rm -it -v "$(pwd)/resultados:/results" neve_datasets bash
```

Inside the container, run `python3 run.py` or use the quick validation command
`python3 run.py --repetitions 1 --warmups 0`. No GPU is required.
See the folder README for dependencies, methodology and reference results.

---
## Syntax Highlight

Want to inspect the code (neve_samples/all_in_one.nv)? You could either tell your IDE to use Python highlight for .nv,
or install a highlight plugin for either Vim or VSCode

#### vim

For vim, intall plugins 'NosavedDATA/vim-neve' and 'NosavedDATA/vim-neve-dark'.

Then use set 'colorscheme ghdark' in the config file.


#### vscode

For vscode, install the syntax extension.
```
wget https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/neve-syntax.vsix
code --install-extension neve-syntax.vsix
```
---
