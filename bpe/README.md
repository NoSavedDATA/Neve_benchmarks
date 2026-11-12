## Install Steps

This one downloads Openwebtext from huggingface, so it is quite slow to build.


```bash
cd ~/
git clone https://github.com/NoSavedDATA/Neve_benchmarks.git
cd Neve_benchmarks/bpe
docker build -t neve-bpe .
docker run --rm --gpus all -v ~/Neve_benchmarks:/frost_exp/Neve_benchmarks -it neve-bpe bash
```


Neve evaluation
```bash
time neve bpe.nv
```


Python evaluation
```bash
time python bpe.py
time python bpe_8_threads.py
```
