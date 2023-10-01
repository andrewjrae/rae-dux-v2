// Router
// Version: 0.1

// Snippets of code used here were taken from https://github.com/infused-kim/kb_ergogen_fp (adjust_oint)
// Credits goes to Github infused-kim, Thanks!

const a = await import('./assert.js')
const u = await import('./utils.js')
const anchor = await import('./anchor.js')
const mathjs = await import('mathjs')

module.exports = {
  params: {
    net: { type: "net", value: "" },
    width: { type: "number", value: 0.25 },
    route: { type: "array", value: [] },
    via_size: { type: "number", value: 0.8 },
    via_drill: { type: "number", value: 0.4 },
  },

  body: (p) => {
    const adjust_point = (point, rot=p.r, offset = [p.x, p.y]) => {
      let v = mathjs.rotate(point, mathjs.unit(`${-rot}deg`))
      return mathjs.add(v, offset)
    }

    const format_point = (point) => {
      return `${point[0]} ${point[1]}`
    }

    // (segment (start 108.8 108) (end 109.7 108) (width 0.2) (layer "F.Cu") (net 0))
    const gen_trace = (start, end, layer) => {
      return `(segment (start ${format_point(start)}) (end ${format_point(end)}) (width ${p.width})
              (layer ${layer}) (net ${p.net.index}))`
    }

    // (via (at 108.8 108) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 0))
    const gen_via = (pos) => {
      return `(via (at ${format_point(pos)}) (size ${p.viasize}) (drill ${p.viadrill})
              (layers "F.Cu" "B.Cu") (net ${p.net.index}))`
    }

    const route_params = ['point_type', 'route_type', 'layer', 'point', 'rotate']
    const point_types = ['relative', 'offset', 'anchor']
    const route_types = ['via', 'none', 'trace']

    let units = u.deepcopy(p.units)
    let rot = p.r
    let layer = undefined
    let route_parsed = []
    for (const r of p.route) {
      a.assert(r.point, 'Must specify router.route.point')
      a.unexpected(r, 'router.route', route_params)
      a.in(r.point_type, 'router.route.point_type', point_types)

      let route_type = 'trace'
      if (r.route_type) {
        a.in(r.route_type, 'router.route.route_type', route_types)
        route_type = r.route_type
      }

      if (r.layer) {
        layer = r.layer
      } else {
        a.assert(layer, 'Must specify an initial layer type in router.route')
      }

      if (r.rotate) {
        units.r = rot
        rot = rot + a.mathnum(r.rotate)(units)
      }

      let point = undefined
      if (r.point_type == 'anchor') {
        point = anchor.parse(r.point, 'router.route.point', p.points)(units)
        point = [point.x, -point.y]
      } else if (r.point_type == 'relative') {
        point = a.type(r.point)(units) == 'array' ? `[${r.point}]` : r.point
        point = a.mathnum(point)(units)._data
        point = adjust_point(point, rot)
      } else {
        point = r.point
      }

      route_parsed.push({
        layer: layer,
        point: point,
        route_type: route_type,
        point_type: r.point_type,
        rotate: rot
      })
    }


    const is_parsed = (r) => { return r.point_type != 'offset' }

    let traces = ''
    let last_point = [p.x, p.y]
    for (const [i, r] of route_parsed.entries()) {

      let point = r.point
      if (is_parsed(r)) {
        const next_parsed = route_parsed.slice(i+1).find(is_parsed)
        if (next_parsed) {
          let diff = mathjs.subtract(next_parsed.point, point)
          diff = mathjs.rotate(diff, mathjs.unit(`${next_parsed.rotate}deg`))
          units.rx = diff[0]
          units.ry = diff[1]
        } else {
          delete units.rx
          delete units.ry
        }
      } else {
          point = a.type(point)(units) == 'array' ? `[${point}]` : point
          point = a.mathnum(point)(units)._data
          point = adjust_point(point, r.rotate, last_point)
      }

      // console.log(point)
      if (r.route_type == 'trace' && i != 0) {
        traces += gen_trace(last_point, point, r.layer)
      } else if (r.route_type == 'via') {
        traces += gen_via(point)
      }

      last_point = point
    }

    return traces
  }
}
