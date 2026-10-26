"""Round the island's empty margins, pinning buildings and Valencia's shoreline."""
from common import *
from shapely import prepare
from shapely.ops import nearest_points

fs=json.load(open(D/'isla-metros.geojson'))['features'];old=shape(next(f['geometry'] for f in fs if f['properties']['kind']=='coast'))
buildings=[shape(f['geometry']) for f in fs if f['properties']['kind']=='building']
source=translate(rel(json.load(gzip.open(ROOT/'isla-v3/data/source-coast.geojson.gz'))),*OFFSET)
shorebox=box(6500,-3100,18000,8300);shore=source.intersection(shorebox)
allowed=box(-25000,-30000,25000,20000).difference(shorebox).union(shore)
# The offshore lighthouse sits on a narrow harbour structure, not a wide
# circular land pad. Keep its full footprint and a narrow quay connection.
for g in buildings:
 if not allowed.covers(g):
  a,b=nearest_points(g,allowed);allowed=allowed.union(g.buffer(12)).union(LineString([a,b]).buffer(12))
natural=[shape(f['geometry']).buffer(400 if f['properties']['kind']=='reservoir' else 180) for f in fs if f['properties']['kind'] in ['lake','reservoir','airfield']]
landmarks=[Point(l['xy']).buffer(70) for l in json.load(open(D/'landmarks.json')) if l['id'] not in ['f1-300','safor-300']]
raw=unary_union([g.buffer(60) for g in buildings]+natural+landmarks+[shore,Point(0,-12400).buffer(750)])
required=unary_union([Polygon(g.exterior).simplify(8) for g in parts(raw,'Polygon')]);required=required.intersection(allowed)
rounded=old.simplify(15).buffer(1800,quad_segs=12).buffer(-1800,quad_segs=12)
def outline(retreat):
 g=rounded.buffer(-retreat,quad_segs=12).union(required)
 g=g.buffer(500,quad_segs=12).buffer(-500,quad_segs=12).intersection(allowed)
 # Keep every required piece joined to the main island, including small quays.
 while g.geom_type!='Polygon':
  ps=sorted(parts(g,'Polygon'),key=lambda p:p.area,reverse=True);a=ps[0];b=min(ps[1:],key=a.distance);u,v=nearest_points(a,b);link=LineString([u,v]).buffer(15).intersection(allowed)
  ng=g.union(link)
  if len(list(parts(ng,'Polygon')))>=len(ps):ng=g.union(LineString([u,v]).buffer(12))
  g=ng
 return Polygon(g.exterior)
lo,hi=0.,2500.
print('COAST BUDGET',outline(lo).area/1e6,outline(hi).area/1e6,flush=True)
assert outline(lo).area>300e6>outline(hi).area
for i in range(24):
 mid=(lo+hi)/2;g=outline(mid)
 if g.area>300e6:lo=mid
 else:hi=mid
 if i%6==0:print('FIT',i,mid,g.area/1e6,flush=True)
coast=outline(hi);p=Point(min(coast.exterior.coords,key=lambda p:p[0]));base=coast
lo,hi=0.,200.
for _ in range(50):
 mid=(lo+hi)/2;g=base.union(p.buffer(mid,quad_segs=48))
 if g.area<300e6:lo=mid
 else:hi=mid
coast=base.union(p.buffer((lo+hi)/2,quad_segs=48));cover=coast.buffer(.02);prepare(cover)
assert coast.geom_type=='Polygon' and abs(coast.area-300e6)<.1
assert all(cover.covers(g) for g in buildings),'A protected footprint left the outline'
write('island-outline.geojson.gz',mapping(coast));write('coast-design-review.json',{'area_km2':coast.area/1e6,'source':'Rounded empty margins; fixed source Valencia shore, complete building footprints, lagoons and airport protected.','buildings_preserved':len(buildings),'bounds':coast.bounds})
print('DESIGNED COAST',coast.area/1e6,coast.bounds,flush=True)
