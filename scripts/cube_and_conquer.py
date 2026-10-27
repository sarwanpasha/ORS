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
                level = [l + (m,) for l in open_ for m in M]
        open_ = [l for l in level if done.get(l) != "UNSAT"]
    if not open_:
        print("RESULT: UNSAT -- no fresh schedule of order %d and length %d%s" %
              (K, T, "" if o.nshards == 1 else " in shard %d/%d" % (o.shard, o.nshards)))
    else:
        print("RESULT: incomplete, %d leaves still open (raise --timeouts and rerun)" % len(open_))

if __name__ == "__main__":
    main()
