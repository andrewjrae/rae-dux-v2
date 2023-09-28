#!/usr/bin/env python3

import argparse
import os
import pcbnew

from pcbnew_helpers import import_ses, save_pcb, load_pcb
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--board')
    parser.add_argument('-s', '--session')
    args = parser.parse_args()

    pcb_path = Path(args.board)
    pcb = load_pcb(pcb_path)
    import_ses(pcb, args.session)

    routed_path = pcb_path.with_name(f'{pcb_path.stem}-routed.kicad_pcb')

    save_pcb(pcb, routed_path)

if __name__ == '__main__':
    main()
