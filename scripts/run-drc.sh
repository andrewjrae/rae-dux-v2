#!/usr/bin/env sh
board=${1:-output/pcbs/board-routed.kicad_pcb}
report=${board%.*}-drc.json
kicad-cli pcb drc --format json --severity-error -o $report $board

echo ""

# for whatever reason --severity-error doesn't work, so check the report instead
num_error=$(grep '"severity": "error"' -c $report)
if (( num_error > 0 )); then
   echo "$num_error errors found in DRC!"
   exit -1
else
   echo "No errors found in DRC!"
   exit 0
fi
