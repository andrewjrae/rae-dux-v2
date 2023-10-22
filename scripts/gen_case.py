import yaml
import numpy as np
import cadquery as cq
import argparse
import os

def main(outpath, in_gui=False):
    outlines_path = f'{outpath}/outlines'
    points_path = f'{outpath}/points'

    points_yaml = None
    with open(f'{points_path}/points.yaml') as f:
        points_yaml = yaml.load(f, yaml.FullLoader)

    units = None
    with open(f'{points_path}/units.yaml') as f:
        units = yaml.load(f, yaml.FullLoader)

    def get_points(check_func, scale=1, offset=0):
        points = []
        for key in points_yaml.keys():
            if check_func(key):
                points.append(get_point(key, scale=scale, offset=offset))
        return points

    def get_point(name, scale=1, offset=0):
        p = points_yaml[name]
        p = scale * np.array([p['x'], p['y'], 0])
        p = p + offset
        return tuple(p)

    def extrudeDXF(file, e):
        obj = cq.importers.importDXF(file, tol=1e-2).clean()
        return obj.wires().toPending().extrude(e)

    def display(objs):
        center = get_point('matrix_index_home', -1)
        for obj in objs:
            obj = obj.translate(center)
            show_object(obj)

    # units and params
    kx = units['kx']
    ky = units['ky']
    px = units['px']
    py = units['py']
    cap_tol = units['cap_tol']
    wall_width = units['wall_width']
    fillet_width = units['case_fillet']
    ceiling_width = wall_width

    heatset_radius = units['heatset_radius']
    heatset_depth = 4

    usbc_width = 12
    usbc_height = 7.5
    usbc_fillet = 2.5
    usbc_pcb_offset = 4.8

    pcb_width = 1.6
    plate_width = 2.2 # for both switch and bottom plate

    headroom = usbc_pcb_offset + 0.51*usbc_height

    pcb_top = plate_width + pcb_width + 0.3 # extra 0.3 for wiggle room
    full_height = pcb_top + headroom + ceiling_width
    extrude_height = full_height - 2*fillet_width

    slider_width = 8
    slider_height = 1.5
    slider_pad = 2
    slider_height_padded = slider_height + 2*slider_pad
    slider_pos = fillet_width + 0.5 + slider_height_padded/2

    def get_key(name, box=[kx-1, ky-1, 10], height=pcb_top+10):
        p = get_point(name)
        r = points_yaml[name]['r']
        key = cq.Workplane(origin=p).box(*box)
        key = key.rotate(p, [p[0], p[1], 1], r)
        return key.translate([0, 0, height])

    def all_keys(height=pcb_top+10):
        ret = None
        for p in points_yaml.keys():
            is_key = p.startswith('matrix') or p.startswith('thumbfan')
            if is_key:
                key = get_key(p, height=height)
                ret = ret + key if ret else key
        return ret

    def slider_cutout():
        cutout_top = full_height - fillet_width
        cutin = wall_width - 0.75
        p1 = [(0, fillet_width),
            (-cutin, slider_pos - slider_height_padded/2),
            (-cutin, slider_pos + slider_height_padded/2),
            (0, cutout_top)]
        t1 = [(-1, 1), (-1, 3), (1, 3), (1, 3)]
        rect = [(1, fillet_width),
                (0, fillet_width),
                (0, cutout_top),
                (1, cutout_top)]
        spline = (cq.Workplane('XZ')
                .moveTo(*rect[0])
                .lineTo(*rect[1])
                .spline(p1, t1)
                .lineTo(*rect[3])
                .close())
        spline = (spline
                .extrude(slider_width/2)
                .faces('<Y')
                .wires()
                .toPending())
        p2 = [(0, fillet_width), (0, cutout_top)]
        t2 = [(-1, 1.5), (1, 4)]
        spline = (spline
                .workplane(offset=0.39*ky)
                .moveTo(*rect[0])
                .lineTo(*rect[1])
                .spline(p2, t2)
                .lineTo(*rect[3])
                .close())
        sloft = (spline
                .workplane(offset=0.1*ky)
                .moveTo(*rect[0])
                .lineTo(*rect[1])
                .lineTo(*rect[2])
                .lineTo(*rect[3])
                .close()
                .loft(combine=True)
                )
        cutout = sloft
        cutout = sloft.mirror(mirrorPlane='XZ').union(sloft)

        slider = cq.Workplane('XY').box(10, slider_width, slider_height_padded)
        slider = slider.translate([0, 0, slider_pos])
        slider = slider.edges('|X').fillet(slider_height_padded/3)
        cutout = cutout.union(slider, tol=0.01, clean=True)

        tol = units['tol']
        cutout_x = get_point('outline_top_right')[0] + wall_width + tol
        cutout_y = get_point('slider')[1]
        return cutout.translate([cutout_x, cutout_y, 0])

    def thumb_cutout(cut_height=full_height):
        cap_tol = (4/3)*units['cap_tol']
        choc_travel = 1.5
        depth = 2.5*choc_travel
        wx = kx + cap_tol/2
        wy = ky + cap_tol/2
        near_rad = (np.pi / 180) * points_yaml['thumbfan_near_thumb']['r']
        near_rad = near_rad - np.pi/2
        near_dir = (np.cos(near_rad), np.sin(near_rad), 0)
        near = get_key('thumbfan_near_thumb',
                    [wx, wy, 2*depth],
                    cut_height)
        near = near.faces(f'>{near_dir}').workplane()
        near = near.moveTo(-wx/2, depth).line(0, -depth)
        near = near.spline([(-wx/2, 0),
                            (-wx/2 + 0.25 * kx, -depth)],
                        [(1, 0), (1, 0)])
        near = near.line(2.5*kx, 0).line(0, 2*depth).close()
        near = near.extrude(ky)

        far_rad = (np.pi / 180) * points_yaml['thumbfan_far_thumb']['r']
        far_rad = far_rad
        far_dir = (np.cos(far_rad), np.sin(far_rad), 0)
        far = get_key('thumbfan_far_thumb',
                    [1, wy, 2*depth],
                    full_height)
        far = far.faces(f'>{far_dir}').workplane()
        far = far.moveTo(wy/2, depth).line(0, -depth)
        far = far.spline([(wy/2, 0),
                        (wy/2 - 0.25 * ky, -depth)],
                        [(-1, 0), (-1, 0)])
        far = far.line(-1.5*ky, 0).line(0, 2*depth).close()
        far = far.extrude(ky)
        cut = near + far
        return cut.translate([0, 0, cut_height])

    # create case
    case = extrudeDXF(f'{outlines_path}/case_outline.dxf', extrude_height)
    case = case.shell(fillet_width).union(case) # fillet fails, so use shell instead
    case = case.translate([0, 0, fillet_width])

    # cutin to bottom of switch plate
    pcb = extrudeDXF(f'{outlines_path}/pcb_cutout.dxf', -extrude_height)
    pcb = pcb.translate([0, 0, pcb_top])
    case = case.cut(pcb)

    # hollow out inside
    inside = extrudeDXF(f'{outlines_path}/inside_cutout.dxf', full_height - ceiling_width)
    case = case.cut(inside)

    # keywell cutin
    keywell = extrudeDXF(f'{outlines_path}/keywell.dxf', extrude_height)
    keywell = keywell.translate([0, 0, pcb_top + plate_width])
    case = case.cut(keywell)

    # switch cutouts
    switches = extrudeDXF(f'{outlines_path}/switches.dxf', extrude_height)
    case = case.cut(switches)
    switch_clips = extrudeDXF(f'{outlines_path}/switch_clips.dxf', pcb_top + 0.55)
    case = case.cut(switch_clips)

    # usbc cutout
    usbc = (cq.Workplane('XY')
            .box(usbc_width,15,usbc_height)
            .edges('|Y')
            .fillet(usbc_fillet)
            .translate(get_point('mcu'))
            .translate([0, 18+15/2, pcb_top + usbc_pcb_offset])
            )
    case = case.cut(usbc)

    # slider
    # case = case.cut(slider_cutout())
    slider = slider_cutout()
    case = case.cut(slider, clean=True)
    # case = case.cut(slider)

    case = case.cut(thumb_cutout())

    def is_screw(name):
        return name.startswith('screw')

    screw_walls = (cq.Workplane('XY')
                   .pushPoints(get_points(is_screw))
                   .cylinder(headroom,
                             heatset_radius + wall_width,
                             centered=(1, 1, 0))
                   .translate([0, 0, pcb_top]))
    case = case + screw_walls
    screw_holes = (cq.Workplane('XY')
                   .pushPoints(get_points(is_screw))
                   .cylinder(heatset_depth,
                             heatset_radius,
                             centered=(1, 1, 0))
                   .translate([0, 0, pcb_top]))
    case = case - screw_holes

    wire_cut = (cq.Workplane('YZ')
                .cylinder(2.5*units['screw_offset'], 2.5)
                .translate(get_point('wire_cut'))
                .translate([0, wall_width/2, pcb_top]))
    case = case.cut(wire_cut)


    # bottom plate
    # Build it as thought it's right sided for now, just because I can't get cskHole
    # to work on the bottom
    bottom_plate = extrudeDXF(f'{outlines_path}/base_outline.dxf', plate_width)

    hotswaps = extrudeDXF(f'{outlines_path}/hotswap.dxf', 2*plate_width)
    bottom_plate = bottom_plate.cut(hotswaps)

    switch_holes = extrudeDXF(f'{outlines_path}/switch_holes.dxf', 1)
    bottom_plate = bottom_plate.cut(switch_holes)


    m2_diameter = 2*units['screw_radius']
    bottom_plate = (bottom_plate
                    .pushPoints(get_points(is_screw, offset=[0, 0, plate_width]))
                    .cskHole(m2_diameter, 3.8, 90, depth=None))

    mcu_width = units['mcu_width']
    mcu_height = units['mcu_height']
    pins = (cq.Workplane('XY')
            .box(6, 2.3, 2)
            .translate(get_point('jst_bat'))
            .pushPoints([
                get_point('mcu', offset=[-7.62, -2.54/2, 0]),
                get_point('mcu', offset=[7.62, -2.54/2, 0])])
            .box(2, mcu_height - 2.54, 2)
            )
    bottom_plate = bottom_plate.cut(pins)

    bottom_plate = bottom_plate.mirror(mirrorPlane='XY')
    bottom_plate = bottom_plate.translate([0, 0, plate_width])

    if in_gui:
        display([case, bottom_plate])
    else:
        case_path = f'{outpath}/case'
        try:
            os.mkdir(case_path)
        except:
            pass

        def export(left, path):
            left = left.clean()
            cq.exporters.export(left, f'{path}left.stl', tolerance=1e-4)
            cq.exporters.export(left, f'{path}left.step')
            right = left.mirror(mirrorPlane='YZ').clean()
            cq.exporters.export(right, f'{path}right.stl', tolerance=1e-4)
            cq.exporters.export(right, f'{path}right.step')

        export(case, f'{case_path}/case')
        export(bottom_plate, f'{case_path}/bottom')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('outpath')
    args = parser.parse_args()

    print('Generating rae-dux case!')
    main(args.outpath, in_gui=False)
else:
    # hardcode this as needed
    outpath = '/home/ajrae/projects/rae-dux-v2/output'
    main(outpath, in_gui=True)
