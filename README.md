## Benchmarks

This repository contains multiple bercharks separated by folder. Each folder has its readme and installation steps according to the tasks frameworks and system dependencies.

#### Folders & Experiments:

- datasets: interop SQLite interface for database operations.
- esp: embedded system ESP32-S3 computation.
- gemm: CPU tensor matrix multiplication.
- kmeans: kmeans in HAR dataset.
- net: sockets networking.
- resnet_cifar: Frost deep learning framework.

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
