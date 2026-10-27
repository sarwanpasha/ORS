#!/usr/bin/env python3
"""DIMACS CNF for: does a fresh schedule of order K and length T exist?

Fresh schedule (paper Def. 4): (A_j,B_j,N_j)_{j=1..T} with A_j,B_j subseteq [K],
|A_j|=|B_j|=K/2, N_j : A_j -> B_j a bijection, and for every j and x in A_j there
is no i<j with x in A_i and N_j(x) in B_i.

Variables
  a[j][x], b[j][y], n[j][x][y]
Clauses
  |A_j| = |B_j| = K/2                       (Sinz sequential at-most-k, twice)
  n -> a, n -> b
  a[j][x] -> exactly one y with n[j][x][y]
  b[j][y] -> exactly one x with n[j][x][y]
  freshness: ~n[j][x][y] v ~a[i][x] v ~b[i][y]     for i < j
Symmetry breaking (WLOG under relabelling rows/columns):
  A_1 = B_1 = {0..K/2-1}, N_1 = identity
Emits a var map so a model can be decoded and re-verified independently.
"""
import sys, json

# usage: gen_cnf.py K T [out.cnf] [a b1 b2 b3]
# The optional 4-tuple fixes step 2 to a canonical representative of its orbit
# under the stabiliser of the fixed step 1.  Ranging over all valid tuples is an
# exhaustive, sound case split (cube-and-conquer): the instance is satisfiable
# iff some cube is.
K = int(sys.argv[1]); T = int(sys.argv[2])
out = sys.argv[3] if len(sys.argv) > 3 else "k%dt%d.cnf" % (K, T)
cube = tuple(int(v) for v in sys.argv[4:8]) if len(sys.argv) > 7 else None
a3   = int(sys.argv[8]) if len(sys.argv) > 8 else None   # optional bitmask fixing A_3
a4   = int(sys.argv[9]) if len(sys.argv) > 9 else None   # optional bitmask fixing A_4
H = K // 2
nv = 0
def new():
    global nv; nv += 1; return nv

a = [[new() for _ in range(K)] for _ in range(T)]
b = [[new() for _ in range(K)] for _ in range(T)]
n = [[[new() for _ in range(K)] for _ in range(K)] for _ in range(T)]
cls = []

def atmost(lits, k):
    """Sinz sequential counter: sum(lits) <= k."""
    m = len(lits)
    if k >= m: return
    if k == 0:
        for l in lits: cls.append([-l])
        return
    s = [[new() for _ in range(k)] for _ in range(m)]
    cls.append([-lits[0], s[0][0]])
    for j in range(1, k): cls.append([-s[0][j]])
    for i in range(1, m):
        cls.append([-lits[i], s[i][0]])
        cls.append([-s[i-1][0], s[i][0]])
        for j in range(1, k):
            cls.append([-lits[i], -s[i-1][j-1], s[i][j]])
            cls.append([-s[i-1][j], s[i][j]])
        cls.append([-lits[i], -s[i-1][k-1]])

def exactly(lits, k):
    atmost(lits, k)
    atmost([-l for l in lits], len(lits) - k)

for j in range(T):
    exactly(a[j], H)
    exactly(b[j], H)
    for x in range(K):
        for y in range(K):
            cls.append([-n[j][x][y], a[j][x]])
            cls.append([-n[j][x][y], b[j][y]])
        cls.append([-a[j][x]] + [n[j][x][y] for y in range(K)])
        for y in range(K):
            for y2 in range(y + 1, K):
                cls.append([-n[j][x][y], -n[j][x][y2]])
    for y in range(K):
        cls.append([-b[j][y]] + [n[j][x][y] for x in range(K)])
        for x in range(K):
            for x2 in range(x + 1, K):
                cls.append([-n[j][x][y], -n[j][x2][y]])
    for i in range(j):
        for x in range(K):
            for y in range(K):
                cls.append([-n[j][x][y], -a[i][x], -b[i][y]])

for x in range(H):
    cls.append([a[0][x]]); cls.append([b[0][x]]); cls.append([n[0][x][x]])
for x in range(H, K):
    cls.append([-a[0][x]]); cls.append([-b[0][x]])

# Stabiliser of step 1 in S_K x S_K: sigma preserves P={0..H-1} and P^c, tau
# preserves P and P^c, with tau|_P = sigma|_P.  So A_2 is determined up to
# symmetry by av = |A_2 & P|, and then B_2 by the counts b1 = |B_2 & [0,av)|,
# b2 = |B_2 & [av,H)|, b3 = |B_2 & [H,K)|.  Ranging over every valid tuple is an
# exhaustive, sound case split: the instance is SAT iff some cube is SAT.
if cube is not None and T > 1:
    av, b1, b2, b3 = cube
    assert b1 <= av and b2 <= H - av and b3 <= H and b1 + b2 + b3 == H
    A2 = set(range(av)) | set(range(H, H + (H - av)))
    B2 = set(range(b1)) | set(range(av, av + b2)) | set(range(H, H + b3))
    for x in range(K):
        cls.append([a[1][x]] if x in A2 else [-a[1][x]])
        cls.append([b[1][x]] if x in B2 else [-b[1][x]])

# Optional second-level split: fix A_3 to an explicit set.  Ranging over all
# K/2-subsets is an exhaustive case split (every schedule has some A_3), sound
# with no symmetry argument at all -- it just makes each subproblem far easier.
if a3 is not None and T > 2:
    for x in range(K):
        cls.append([a[2][x]] if (a3 >> x) & 1 else [-a[2][x]])
if a4 is not None and T > 3:
    for x in range(K):
        cls.append([a[3][x]] if (a4 >> x) & 1 else [-a[3][x]])

with open(out, "w") as f:
    f.write("p cnf %d %d\n" % (nv, len(cls)))
    f.write("".join(" ".join(map(str, c)) + " 0\n" for c in cls))
with open(out + ".map", "w") as f:
    json.dump({"K": K, "T": T, "a": a, "b": b, "n": n}, f)
print("K=%d T=%d vars=%d clauses=%d -> %s" % (K, T, nv, len(cls), out))
