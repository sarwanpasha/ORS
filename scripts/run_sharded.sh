#!/bin/bash
# Run an exact sym search split into NSH independent shards, NCORES at a time, resumably.
#   usage: scripts/run_sharded.sh MODE K SEED NSH SPLITD NCORES OUTDIR [JOBIDX NJOBS]
#   e.g.   scripts/run_sharded.sh d 22 6 512 4 8 out_d22        # proves d(22) <= 6
# Shard s is finished iff OUTDIR/s<s>.txt contains a DONE line; finished shards are skipped,
# so the same command can be re-run (or spread over NJOBS machines/array tasks) until all are done.
# The search value is the maximum of the DONE values over all shards; the counts printed in the
# DONE lines let you check the split is complete: every shard reports the same splitcnt and the
# per-shard "mine" values sum to it.
set -u
MODE=$1 K=$2 SEED=$3 NSH=$4 SPLITD=$5 NC=$6 OUT=$7 JI=${8:-0} NJ=${9:-1}
HERE=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$OUT"; BIN=$(mktemp -d)/sym
gcc -O3 -march=native -o "$BIN" "$HERE/src/sym.c" 2>/dev/null || gcc -O3 -o "$BIN" "$HERE/src/sym.c" || exit 1
export BIN OUT MODE K SEED NSH SPLITD
one(){ s=$1; f=$OUT/s$s.txt; grep -q '^DONE' "$f" 2>/dev/null && return
  t=$(mktemp); "$BIN" $MODE $K $SEED $s $NSH $SPLITD > "$t" 2>/dev/null
  if grep -q '^DONE' "$t"; then mv "$t" "$f"; else rm -f "$t"; fi; }
export -f one
seq 0 $((NSH-1)) | awk -v j=$JI -v n=$NJ '$1%n==j' | xargs -P $NC -I{} bash -c 'one {}'
python3 "$HERE/scripts/check_shards.py" "$OUT"
