#!/usr/bin/env python3
"""Aggregate the DONE lines of a sharded sym run and check that the split is complete.
usage: python3 scripts/check_shards.py OUTDIR"""
import glob, re, sys
rows = []
for f in glob.glob(sys.argv[1] + "/*.txt"):
    for line in open(f):
        if line.startswith("DONE"):
            rows.append(dict(kv.split("=", 1) for kv in line.split()[1:] if "=" in kv))
if not rows: sys.exit("no finished shards")
nsh = int(rows[0]["shard"].split("/")[1])
done = {int(r["shard"].split("/")[0]) for r in rows}
splitcnt = {r["splitcnt"] for r in rows}
mine = sum(int(r["mine"]) for r in rows)
best = max(int(r["value"]) for r in rows); seed = int(rows[0]["seed"])
print("mode=%s K=%s seed=%d  shards finished %d/%d  splitcnt=%s  sum(mine)=%d  nodes=%d"
      % (rows[0]["mode"], rows[0]["K"], seed, len(done), nsh, ",".join(splitcnt), mine, sum(int(r["nodes"]) for r in rows)))
complete = len(done) == nsh and len(splitcnt) == 1 and (nsh == 1 or mine == int(splitcnt.pop()))
if complete:
    print("COMPLETE: value = %d%s" % (best, "  (no schedule longer than the seed exists)" if best == seed else ""))
else:
    print("INCOMPLETE: best so far %d; re-run the same command to finish the remaining shards" % best)
