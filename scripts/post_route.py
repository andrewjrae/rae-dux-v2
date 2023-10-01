#!/usr/bin/env python3

import argparse
import os
import pcbnew
import yaml
import numpy as np

from pcbnew_helpers import import_ses, save_pcb, load_pcb
from pathlib import Path

gnd_name = 'GND'
kicad_scaling_factor = 1000000
radius = 6.7
radius_kicad = int(radius * kicad_scaling_factor)

def is_key_point(str):
    is_key = str.startswith('matrix') or str.startswith('thumbfan')
    # ignore inner because the autorouter might actually do something useful here
    is_inner = str.startswith('matrix_inner')
    return is_key and not is_inner

def in_radius(a, b):
    diff = a - b
    return diff.EuclideanNorm() < radius_kicad

def track_in_radius(c, t):
    s = t.GetStart()
    e = t.GetEnd()
    return in_radius(c, s) and in_radius(c, e)

def get_key_points(points_path):
    points = {}
    points_yaml = None
    with open(points_path) as f:
        points_yaml = yaml.load(f, yaml.FullLoader)
    for k in points_yaml.keys():
        if is_key_point(k):
            x = points_yaml[k]['x'] * kicad_scaling_factor
            y = -points_yaml[k]['y'] * kicad_scaling_factor
            points[k] = pcbnew.VECTOR2I(int(x), int(y))
    return points

def get_key_tracks(points, tracks, copy=False):
    key_tracks = []
    for t in tracks:
        net = t.GetNetname()
        if is_key_point(net) and track_in_radius(points[net], t):
            if copy:
                t_copy = pcbnew.PCB_TRACK(t) # for some reason this copy ctor is broken
                t_copy.SetNet(t.GetNet())
                t_copy.SetWidth(t.GetWidth())
                t_copy.SetLayer(t.GetLayer())
                t_copy.SetStart(pcbnew.VECTOR2I(t.GetStart()))
                t_copy.SetEnd(pcbnew.VECTOR2I(t.GetEnd()))
                key_tracks.append(t_copy)
            else:
                key_tracks.append(t)
    return key_tracks

def import_and_clean_up(pcb, ses_path, points_path):
    points = get_key_points(points_path)

    tracks = pcb.Tracks()
    old_tracks = get_key_tracks(points, tracks, True)

    import_ses(pcb, ses_path)

    new_tracks = get_key_tracks(points, tracks)

    # remove the new tracks, some of which are unnecessary and ugly
    for t in new_tracks:
        pcb.Remove(t)

    # add back the old tracks
    for t in old_tracks:
        pcb.Add(t)

# probably shouldn't use pcb after this, some things have been cleaned up...
def ground_fill_and_save(pcb, out_path):
    # ground_fill(pcb)
    gnd = pcb.GetNetsByName()[gnd_name]

    # get board outline
    outline = pcbnew.SHAPE_POLY_SET()
    pcb.GetBoardPolygonOutlines(outline)

    # create new zone
    zone = pcbnew.ZONE(pcb)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNet(gnd)
    zone.SetOutline(outline)

    # add to zones and fill
    zones = pcb.Zones()
    zones.append(zone)

    zone_filler = pcbnew.ZONE_FILLER(pcb)
    zone_filler.Fill(zones)

    save_pcb(pcb, out_path)

    zone.SetOutline(None) # otherwise we hit a segfault

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--board')
    parser.add_argument('-s', '--session')
    parser.add_argument('-p', '--points')
    args = parser.parse_args()

    pcb_path = Path(args.board)
    pcb = load_pcb(pcb_path)

    import_and_clean_up(pcb, args.session, args.points)

    routed_path = pcb_path.with_name(f'{pcb_path.stem}-routed.kicad_pcb')
    ground_fill_and_save(pcb, routed_path)

if __name__ == '__main__':
    main()
