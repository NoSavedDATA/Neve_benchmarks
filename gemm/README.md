The Python and OpenBLAS scripts assessed failed to select the correct GEMM CPU architecture inside Docker containers. Thus, they have been evaluated directly in Arch.

To install Neve
```
wget -qO- https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh | bash
```

Run with

```
neve gemm.nv
```

For Python, install NumPy and run

```
python np_mma.py
```


For OpenBLAS, install
```
sudo apt install libopenblas-dev
```
or
```
sudo pacman -S openblas
```
And run
```
clang++ -std=c++17 blas_mma.cpp -o main -lopenblas -lpthread
./main
```

You may adapt the matrix sizes inside the scripts, the default is M=N=P=4096
