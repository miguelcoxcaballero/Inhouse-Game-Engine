"""Planar connectivity review. Does not certify road levels, driveability or bridges."""
import json,pathlib,collections,math
import numpy as np
from shapely.geometry import shape,Point,LineString,mapping
from shapely.ops import unary_union,nearest_points
from shapely import set_precision,STRtree,union_all
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data'
def components(features):
 roads=[]
 for f in features:
  p=f['properties']
  if p['kind'] in ['retained-road','expressway','new-road','secondary-road','urban-arterial'] and p.get('roadclass','residential') not in ['footway','path','steps','pedestrian','cycleway','track','corridor','elevator','platform','bridleway','via_ferrata']:
   g=shape(f['geometry'])
   if g.geom_type in ['LineString','MultiLineString']:roads.append(g)
 u=union_all(roads,grid_size=1);parts=[u] if u.geom_type=='LineString' else list(u.geoms);adj=collections.defaultdict(list)
 for i,g in enumerate(parts):
  if g.geom_type!='LineString':continue
  a=tuple(round(v) for v in g.coords[0]);b=tuple(round(v) for v in g.coords[-1]);adj[a].append((b,i));adj[b].append((a,i))
 seen=set();cs=[]
 for st in adj:
  if st in seen:continue
  q=[st];edges=set()
  while q:
   a=q.pop()
   if a in seen:continue
   seen.add(a)
   for b,i in adj[a]:edges.add(i);q.append(b)
  geom=unary_union([parts[i] for i in edges]);cs.append({'length_m':geom.length,'geometry':geom,'parts':[parts[i] for i in edges]})
 return sorted(cs,key=lambda c:c['length_m'],reverse=True)
if __name__=='__main__':
 F=json.load(open(D/'isla-metros.geojson'))['features'];cs=components(F);main=cs[0]['geometry']
 for c in cs[1:10]:
  a,b=nearest_points(main,c['geometry']);print(round(c['length_m']),round(a.distance(b)),list(a.coords)[0],list(b.coords)[0])
