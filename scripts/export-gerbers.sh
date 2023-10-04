#!/usr/bin/env sh
board=${1:-output/pcbs/board-routed.kicad_pcb}
output=${2:-output/gerbers}

mkdir -p $output
kicad-cli pcb export gerbers --subtract-soldermask -o $output $board
kicad-cli pcb export drill -o $output/ $board
zip $output.zip $output/*
