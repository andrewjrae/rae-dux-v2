import cadquery as cq

path = '/home/ajrae/projects/rae-dux-v2/output/outlines'

def extrudeDXF(file, e):
    obj = cq.importers.importDXF(file, tol=1e-2)
    return obj.wires().toPending().extrude(e)


def display(objs):
    for obj in objs:
        obj = obj.translate([-150, 180, 0])
        show_object(obj)

pcb_width = 1.6
hotswap_height = 1.8
plate_width = 1.3

headroom = 7
fillet_width = 4

extrude_height = pcb_width + hotswap_height + plate_width + headroom - fillet_width

case = extrudeDXF(f'{path}/case_outline.dxf', extrude_height)
case = case.shell(fillet_width/2).union(case)
case = case.translate([0, 0, fillet_width/2])

pcb = extrudeDXF(f'{path}/pcb_cutout.dxf', -extrude_height)
pcb = pcb.translate([0, 0, hotswap_height + pcb_width])

case = case.cut(pcb)

inside = extrudeDXF(f'{path}/inside_cutout.dxf', -extrude_height)
inside = inside.translate([0, 0, hotswap_height + headroom])

case = case.cut(inside)

keywell = extrudeDXF(f'{path}/keywell.dxf', extrude_height)
keywell = keywell.translate([0, 0, pcb_width + hotswap_height + plate_width])

case = case.cut(keywell)

switches = extrudeDXF(f'{path}/switches.dxf', extrude_height)
case = case.cut(switches)

bottom_plate = extrudeDXF(f'{path}/base_outline.dxf', hotswap_height)

# display([case, bottom_plate])
display([case])
