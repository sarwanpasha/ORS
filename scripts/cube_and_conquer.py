#!/usr/bin/env python3
"""Multi-level cube-and-conquer for "does a fresh schedule of order K and length T exist?".

Level 1  fixes step 2 to one canonical representative (a,b1,b2,b3) of each orbit under the
         stabiliser of the (already fixed) step 1  -- see src/gen_cnf.py.
Level 2  splits every level-1 cube that timed out by fixing A_3 to each of the C(K,K/2) sets.
Level 3  splits every level-2 sub-instance that timed out by fixing A_4 the same way.
Levels 2 and 3 are plain exhaustive case splits (every schedule has *some* A_3, A_4), so the
instance is UNSAT iff every leaf is UNSAT, and SAT as soon as one leaf is SAT.

usage:
  python3 scripts/cube_and_conquer.py K T [--jobs N] [--timeouts t1,t2,t3] [--solver PATH]
                                      [--shard i --nshards m] [--workdir DIR]
A SAT leaf is decoded and re-verified independently by src/decode.py.
Results are appended to WORKDIR/results.jsonl, so an interrupted run can simply be restarted.
"""
import argparse, itertools, json, os, subprocess, sys, tempfile
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "src", "gen_cnf.py")
DEC = os.path.join(HERE, "..", "src", "decode.py")

def cubes(K):
    H = K // 2
    for a in range(H + 1):
        for b1 in range(min(a, H) + 1):
            for b2 in range(min(H - a, H - b1) + 1):
                b3 = H - b1 - b2
                if 0 <= b3 <= H:
                    yield (a, b1, b2, b3)

def masks(K):
    return [sum(1 << i for i in c) for c in itertools.combinations(range(K), K // 2)]

def _canon(atoms, H):
    """All sets with exactly H elements that meet every atom in an initial segment (ascending)."""
    out = []
    def rec(i, left, acc):
        if i == len(atoms):
            if left == 0: out.append(acc)
            return
        rest = sum(len(a) for a in atoms[i + 1:])
        for c in range(0, min(len(atoms[i]), left) + 1):
            if left - c <= rest:
                rec(i + 1, left - c, acc | sum(1 << x for x in atoms[i][:c]))
    rec(0, H, 0)
    return out

def sym_children(K, leaf):
    """Children of a leaf under the symmetry-reduced split (option --sym).
    After step 1 (A1=B1=P, N1=id) and step 2 (A2,B2 fixed by the cube), the remaining symmetry is
    (sigma on rows, tau on columns) with sigma(P)=P, tau(P)=P, tau|P = sigma|P, sigma(A2)=A2,
    tau(B2)=B2, and, once A3 is fixed, sigma(A3)=A3.  Hence sigma may permute freely inside each
    row atom: on P the classes of membership in (A2, B2[, A3]); on the complement of P the classes
    of membership in (A2[, A3]).  A_{j+1} can therefore be taken to meet every such atom in an
    initial segment, which is an exhaustive (sound) split up to symmetry."""
    H = K // 2
    av, b1, b2, b3 = leaf[:4]
    P = set(range(H))
    A2 = set(range(av)) | set(range(H, H + (H - av)))
    B2 = set(range(b1)) | set(range(av, av + b2)) | set(range(H, H + b3))
    fixed = [A2] + [set(x for x in range(K) if (m >> x) & 1) for m in leaf[4:]]
    def sig(x):
        if x in P: return (0, x in A2, x in B2) + tuple(x in F for F in fixed[1:])
        return (1,) + tuple(x in F for F in fixed)
    groups = {}
    for x in range(K): groups.setdefault(sig(x), []).append(x)
    return _canon([groups[k] for k in sorted(groups)], H)

def solve(job):
    K, T, leaf, timeout, solver = job
    with tempfile.TemporaryDirectory() as d:
        cnf = os.path.join(d, "f.cnf")
        args = [sys.executable, GEN, str(K), str(T), cnf] + [str(v) for v in leaf]
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
        r = subprocess.run([solver, "-q", "--time=%d" % timeout, cnf], capture_output=True, text=True)
        if r.returncode == 10:
            mf = os.path.join(d, "model.txt"); open(mf, "w").write(r.stdout)
            dec = subprocess.run([sys.executable, DEC, cnf + ".map", mf], capture_output=True, text=True).stdout
            return leaf, "SAT", dec
        if r.returncode == 20:
            return leaf, "UNSAT", ""
        if r.returncode == 0:
            return leaf, "TIMEOUT", ""
        return leaf, "ERROR%d" % r.returncode, r.stderr[-300:]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("K", type=int); p.add_argument("T", type=int)
    p.add_argument("--jobs", type=int, default=os.cpu_count())
    p.add_argument("--timeouts", default="600,1800,7200", help="per-leaf seconds for levels 1,2,3")
    p.add_argument("--solver", default="kissat")
    p.add_argument("--shard", type=int, default=0); p.add_argument("--nshards", type=int, default=1)
    p.add_argument("--workdir", default="run_k{K}_t{T}")
    p.add_argument("--sym", action="store_true", help="split levels 2-3 only over symmetry classes of A_3, A_4")
    o = p.parse_args()
    K, T = o.K, o.T
    tl = [int(x) for x in o.timeouts.split(",")]
    wd = o.workdir.format(K=K, T=T); os.makedirs(wd, exist_ok=True)
    log = os.path.join(wd, "results.jsonl")
    done = {}
    if os.path.exists(log):
        for line in open(log):
            r = json.loads(line); done[tuple(r["leaf"])] = r["verdict"]
    M = masks(K)
    level = [c for i, c in enumerate(cubes(K)) if i % o.nshards == o.shard]
    with Pool(o.jobs) as pool:
        for lev in range(3):
            todo = [l for l in level if done.get(l) not in ("SAT", "UNSAT")]
            print("level %d: %d leaves (%d already decided)" % (lev + 1, len(level), len(level) - len(todo)), flush=True)
            jobs = [(K, T, l, tl[lev], o.solver) for l in todo]
            with open(log, "a") as f:
                for leaf, v, extra in pool.imap_unordered(solve, jobs):
                    done[leaf] = v
                    f.write(json.dumps({"level": lev + 1, "leaf": leaf, "verdict": v}) + "\n"); f.flush()
                    if v == "SAT":
                        print("SAT leaf", leaf); print(extra)
                        print("RESULT: a fresh schedule of order %d and length %d EXISTS" % (K, T)); return
                    if v.startswith("ERROR"):
                        print("solver error on", leaf, extra); return
            open_ = [l for l in level if done.get(l) == "TIMEOUT"]
            if not open_:
                break
            if lev < 2:
                level = [l + (m,) for l in open_ for m in (sym_children(K, l) if o.sym else M)]
        open_ = [l for l in level if done.get(l) != "UNSAT"]
    if not open_:
        print("RESULT: UNSAT -- no fresh schedule of order %d and length %d%s" %
              (K, T, "" if o.nshards == 1 else " in shard %d/%d" % (o.shard, o.nshards)))
    else:
        print("RESULT: incomplete, %d leaves still open (raise --timeouts and rerun)" % len(open_))

if __name__ == "__main__":
    main()
