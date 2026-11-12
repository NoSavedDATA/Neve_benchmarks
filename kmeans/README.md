## Install Steps

Run a Docker to guarantee the GPU lib compatibility. Create a local folder first as the experiment volume path.

```bash
cd ~/
git clone https://github.com/NoSavedDATA/Neve_benchmarks.git
cd Neve_benchmarks/kmeans
docker build -t neve-kmeans .
docker run --rm --gpus all -v ~/Neve_benchmarks:/frost_exp/Neve_benchmarks -it neve-kmeans bash
```


Neve evaluation
```bash
neve kmeans_simd.nv
```

Neve GPU evaluation
```bash
neve kmeans_gpu.nv
```


Python evaluation
```bash
python eval_sklearn.py
```
