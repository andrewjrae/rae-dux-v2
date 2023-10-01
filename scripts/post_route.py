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
    return str.startswith('matrix') or str.startswith('thumbfan')

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

def get_key_tracks(points, tracks):
    key_tracks = {}
    for t in tracks:
        net = t.GetNetname()
        if is_key_point(net) and track_in_radius(points[net], t):
            s = pcbnew.VECTOR2I(t.GetStart())
            e = pcbnew.VECTOR2I(t.GetEnd())
            if net in key_tracks:
                key_tracks[net].append((s, e))
            else:
                key_tracks[net] = [(s, e)]
    return key_tracks

def dir_matches_old_track(old_tracks, t):
    thresh = 100000
    s = t.GetStart()
    e = t.GetEnd()
    dir = s - e
    dirnorm = dir.EuclideanNorm()
    # need floats to normalize
    dir = np.array([dir.x, dir.y]) / dirnorm
    for old_s, old_e in old_tracks:
        old_dir = old_s - old_e
        old_dirnorm = old_dir.EuclideanNorm()
        old_dir = np.array([old_dir.x, old_dir.y]) / old_dirnorm
        dir_matches = np.allclose(dir, old_dir, rtol=0.01) or np.allclose(-dir, old_dir, rtol=0.01)
        if dir_matches:
            return True
    return False

def import_and_clean_up(pcb, ses_path, points_path):
    points = get_key_points(points_path)

    tracks = pcb.Tracks()
    key_tracks = get_key_tracks(points, tracks)

    import_ses(pcb, ses_path)

    # clean up the annoying tracks that freerouting adds
    # basically just checks if it added any in a different direction than before
    tracks = pcb.Tracks()
    it = tracks.begin()
    while it != tracks.end():
        t = it.value()
        net = t.GetNetname()
        if is_key_point(net) and track_in_radius(points[net], t):
            if not dir_matches_old_track(key_tracks[net], t):
                to_erase = it.copy()
                it.previous()
                tracks.erase(to_erase)
                continue
        it.next()

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
