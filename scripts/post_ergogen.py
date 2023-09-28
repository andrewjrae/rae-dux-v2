#!/usr/bin/env python3

import argparse
import os
import pcbnew

from pcbnew_helpers import export_dsn, save_pcb, load_pcb
from pathlib import Path

gnd_name = 'GND'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--board')
    args = parser.parse_args()

    print(args.board)
    pcb = load_pcb(args.board)

    ncs = pcb.GetNetClasses()
    gnd_nc = pcbnew.NETCLASS(gnd_name)
    ncs[gnd_name] = gnd_nc

    nc_assignments = pcb.GetNetClassLabelAssignments()
    nc_assignments[gnd_name] = gnd_name

    pcb.SynchronizeNetsAndNetClasses(False)

    save_pcb(pcb)
    export_dsn(pcb)

if __name__ == '__main__':
    main()
