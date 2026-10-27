#!/usr/bin/env python3
"""DIMACS CNF for: does a DISJOINT fresh schedule of order K and length T exist?
(B_j = [K] \\ A_j for every step; rows and columns carry the same labels.)

Variables a[j][x] (x in A_j) and n[j][x][y] (N_j(x) = y).  B_j is the complement of A_j.
Clauses
  |A_j| = K/2                                  (Sinz sequential counters)
  n[j][x][y] -> a[j][x] and ~a[j][y]
  a[j][x]  -> exactly one y with n[j][x][y];  ~a[j][y] -> exactly one x with n[j][x][y]
  freshness: ~n[j][x][y] v ~a[i][x] v a[i][y]       for i < j
Symmetry breaking (relabelling acts diagonally): A_1 = {0..K/2-1}, N_1(x) = x + K/2.

usage: gen_cnf_d.py K T [out.cnf]      -> writes out.cnf and out.cnf.map
"""
import sys, json

K = int(sys.argv[1]); T = int(sys.argv[2])
out = sys.argv[3] if len(sys.argv) > 3 else "d%dt%d.cnf" % (K, T)
H = K // 2
nv = 0
def new():
    global nv; nv += 1; return nv
a = [[new() for _ in range(K)] for _ in range(T)]
n = [[[new() for _ in range(K)] for _ in range(K)] for _ in range(T)]
cls = []

def atmost(lits, k):
    m = len(lits)
    if k >= m: return
    if k == 0:
        for l in lits: cls.append([-l])
        return
    s = [[new() for _ in range(k)] for _ in range(m)]
    cls.append([-lits[0], s[0][0]])
    for j in range(1, k): cls.append([-s[0][j]])
    for i in range(1, m):
        cls.append([-lits[i], s[i][0]]); cls.append([-s[i-1][0], s[i][0]])
        for j in range(1, k):
            cls.append([-lits[i], -s[i-1][j-1], s[i][j]]); cls.append([-s[i-1][j], s[i][j]])
        cls.append([-lits[i], -s[i-1][k-1]])

for j in range(T):
    atmost(a[j], H); atmost([-l for l in a[j]], K - H)
    for x in range(K):
        for y in range(K):
            if x == y: cls.append([-n[j][x][y]]); continue
            cls.append([-n[j][x][y], a[j][x]]); cls.append([-n[j][x][y], -a[j][y]])
        cls.append([-a[j][x]] + [n[j][x][y] for y in range(K) if y != x])
        for y in range(K):
            for y2 in range(y + 1, K):
                cls.append([-n[j][x][y], -n[j][x][y2]])
    for y in range(K):
        cls.append([a[j][y]] + [n[j][x][y] for x in range(K) if x != y])
        for x in range(K):
            for x2 in range(x + 1, K):
                cls.append([-n[j][x][y], -n[j][x2][y]])
    for i in range(j):
        for x in range(K):
            for y in range(K):
                if x != y: cls.append([-n[j][x][y], -a[i][x], a[i][y]])
for x in range(K):
    cls.append([a[0][x]] if x < H else [-a[0][x]])
for x in range(H):
    cls.append([n[0][x][x + H]])

with open(out, "w") as f:
    f.write("p cnf %d %d\n" % (nv, len(cls)))
    f.write("".join(" ".join(map(str, c)) + " 0\n" for c in cls))
with open(out + ".map", "w") as f:
    json.dump({"K": K, "T": T, "a": a, "b": [[-v for v in row] for row in a], "n": n, "disjoint": True}, f)
print("K=%d T=%d (disjoint) vars=%d clauses=%d -> %s" % (K, T, nv, len(cls), out))
