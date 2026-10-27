# Computed values

`t(K)`: longest fresh schedule of order `K`. `d(K)`: longest *disjoint* fresh schedule
(`B_j` = complement of `A_j`). Every lower bound has a witness in `schedules/` that
`python3 src/constructions.py verify FILE` checks directly against Definition 4.

## t(K)

| K | t(K) | how the upper bound was established | witness |
|---|---|---|---|
| 2 | 4 | `./sym t 2` (22 nodes) | — |
| 4 | 6 | `./sym t 4` (758 nodes) | — |
| 6 | 7 | `./sym t 6` (117,375 nodes); SAT: `gen_cnf.py 6 8` UNSAT | `schedules/t6.txt` |
| 8 | 8 | `./sym t 8 7` (709,945,256 nodes, also run as 1,024 shards); independently by the paper's certificate | — |
| 10 | 8 | 3-level cube-and-conquer on `gen_cnf.py 10 9`: every level-3 leaf (490,644 of them) UNSAT, no SAT leaf at any level | `schedules/t10.txt` |

All five values equal `⌊2 log2 K⌋ + 2`.

## d(K)

| K | d(K) | search | witness |
|---|---|---|---|
| 2 | 2 | `./sym d 2` | — |
| 4 | 4 | `./sym d 4` (10 nodes) | — |
| 6 | 4 | `./sym d 6` (6 nodes) | — |
| 8 | 6 | `./sym d 8` (152 nodes) | `schedules/d8.txt` |
| 10 | 6 | `./sym d 10` (55 nodes) | — |
| 12 | 6 | `./sym d 12` (1,030 nodes) | — |
| 14 | 6 | `./sym d 14` (256 nodes) | — |
| 16 | 8 | `./sym d 16` (141,973 nodes) | `schedules/d16.txt` |
| 18 | 6 | `./sym d 18` (18,587 nodes) | — |
| 20 | 8 | 256 shards, seed 7 (1,670,985 nodes) | `schedules/d20.txt` |
| 22 | 6 | 512 shards, seed 6 (958,456 nodes) | `schedules/d22.txt` |
| 24 | 8 | 2,048 shards, seed 8 (see below) | `schedules/d24.txt` |
| 26 | ≥ 7 | best found | `schedules/d26_lower.txt` |
| 28 | ≥ 8 | best found | `schedules/d28_lower.txt` |
| 30 | ≥ 7 | best found | `schedules/d30_lower.txt` |

For `K ≤ 14` the same values were also obtained by an independently written search that breaks
symmetry only at the first two steps (e.g. 2,717,048 nodes for `K = 12` instead of 1,030), and
`d(20) = 8` was obtained both by an unsharded run of an earlier implementation and by the sharded
run above.

### d(24) = 8: how the 2,048 shards were completed

* 2,022 of the 2,048 depth-4 shards finished directly (each reports `value=8`, all report
  `splitcnt=18302`, and their `mine` counts sum to 18,070).
* The remaining 26 shards (`mine` total 232, so 18,070 + 232 = 18,302) were each split 64 ways at
  depth 5; `d24_refined_shards_digest.txt` lists, per shard, the number of finished sub-shards,
  the sum of their `submine` counts and `subcnt` (equal for every completed shard).
* Four sub-shards were split a further 36 ways at depth 6; `d24_last4_digest.txt` shows that
  each is covered exactly once (sum of `sub2mine` = `sub2cnt`).
* No leaf at any level reported a schedule longer than 8.

## Lower bounds on t(n) from the product lemma

`python3 src/bounds.py 4096` combines the table above with `t(K·K') ≥ t(K) + d(K')`: for even
`n ≤ 4096` the resulting lower bound reaches `⌊2 log2 n⌋ + 2` for 38 values of `n` (31 with
doubling alone), and the product lemma improves on doubling alone for 619 values of `n`.
For example `t(160) ≥ t(10) + d(16) = 16 = ⌊2 log2 160⌋ + 2`
(`python3 src/constructions.py product schedules/t10.txt schedules/d16.txt`).
