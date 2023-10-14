import yaml
import numpy as np
import cadquery as cq

path = '/home/ajrae/projects/rae-dux-v2/output/outlines'
points_path = '/home/ajrae/projects/rae-dux-v2/output/points/points.yaml'

points_yaml = None
with open(points_path) as f:
    points_yaml = yaml.load(f, yaml.FullLoader)

def get_point(name, scale=1):
    p = points_yaml[name]
    p = scale * np.array([p['x'], p['y'], 0])
    return list(p)

def extrudeDXF(file, e):
    obj = cq.importers.importDXF(file, tol=1e-2)
    return obj.wires().toPending().extrude(e)

def display(objs):
    center = get_point('matrix_index_home', -1)
    for obj in objs:
        obj = obj.translate(center)
        show_object(obj)

usbc_width = 8.34
usbc_height = 2.65
usbc_pcb_offset = 6
usbc_px = 2.3

pcb_width = 1.6
hotswap_height = 1.8
plate_width = 1.3

headroom = 9
fillet_width = 2

extrude_height = pcb_width + hotswap_height + plate_width + headroom - fillet_width
pcb_top = pcb_width + hotswap_height

case = extrudeDXF(f'{path}/case_outline.dxf', extrude_height)
case = case.shell(fillet_width).union(case) # fillet fails, so use shell instead
case = case.translate([0, 0, fillet_width])

pcb = extrudeDXF(f'{path}/pcb_cutout.dxf', -extrude_height)
pcb = pcb.translate([0, 0, hotswap_height + pcb_width])
case = case.cut(pcb)

inside = extrudeDXF(f'{path}/inside_cutout.dxf', extrude_height + fillet_width)
case = case.cut(inside)

keywell = extrudeDXF(f'{path}/keywell.dxf', extrude_height)
keywell = keywell.translate([0, 0, pcb_width + hotswap_height + plate_width])
case = case.cut(keywell)

switches = extrudeDXF(f'{path}/switches.dxf', extrude_height)
case = case.cut(switches)

# mcu_point
usbc = cq.Workplane('XY').box(usbc_width,15,usbc_height)
usbc = usbc.edges('|Y').fillet(usbc_height/2.01)
usbc = usbc.translate(get_point('mcu'))
usbc = usbc.translate([0, 18+15/2, pcb_top + usbc_pcb_offset])
usbc = usbc.faces('|Y').shell(usbc_px).union(usbc)
case = case.cut(usbc)

bottom_plate = extrudeDXF(f'{path}/base_outline.dxf', hotswap_height)


# display([case, bottom_plate])
display([case])
# display([case, usbc])
