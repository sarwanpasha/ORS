#!/usr/bin/env python3
"""Lower bounds on t(n) obtained by combining the computed values with
   (i)  t(n) >= d(n)                          (a disjoint schedule is a schedule),
   (ii) t(K*K') >= t(K) + d(K')               (product lemma, src/constructions.py),
   (iii) t(n) >= d(n) >= 2 for every even n (a half-set A followed by its complement),
   doubling t(2K) >= t(K) + 2 being the case K' = 2, d(2) = 2.
Compares them with the conjectured value F(n) = floor(2 log2 n) + 2.

usage: python3 src/bounds.py [N] [--csv out.csv]
"""
import math, sys

T_EXACT = {2: 4, 4: 6, 6: 7, 8: 8, 10: 8}                    # exact t(K)
D_EXACT = {2: 2, 4: 4, 6: 4, 8: 6, 10: 6, 12: 6, 14: 6, 16: 8,
           18: 6, 20: 8, 22: 6, 24: 8}                          # exact d(K)
D_LOWER = {26: 7, 28: 8, 30: 7}                                 # d(K) >= value (explicit schedules)

def F(n): return int(math.floor(2 * math.log2(n))) + 2

def lower_bounds(N, D):
    lb, how = {}, {}
    for n in range(2, N + 1, 2):
        best, why = (T_EXACT[n], "exact") if n in T_EXACT else (2, "trivial: A, then its complement")
        if D.get(n, 0) > best: best, why = D[n], "t>=d"
        for kp, dk in D.items():
            if n % kp == 0 and (n // kp) % 2 == 0 and n // kp in lb and lb[n // kp] + dk > best:
                best, why = lb[n // kp] + dk, "t(%d)+d(%d)" % (n // kp, kp)
        lb[n], how[n] = best, why
    return lb, how

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 256
    D = {**D_EXACT, **D_LOWER}
    lb, how = lower_bounds(N, D)
    dbl, _ = lower_bounds(N, {2: 2})                            # doubling only
    ev = list(range(2, N + 1, 2))
    print("even n <= %d: lower bound reaches F(n) for %d (doubling alone: %d); product beats doubling for %d n"
          % (N, sum(lb[n] >= F(n) for n in ev), sum(dbl[n] >= F(n) for n in ev), sum(lb[n] > dbl[n] for n in ev)))
    print("%5s %6s %6s %5s  %s" % ("n", "LB", "dbl", "F(n)", "derivation"))
    for n in ev:
        if n <= 64 or lb[n] > dbl[n] and n <= 256:
            print("%5d %6d %6d %5d  %s" % (n, lb[n], dbl[n], F(n), how[n]))
    if "--csv" in sys.argv:
        with open(sys.argv[sys.argv.index("--csv") + 1], "w") as f:
            f.write("n,lower_bound,doubling_only,F\n")
            for n in ev: f.write("%d,%d,%d,%d\n" % (n, lb[n], dbl[n], F(n)))
