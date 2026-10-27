#!/usr/bin/env python3
"""Schedules: parse, verify (Definition 4), and the product / doubling constructions.

A schedule of order K is a list of steps (A, B, N): A, B are K/2-subsets of {0..K-1} and N is a
bijection A -> B such that for every step j and every x in A_j there is no earlier step i < j
with x in A_i and N_j(x) in B_i.  It is *disjoint* if additionally B_j = [K] \\ A_j for all j.

Product lemma.  If S is a schedule of order K and length t, and D is a disjoint schedule of
order K' and length d, then the following is a schedule of order K*K' and length t + d on the
ground set [K] x [K'] (pair (x, y) is encoded as x*K' + y):
  first,  for each step (A', B', N') of D:  rows [K] x A', columns [K] x B', (x,y) -> (x, N'(y));
  then,   for each step (A, B, N) of S:     rows A x [K'], columns B x [K'], (x,y) -> (N(x), y).
Freshness among the D-lifted steps and among the S-lifted steps is inherited from D and S; an
S-lifted pair (x,y) -> (N(x),y) lies in an earlier rectangle ([K] x A') x ([K] x B') only if
y is in both A' and B', impossible because D is disjoint.  Hence t(K*K') >= t(K) + d(K').
Doubling (t(2K) >= t(K) + 2) is the case K' = 2 with the disjoint schedule {0}->{1}, {1}->{0}.

usage:
  python3 src/constructions.py verify FILE                 # FILE = output of ./sym or decode.py
  python3 src/constructions.py product T_FILE D_FILE       # lift and verify
  python3 src/constructions.py double  T_FILE [times]
"""
import re, sys

def parse(path):
    """Read the last schedule printed in FILE (formats of ./sym and src/decode.py)."""
    txt = open(path).read()
    blocks = re.split(r"(?m)^(?:FOUND |K=\d+ T=\d+ VERIFIED)", txt)
    body = blocks[-1]
    steps = []
    for line in body.splitlines():
        m = re.search(r"A=([\d,]*) B=([\d,]*) N=([\d>,]*)", line)           # ./sym format
        if m:
            A = [int(v) for v in m.group(1).split(",") if v]
            B = [int(v) for v in m.group(2).split(",") if v]
            N = dict(tuple(map(int, p.split(">"))) for p in m.group(3).split(",") if p)
            steps.append((A, B, N)); continue
        m = re.search(r"A=\[([\d, ]*)\]\s+B=\[([\d, ]*)\]\s+N=(.*)$", line)   # decode.py format
        if m:
            A = [int(v) for v in m.group(1).split(",") if v.strip()]
            B = [int(v) for v in m.group(2).split(",") if v.strip()]
            N = dict(tuple(map(int, p.split("->"))) for p in m.group(3).split())
            steps.append((A, B, N))
    K = 2 * len(steps[0][0])
    return K, steps

def verify(K, steps, disjoint=False):
    dead = set()
    for j, (A, B, N) in enumerate(steps):
        A, B = set(A), set(B)
        if len(A) != K // 2 or len(B) != K // 2: return False, "step %d: wrong sizes" % (j + 1)
        if set(N) != A or set(N.values()) != B: return False, "step %d: N not a bijection A->B" % (j + 1)
        for x in A:
            if (x, N[x]) in dead: return False, "step %d: pair (%d,%d) not fresh" % (j + 1, x, N[x])
        if disjoint and B != set(range(K)) - A: return False, "step %d: not disjoint" % (j + 1)
        dead |= {(x, y) for x in A for y in B}
    return True, "ok"

def product(K, S, Kp, D):
    enc = lambda x, y: x * Kp + y
    out = []
    for (A, B, N) in D:
        out.append(([enc(x, y) for x in range(K) for y in A], [enc(x, y) for x in range(K) for y in B],
                    {enc(x, y): enc(x, N[y]) for x in range(K) for y in A}))
    for (A, B, N) in S:
        out.append(([enc(x, y) for x in A for y in range(Kp)], [enc(x, y) for x in B for y in range(Kp)],
                    {enc(x, y): enc(N[x], y) for x in A for y in range(Kp)}))
    return K * Kp, out

D2 = [([0], [1], {0: 1}), ([1], [0], {1: 0})]

def show(K, steps):
    ok, msg = verify(K, steps)
    print("order K=%d  length=%d  VALID=%s %s" % (K, len(steps), ok, "" if ok else msg))
    for j, (A, B, N) in enumerate(steps):
        print(" step %2d: A=%s B=%s N=%s" % (j + 1, ",".join(map(str, sorted(A))) + ",",
              ",".join(map(str, sorted(B))) + ",", ",".join("%d>%d" % (x, N[x]) for x in sorted(A)) + ","))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "verify":
        K, S = parse(sys.argv[2]); ok, msg = verify(K, S)
        print("order K=%d length=%d VALID=%s (%s)  disjoint=%s" % (K, len(S), ok, msg, verify(K, S, True)[0]))
    elif cmd == "product":
        K, S = parse(sys.argv[2]); Kp, D = parse(sys.argv[3])
        assert verify(K, S)[0] and verify(Kp, D, disjoint=True)[0], "inputs must be a schedule and a DISJOINT schedule"
        show(*product(K, S, Kp, D))
    elif cmd == "double":
        K, S = parse(sys.argv[2])
        for _ in range(int(sys.argv[3]) if len(sys.argv) > 3 else 1):
            K, S = product(K, S, 2, D2)
        show(K, S)
    else:
        print(__doc__)
