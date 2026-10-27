#!/usr/bin/env python3
"""Decode a kissat model against a .cnf.map and INDEPENDENTLY re-verify the
schedule directly from Definition 4 (no reuse of the encoding's own logic).

usage: decode.py file.cnf.map model.txt
"""
import sys, json, re

m = json.load(open(sys.argv[1]))
K, T, A, B, N = m["K"], m["T"], m["a"], m["b"], m["n"]
txt = open(sys.argv[2]).read()
if "UNSATISFIABLE" in txt:
    print("UNSATISFIABLE"); sys.exit(0)
val = {}
for tok in re.findall(r"^v (.*)$", txt, re.M):
    for w in tok.split():
        v = int(w)
        if v: val[abs(v)] = v > 0

def lit(v):   # a negative id in the map means "negation of that variable" (used by gen_cnf_d.py)
    return bool(val.get(v)) if v > 0 else not val.get(-v, False)
Aj = [sorted(x for x in range(K) if lit(A[j][x])) for j in range(T)]
Bj = [sorted(y for y in range(K) if lit(B[j][y])) for j in range(T)]
Nj = [{x: y for x in range(K) for y in range(K) if lit(N[j][x][y])} for j in range(T)]

ok = True
for j in range(T):
    if len(Aj[j]) != K // 2 or len(Bj[j]) != K // 2:
        print("step %d: |A|=%d |B|=%d (want %d)" % (j + 1, len(Aj[j]), len(Bj[j]), K // 2)); ok = False
    if sorted(Nj[j].keys()) != Aj[j] or sorted(Nj[j].values()) != Bj[j]:
        print("step %d: N is not a bijection A->B" % (j + 1)); ok = False
    for x, y in Nj[j].items():
        for i in range(j):
            if x in Aj[i] and y in Bj[i]:
                print("step %d: pair (%d,%d) not fresh, co-covered at step %d" % (j + 1, x, y, i + 1)); ok = False

print("K=%d T=%d VERIFIED=%s" % (K, T, ok))
for j in range(T):
    print("step %2d: A=%-28s B=%-28s N=%s" % (j + 1, Aj[j], Bj[j],
          " ".join("%d->%d" % (x, Nj[j][x]) for x in Aj[j])))
