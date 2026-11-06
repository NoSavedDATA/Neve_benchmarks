```bash
cd ~/
docker build -t neve_sockets .
docker run --name neve --gpus all --network host -v ~/Neve_benchmarks:/frost_exp/Neve_benchmarks -v ~/:/my_home -it neve_sockets bash
```
