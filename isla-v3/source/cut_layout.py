"""Delete whole block strips and close them in a street-aligned coordinate frame.

Unlike moving a sparse selection into a deformed copy of every original street,
this records the removed territory explicitly. Retained parcels undergo one
translation. Important Blasco bends and the 100 protected ensembles reserve
their original footprint spans. The thin remaining strip is a street junction.
"""
import json,gzip,math
import numpy as np
from shapely.geometry import shape,mapping,Point,LineString,Polygon,box
from shapely.affinity import translate
from shapely.ops import transform,unary_union
from shapely import STRtree
from scipy.spatial import Delaunay
from rigid_units import source_ensembles

ANGLE=0.
C,S=math.cos(ANGLE),math.sin(ANGLE)
R=np.array([[C,S],[-S,C]])
OFFSET=np.array([1750.,1500.])

def oriented(g):return transform(lambda x,y,z=None:(C*np.asarray(x)+S*np.asarray(y),-S*np.asarray(x)+C*np.asarray(y)),g)
def merge(intervals):
 result=[]
 for a,b in sorted(intervals):
  if result and a<=result[-1][1]:result[-1][1]=max(result[-1][1],b)
  else:result.append([float(a),float(b)])
 return result

class CutField:
 def __init__(self,cuts,slopes):self.cuts=cuts;self.slopes=slopes
 def uv(self,p):
  original=np.asarray(p,float);p=original.copy()
  for axis in [0,1]:
   for index,(a,b,remaining) in enumerate(self.cuts[axis]):
    loss=np.clip((original[:,axis]-a)/(b-a),0,1)*(b-a-remaining);p[:,axis]-=loss
    if axis==0:p[:,1]-=loss*self.slopes[index]
  return p
 def points(self,p):return self.uv(np.asarray(p)@R.T)@R+OFFSET
 def crosses(self,g):
  b=oriented(g).bounds
  return any(b[k]<end-.01 and b[k+2]>start+.01 for k in [0,1] for start,end,width in self.cuts[k])
 def delta(self,g):
  c=np.array([g.centroid.x,g.centroid.y]);return self.points([c])[0]-c

def build_cut_layout(D,OLD,lookup,buildings,rel,Mesh,parts,feature,fc):
 mandatory=source_ensembles(OLD,lookup,rel)
 for label,mask in [('Alboraia',box(1850,2750,2600,3500)),('Port Saplaya',box(4350,3800,5100,4700))]:mandatory.append({'source':mask,'buildings':[],'landmarks':[],'required':[],'label':label})
 bt=STRtree([g for o,g in buildings]);used=set()
 for u in mandatory:
  u['buildings']=[buildings[int(i)] for i in bt.query(u['source'],predicate='intersects') if u['source'].covers(buildings[int(i)][1].representative_point())]
  u['source']=unary_union([u['source'],*[g for o,g in u['buildings']]]);u['mandatory']=True
  used.update(o['id'] for o,g in u['buildings']);used.update(i for i,g in u['landmarks'])
 reserves=[oriented(u['source']).bounds for u in mandatory]
 core=Polygon([(-3100,750),(-2200,2200),(-800,2450),(1200,2850),(2400,2200),(3300,1800),(4550,1400),(4800,-1550),(3800,-2700),(1300,-3000),(-1250,-2450),(-2850,-1300)])
 selection=unary_union([core,*[u['source'].buffer(80) for u in mandatory],rel(mapping(box(-.355,39.430,-.346,39.440)))])
 (D/'urban-selection-source.geojson').write_text(json.dumps(fc([feature(selection,'urban-selection')]),separators=(',',':')))
 axes=[[(b[k]-18,b[k+2]+18) for b in reserves] for k in [0,1]]
 blasco=[];bend_reserves=[]
 for o in lookup.values():
  if o['tags'].get('name')!='Avinguda de Blasco Ibáñez' or o['tags'].get('highway') not in ['primary','secondary','tertiary']:continue
  g=rel(o['geometry']);blasco.append(g);q=oriented(g).simplify(1.5)
  # Mislata and Alboraia also have streets with this name. Only protect the
  # Valencia avenue here; a shared name is not a shared alignment.
  if not(0<g.centroid.x<4100 and -800<g.centroid.y<1400):blasco.pop();continue
  for line in parts(q,'LineString'):
   p=np.array(line.coords);v=np.diff(p,axis=0);a=np.arctan2(v[:,1],v[:,0])
   for i,turn in enumerate(abs(np.angle(np.exp(1j*np.diff(a))))):
    if turn>math.radians(9):axes[0].append((p[i+1,0]-55,p[i+1,0]+55));bend_reserves.append(p[i+1].tolist())
 bg=oriented(unary_union(blasco));axes[1].append((bg.bounds[1]-60,bg.bounds[3]+60))
 # Cid's junction bends must survive too. Protect the short pieces that depart
 # from its long straight alignment, instead of squeezing roundabout approaches
 # into a narrow seam. Only its straight sections may be shortened.
 cid=[rel(o['geometry']) for o in lookup.values() if o['tags'].get('name')=='Avinguda del Cid' and o['tags'].get('highway') in ['primary','secondary','tertiary']]
 for g in cid:
  p=np.array(g.simplify(2).coords)
  for a,b in zip(p,p[1:]):
   v=b-a
   if np.linalg.norm(v)<12:continue
   angle=abs(math.atan2(v[0]*-.202-v[1],v[0]+v[1]*-.202))
   angle=min(angle,math.pi-angle)
   if angle>math.radians(4):axes[0].append((min(a[0],b[0])-18,max(a[0],b[0])+18))
 cuts=[]
 for axis in [0,1]:
  intervals=merge(axes[axis]);gaps=[]
  for left,right in zip(intervals,intervals[1:]):
   a,b=left[1]+5,right[0]-5
   if b-a>95:gaps.append([a,b,38. if axis==0 and a<bg.bounds[2] and b>bg.bounds[0] else 22.])
  cuts.append(gaps)
 slopes=[]
 for a,b,width in cuts[0]:
  slope=0.
  for references in [blasco,cid]:
   candidates=[]
   for g in references:
    for line in parts(g.intersection(box(a,-10000,b,10000)),'LineString'):
     if line.is_empty:continue
     p=np.array(line.coords);dx=p[-1,0]-p[0,0]
     if abs(dx)>15:candidates.append((line.length,(p[-1,1]-p[0,1])/dx))
   if candidates:
    slope=float(np.median([s for length,s in candidates if length>max(v[0] for v in candidates)*.3]));break
  slopes.append(slope)
 field=CutField(cuts,slopes)
 assert all(not field.crosses(u['source']) for u in mandatory)
 # Every retained source cell keeps all its houses, street frontages and yards.
 cells=json.load(open(OLD/'block-selection-source.geojson'))['features'];geoms=[shape(f['geometry']) for f in cells];ct=STRtree(geoms)
 occupied=unary_union([u['source'] for u in mandatory]);units=list(mandatory);decisions=[];removed_ids=set();kept_cell_ids=[]
 for i,g in enumerate(geoms):
  if not selection.covers(g.representative_point()):continue
  bs=[buildings[int(j)] for j in bt.query(g,predicate='intersects') if g.covers(buildings[int(j)][1].representative_point())]
  if not bs or g.area<120 or g.area>80000:continue
  footprint=unary_union([g,*[b for o,b in bs]])
  if g.intersection(occupied).area>2:
   action='protected-context';reason='Protected architectural ensemble'
  elif field.crosses(footprint):
   action='remove-and-close';reason='Whole block crosses an explicit closure strip';removed_ids.update(o['id'] for o,b in bs)
  else:
   action='retain';reason='Complete source block, translation only';fresh=[(o,b) for o,b in bs if o['id'] not in used]
   if fresh:units.append({'source':footprint,'cell':g,'cell_id':i,'buildings':fresh,'landmarks':[],'required':[],'mandatory':False});used.update(o['id'] for o,b in fresh)
   kept_cell_ids.append(i)
  decisions.append({'type':'Feature','geometry':mapping(g),'properties':{'source_cell':i,'action':action,'reason':reason,'source_area_m2':g.area,'buildings':len(bs)}})
 # Large campuses and industrial sites are not small street blocks. Their whole
 # individual building footprints can survive on either side of a deleted strip.
 for o,g in buildings:
  if o['id'] in used or o['id'] in removed_ids or field.crosses(g):continue
  if not selection.covers(g.representative_point()):continue
  cells_here=[int(i) for i in ct.query(g.representative_point(),predicate='intersects') if 120<geoms[int(i)].area<80000]
  if cells_here:continue
  units.append({'source':g.buffer(.5),'buildings':[(o,g)],'landmarks':[],'required':[],'mandatory':False});used.add(o['id'])
 for u in units:u['delta']=field.delta(u['source']);u['placed']=translate(u['source'],*u['delta'])
 # Rectangular break lines in the rotated frame are an exact triangulation of
 # this separable map; no nonlinear interpolation can bend an intact street.
 grids=[sorted({-14000.,14000.,*[p for a,b,width in cuts[k] for p in [a,b]]}) for k in [0,1]]
 uv=np.array([(u,v) for u in grids[0] for v in grids[1]]);src=uv@R;dst=field.points(src);mesh=Mesh(src,dst)
 probes=np.random.default_rng(23).uniform(-6500,6500,(1000,2));assert np.max(abs(mesh.points(probes)-field.points(probes)))<1e-7
 for u in units:
  # The buffered context of a single detached building can touch a seam by less
  # than a metre; the actual retained footprint must remain strictly rigid.
  for o,g in u['buildings']:
   p=np.array(g.exterior.coords) if g.geom_type=='Polygon' else np.array(g.convex_hull.exterior.coords)
   assert np.max(abs(mesh.points(p)-(p+u['delta'])))<1e-6,o['id']
 strips=[]
 for k in [0,1]:
  for a,b,width in cuts[k]:
   uvpoly=box(a,-6500,b,6500) if k==0 else box(-6500,a,6500,b)
   poly=transform(lambda x,y,z=None:(C*np.asarray(x)-S*np.asarray(y),S*np.asarray(x)+C*np.asarray(y)),uvpoly)
   strips.append(feature(poly,'removed-strip',axis=k,source_width_m=b-a,seam_width_m=width,closed_m=b-a-width))
 (D/'block-removal-ledger.geojson.gz').write_bytes(gzip.compress(json.dumps(fc(decisions),ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
 (D/'closure-strips.geojson').write_text(json.dumps(fc(strips),separators=(',',':')))
 (D/'urban-units.json.gz').write_bytes(gzip.compress(json.dumps([{'source':mapping(u['source']),'destination':mapping(u['placed']),'delta':u['delta'].tolist(),'mandatory':u['mandatory'],'cell_id':u.get('cell_id')} for u in units],separators=(',',':')).encode(),mtime=0))
 review={'method':'Explicit whole-block strip deletion and street-aligned seam closure. Retained buildings and protected ensembles translate at 1:1.','frame_angle_degrees':math.degrees(ANGLE),'cuts':cuts,'closure_vector_slopes':slopes,'target_distance_factor':None,'selected_ensembles':len(units),'source_blocks':len(cells),'ordinary_blocks':len(kept_cell_ids),'protected_ensembles':len(mandatory),'removed_complete_blocks':sum(f['properties']['action']=='remove-and-close' for f in decisions),'closed_distance_u_m':sum(b-a-w for a,b,w in cuts[0]),'closed_distance_v_m':sum(b-a-w for a,b,w in cuts[1]),'minimum_triangle_jacobian':float(mesh.signed_ratios().min()),'triangles':len(mesh.tri.simplices),'blocks_removed_to_prevent_mesh_folding':0}
 (D/'cut-layout-review.json').write_text(json.dumps(review,indent=2));print('CUT LAYOUT',json.dumps(review),flush=True)
 return units,mesh,review

def choose_streets(roads,units):
 """Keep block frontages and a source-graph connection to the avenue backbone.
 Empty neighbourhood loops are removed, not drawn as vacant city blocks.
 """
 import networkx as nx
 kept=unary_union([u['source'] for u in units]).buffer(32);graph=nx.Graph();essential=set();roots=set();entries={}
 walk={'footway','steps','path','pedestrian','cycleway','track','corridor','platform'}
 for o,g in roads:
  cls=o['tags'].get('highway');ident=o['id'];major=cls in ['primary','secondary','tertiary','motorway','trunk','primary_link','secondary_link','tertiary_link','motorway_link','trunk_link']
  retain=major or o['tags'].get('bridge') not in [None,'no'] or g.intersects(kept) or o['tags'].get('railway')
  if retain:essential.add(ident)
  if cls in walk or cls is None:continue
  for line in ([g] if g.geom_type=='LineString' else g.geoms):
   if line.geom_type!='LineString':continue
   a=tuple(np.round(line.coords[0],3));b=tuple(np.round(line.coords[-1],3));graph.add_edge(a,b,weight=line.length,osm=ident);entries.setdefault(ident,[]).extend([a,b])
   if major:roots.update([a,b])
 # Multi-source Dijkstra paths preserve the actual curves and junction sequence.
 _,paths=nx.multi_source_dijkstra(graph,list(roots),weight='weight');selected=set(essential)
 for ident in essential:
  for a in entries.get(ident,[]):
   path=paths.get(a,[])
   for x,y in zip(path,path[1:]):selected.add(graph[x][y]['osm'])
 return selected,{'source_road_features':len(roads),'retained_road_ids':len(selected),'removed_local_road_ids':len({o['id'] for o,g in roads}-selected),'source_backbone_connection':'Original OSM shortest paths; no invented cross-block links'}
