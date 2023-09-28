#!/usr/bin/env python3

import pcbnew
from pathlib import Path

def load_pcb(pcb_path):
    try:
        pcb = pcbnew.LoadBoard(pcb_path)
    except Exception as e:
        print(f'ERROR: {e}')
        exit(-1)
    return pcb

def import_ses(pcb, ses_path):
    ok = pcbnew.ImportSpecctraSES(pcb, ses_path)
    if not ok:
        print(f'Failed to import {ses_path} into {pcb.GetFileName()}!')
        exit(-1)

def export_dsn(pcb):
    pcb_path = pcb.GetFileName()
    pcb_path = Path(pcb_path)
    dsn_path = pcb_path.with_name(f'{pcb_path.stem}.dsn')

    ok = pcbnew.ExportSpecctraDSN(pcb, dsn_path)
    if not ok:
        print(f'Failed to export {pcb_path} to {dsn_path}!')
        exit(-1)

def save_pcb(pcb, pcb_path = None):
    if pcb_path is None:
        pcb_path = pcb.GetFileName()
        pcb_path = Path(pcb_path)
    try:
        pcb.Save(pcb_path)
    except Exception as e:
        print(f'Could not save pcb to {pcb_path}: {e}')
        exit(-1)
