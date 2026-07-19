#!/usr/bin/env bash
# Note: Do NOT use set -e in this script - we need to capture exit codes
set -uo pipefail
cd /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run
[[ -f '' ]] && source ''
date "+START: %F %T" > /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run/.task_status/p5_run_deseq2.start
echo RUNNING > /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run/.task_status/p5_run_deseq2.status

# Run the actual command and capture exit code
bash -c /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run/run.sh >> /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run/p5_run_deseq2.log 2>&1
ec=$?

if [[ $ec -eq 0 ]]; then
    echo SUCCESS > /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run/.task_status/p5_run_deseq2.status
else
    echo FAILED > /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run/.task_status/p5_run_deseq2.status
fi
date "+END: %F %T" > /Users/vlln/Project/loop_project/bio-reproducer/benchmarks/results/bench-001/run_03/repro-data/05_run/.task_status/p5_run_deseq2.end
exit $ec
