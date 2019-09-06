# ResourceMeasure

## How to install

```
$ sudo apt install graphviz
$ pip install -r requirements.txt
```


## How to use

```
python ResourceMeasure.py
gprof2dot -f pstats measure_result/profile.prof | dot -Gdpi=300 -Tjpg -o profile.jpg
```
