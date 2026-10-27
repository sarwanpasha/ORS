# ORS: exact computations for the balanced fresh process

Code and data accompanying the paper *Ordered Ruzsa–Szemerédi graphs at the critical density*.
Everything here is self-contained: a C compiler and Python 3 are enough for all examples below,
and a SAT solver (kissat) is needed only for the SAT-based part.

## The objects

A **fresh schedule** of order `K` (even) and length `t` is a sequence of steps
`(A_1,B_1,N_1), …, (A_t,B_t,N_t)` where `A_j, B_j` are `K/2`-subsets of `{0,…,K-1}`, `N_j : A_j → B_j`
is a bijection, and every matched pair is *fresh*: for each `x ∈ A_j` there is no earlier step
`i < j` with `x ∈ A_i` and `N_j(x) ∈ B_i`. `t(K)` is the maximum length (Definition 4 in the paper).

A schedule is **disjoint** if `B_j = {0,…,K-1} \ A_j` for every step; `d(K)` is the maximum length
of a disjoint schedule. Disjoint schedules feed the **product lemma**

```
t(K·K') ≥ t(K) + d(K')        (doubling t(2K) ≥ t(K)+2 is the case K' = 2, d(2) = 2)
```

## Repository layout

| path | what it does |
|---|---|
| `src/sym.c` | exact depth-first search for `t(K)` (`t` mode) and `d(K)` (`d` mode) with full sequential symmetry breaking; optional 1-, 2- and 3-level splitting into independent shards |
| `src/gen_cnf.py` | DIMACS encoding of "a fresh schedule of order K and length T exists", with step-1 symmetry breaking and optional cubes fixing step 2 / `A_3` / `A_4` |
| `src/decode.py` | decodes a SAT model and re-verifies it directly against Definition 4 |
| `src/constructions.py` | parses and verifies schedules; builds the product and doubling constructions |
| `src/bounds.py` | table of lower bounds on `t(n)` obtained from the computed values and the product lemma |
| `scripts/cube_and_conquer.py` | portable 3-level cube-and-conquer driver around `gen_cnf.py` + kissat |
| `scripts/run_sharded.sh`, `scripts/check_shards.py` | resumable sharded runs of `sym` and the completeness check for them |
| `scripts/slurm_array_example.sbatch` | template for spreading a sharded run over a Slurm array |
| `results/` | summary of all computed values, per-shard digests, and witness schedules |

## Quick start (about two minutes on a laptop)

```bash
git clone https://github.com/sarwanpasha/ORS.git && cd ORS
gcc -O3 -march=native -o sym src/sym.c          # drop -march=native if your compiler objects

./sym t 6          # exact t(6)
./sym d 12         # exact d(12)
./sym d 16         # exact d(16), about one minute
```

Each run prints every improvement as it is found (`FOUND … len=L` followed by the schedule, one
step per line as `A=… B=… N=x>y,…`) and finishes with a line such as

```
DONE mode=t K=6 value=7 seed=0 ... nodes=117375 t=0s
DONE mode=d K=12 value=6 seed=0 ... nodes=1030 t=0s
DONE mode=d K=16 value=8 seed=0 ... nodes=141973 t=58s
```

`value` is the exact maximum. Give a third argument `seed` to search only for schedules longer
than `seed`: `./sym d 16 8` then proves that no disjoint schedule of order 16 has 9 steps
(`value=8` means "nothing better than the seed exists").

Verify schedules and build new ones from them:

```bash
python3 src/constructions.py verify  results/schedules/t10.txt     # an 8-step schedule of order 10
python3 src/constructions.py verify  results/schedules/d16.txt     # an 8-step disjoint schedule of order 16
python3 src/constructions.py product results/schedules/t10.txt results/schedules/d16.txt | head -1
#  -> order K=160  length=16  VALID=True        (t(160) >= t(10) + d(16) = 16)
python3 src/constructions.py double  results/schedules/t6.txt 3 | head -1
#  -> order K=48  length=13  VALID=True         (t(48) >= t(6) + 3*2)
python3 src/bounds.py 64                          # lower-bound table for even n <= 64
```

## SAT-based search (needs kissat)

```bash
git clone https://github.com/arminbiere/kissat.git && (cd kissat && ./configure && make -j)
export PATH=$PWD/kissat/build:$PATH

python3 src/gen_cnf.py 6 7 k6t7.cnf && kissat -q k6t7.cnf > k6t7.out   # "s SATISFIABLE"
python3 src/decode.py k6t7.cnf.map k6t7.out                             # VERIFIED=True + schedule
python3 src/gen_cnf.py 6 8 k6t8.cnf && kissat -q k6t8.cnf               # "s UNSATISFIABLE"  => t(6)=7
python3 src/gen_cnf.py 10 8 k10t8.cnf && kissat -q k10t8.cnf > k10t8.out  # SAT in a few seconds

python3 scripts/cube_and_conquer.py 6 8      # same question through the cube-and-conquer driver
```

`scripts/cube_and_conquer.py K T` splits the instance into level-1 cubes (canonical second
steps), then splits every cube that exceeds its time limit by fixing `A_3` (level 2) and then
`A_4` (level 3). It stops at the first SAT leaf (decoded and re-verified) and reports UNSAT only
when every leaf is UNSAT. Results are logged to `run_kK_tT/results.jsonl`, so an interrupted run
can be restarted with the same command; `--shard i --nshards m` splits the work across machines.

## Reproducing the paper's numbers

| claim | command | cost |
|---|---|---|
| `t(2)=4, t(4)=6, t(6)=7` | `./sym t 2`, `./sym t 4`, `./sym t 6` | seconds |
| `t(8)=8` | `./sym t 8 7` (finds 8, rules out 9; ≈7·10^8 nodes) | ≈10 CPU-minutes |
| `t(10)=8` | `python3 scripts/cube_and_conquer.py 10 9 --timeouts 600,1800,1800` | cluster scale (all ≈4.9·10^5 level-3 leaves UNSAT) |
| `d(K)`, `K ≤ 18` | `./sym d K` | ≤ 1 CPU-minute each |
| `d(20)=8` | `scripts/run_sharded.sh d 20 7 256 4 16 out_d20` | ≈3 CPU-hours |
| `d(22)=6` | `scripts/run_sharded.sh d 22 6 512 4 16 out_d22` | ≈6 CPU-hours |
| `d(24)=8` | `scripts/run_sharded.sh d 24 8 2048 4 NCORES out_d24` | thousands of CPU-hours; see `results/` |
| `d(26)≥7, d(28)≥8, d(30)≥7` | `./sym d 26` etc. (stop once the stated length is printed) | minutes to an hour |

`scripts/run_sharded.sh MODE K SEED NSH SPLITD NCORES OUTDIR [JOBIDX NJOBS]` runs the `NSH`
shards, skipping finished ones, and calls `scripts/check_shards.py`, which prints `COMPLETE`
only if every shard finished and the shards' work counts add up to the total. For very
unbalanced shards, `sym` accepts a second and third split level:

```
./sym MODE K SEED  shard nshards depth  [sub nsub depth2  [sub2 nsub2 depth3]]
```

For each finished leaf, the counts printed in its `DONE` line (`splitcnt/mine`, `subcnt/submine`,
`sub2cnt/sub2mine`) let you check that the pieces of every shard cover it exactly once.

## Why the symmetry breaking in `sym` is sound

After steps `1..j` the set of dead (non-fresh) pairs is the union of the rectangles `A_i × B_i`,
which does not depend on the bijections. Any permutation of `{0,…,K-1}` that fixes every `A_i`
and `B_i` setwise (acting on both coordinates) therefore maps the current state to itself and
maps valid continuations to valid continuations of the same length. Such permutations act
transitively within every *atom* of the partition generated by `A_1, B_1, …, A_j, B_j`, so we may
assume that the next `A` consists of the lowest-numbered elements of each atom, and that the next
`B` consists of the lowest-numbered elements of each atom of the partition refined by that `A`.
`sym` enumerates exactly these canonical candidates (as count vectors over atoms), checks each
by bipartite matching, and prunes with the bound "every step kills at least `K/2` fresh pairs".

## Results

See [`results/RESULTS.md`](results/RESULTS.md) for every value, the search statistics, and the
per-shard digests; `results/schedules/` holds a witness schedule for every lower bound.
