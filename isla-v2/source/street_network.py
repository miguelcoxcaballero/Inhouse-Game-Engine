"""Route short street seams through free ground; preserve existing block geometry."""
import heapq,math,json
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import Delaunay
from scipy.sparse.csgraph import minimum_spanning_tree
from shapely.geometry import Point,LineString,mapping
from shapely.ops import unary_union,nearest_points
from shapely import contains_xy,prepare

class GroundRouter:
 def __init__(self,bounds,obstacles,land,step=8):
  self.x0,self.y0,x1,y1=bounds;self.step=step;self.w=int((x1-self.x0)/step)+1;self.h=int((y1-self.y0)/step)+1;self.obstacles=obstacles;self.land=land;prepare(obstacles);prepare(land)
  X,Y=np.meshgrid(self.x0+np.arange(self.w)*step,self.y0+np.arange(self.h)*step);self.free=(~contains_xy(obstacles,X,Y))&contains_xy(land,X,Y);self.clearance=distance_transform_edt(self.free)*step
 def index(self,p):
  x=int(round((p.x-self.x0)/self.step));y=int(round((p.y-self.y0)/self.step));best=None
  for radius in range(0,8):
   for dy in range(-radius,radius+1):
    for dx in range(-radius,radius+1):
     a,b=x+dx,y+dy
     if 0<=a<self.w and 0<=b<self.h and self.free[b,a]:
      q=Point(self.x0+a*self.step,self.y0+b*self.step)
      if not LineString([p,q]).intersects(self.obstacles):
       score=p.distance(q)
       if best is None or score<best[0]:best=(score,b*self.w+a)
   if best is not None:return best[1]
  return None
 def point(self,k):return (self.x0+(k%self.w)*self.step,self.y0+(k//self.w)*self.step)
 def valid(self,g):return self.land.covers(g) and not self.obstacles.intersects(g)
 def route(self,a,b):
  direct=LineString([a,b])
  if self.valid(direct):return direct
  st,en=self.index(a),self.index(b)
  if st is None or en is None:return None
  ex,ey=en%self.w,en//self.w;dist={st:0};prev={};queue=[(math.hypot(st%self.w-ex,st//self.w-ey),0,st)];visited=0
  while queue:
   _,cost,k=heapq.heappop(queue)
   if cost!=dist.get(k):continue
   if k==en:break
   visited+=1
   if visited>180000:return None
   x,y=k%self.w,k//self.w
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
    nx,ny=x+dx,y+dy
    if not(0<=nx<self.w and 0<=ny<self.h and self.free[ny,nx]):continue
    if dx and dy and not(self.free[y,nx] and self.free[ny,x]):continue
    q=ny*self.w+nx;v=cost+math.hypot(dx,dy)*(1+.18*max(0,12-self.clearance[ny,nx])/12)
    if v<dist.get(q,float('inf')):dist[q]=v;prev[q]=k;heapq.heappush(queue,(v+math.hypot(nx-ex,ny-ey),v,q))
  if en not in dist:return None
  cells=[en]
  while cells[-1]!=st:cells.append(prev[cells[-1]])
  points=[a.coords[0]]+[self.point(k) for k in reversed(cells)]+[b.coords[0]]
  # Visibility smoothing removes raster stair steps without cutting through a block.
  out=[points[0]];i=0
  while i<len(points)-1:
   j=min(len(points)-1,i+160)
   while j>i+1 and not self.valid(LineString([points[i],points[j]])):j-=1
   out.append(points[j]);i=j
  g=LineString(out)
  if not self.valid(g):return None
  return g

def connect_city(D,units,roads,coast,hard,add):
 protected=unary_union([u['placed'].buffer(-5) for u in units]+[__import__('shapely').affinity.translate(g,*u['delta']).buffer(2) for u in units for _,g,_ in u['buildings']]).union(hard)
 land=coast.buffer(-125);router=GroundRouter((-350,-850,2950,2650),protected,land,8)
 centers=np.array([u['dest'] for u in units]);n=len(units);matrix=np.linalg.norm(centers[:,None]-centers[None,:],axis=2);mst=minimum_spanning_tree(matrix).tocoo();edges={tuple(sorted((int(a),int(b)))) for a,b in zip(mst.row,mst.col)}
 triangles=Delaunay(centers).simplices;candidates=set()
 for tri in triangles:
  for a,b in zip(tri,np.roll(tri,1)):candidates.add(tuple(sorted((int(a),int(b)))))
 extra=sorted(candidates-edges,key=lambda ij:matrix[ij])[:max(12,n//2)];todo=sorted(edges,key=lambda ij:matrix[ij])+extra
 added=[];failed=[]
 for i,j in todo:
  if roads[units[i]['id']].is_empty or roads[units[j]['id']].is_empty:failed.append([i,j]);continue
  a,b=nearest_points(roads[units[i]['id']],roads[units[j]['id']]);g=router.route(a,b)
  if g is None:failed.append([i,j]);continue
  add(g,'new-road',name='Enlace urbano entre manzanas',city=True,roadclass='footway' if units[i].get('required') or units[j].get('required') else 'tertiary',from_ensemble=i,to_ensemble=j,source='Costura de diseño alrededor de manzanas 1:1; no atraviesa edificios ni agua')
  added.append({'a':i,'b':j,'length_m':g.length,'direct_distance_m':a.distance(b)})
 report={'seams_added':len(added),'seam_length_m':sum(x['length_m'] for x in added),'seams':added,'unrouted_ensemble_pairs':failed}
 (D/'city-seams.json').write_text(json.dumps(report,indent=2));return report

def finish_network(D,fs,coast,add):
 """Repair cartographic road connectivity while preserving all rigid parcels.
 Existing real dead ends remain. Connections are explicitly design geometry,
 not inferred turn permissions or certified motorway interchanges.
 """
 from shapely.geometry import shape,MultiPoint
 from shapely import union_all
 from network_review import components
 blocks=[shape(f['geometry']).buffer(-4) for f in fs if f['properties']['kind']=='city-block']
 buildings=[shape(f['geometry']).buffer(1.5) for f in fs if f['properties']['kind']=='building']
 water=[shape(f['geometry']).buffer(2) for f in fs if f['properties']['kind'] in ['lake','water','reservoir','flood-bed']]
 runway=[shape(f['geometry']).buffer(85) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway']
 protected=unary_union(blocks+buildings+water+runway)
 router=GroundRouter(coast.bounds,protected,coast.buffer(-3),6)
 # Avoid any old design connector crossing the newly preserved urban parcels.
 urban_obstacles=unary_union(blocks+buildings)
 adjusted=[];removed=[]
 for f in list(fs):
  p=f['properties'];g=shape(f['geometry'])
  if p['kind']!='new-road' or p.get('city') or g.geom_type!='LineString' or not g.intersects(urban_obstacles):continue
  # Existing designated river bridges are left to the explicit crossing model.
  if g.intersects(unary_union(water)):continue
  a,b=Point(g.coords[0]),Point(g.coords[-1])
  # An old destination now inside a moved block attaches to its street boundary.
  for which,pt in enumerate([a,b]):
   if urban_obstacles.intersects(pt):
    streets=unary_union([shape(z['geometry']) for z in fs if z['properties']['kind']=='retained-road' and z['properties'].get('city')])
    q=nearest_points(pt,streets)[1]
    if which==0:a=q
    else:b=q
  ng=router.route(a,b)
  if ng is not None:
   f['geometry']=mapping(ng);p['rerouted_around_blocks']=True;adjusted.append(p.get('name',''))
  else:
   # Remove only the conflicting part, never an intact source block/building.
   ng=g.difference(urban_obstacles.buffer(3));f['geometry']=mapping(ng);removed.append(p.get('name',''))
 fs[:]=[f for f in fs if not shape(f['geometry']).is_empty]
 cs=components(fs);main=cs[0]['geometry'];pending=cs[1:];added=[];unresolved=[]
 print('NETWORK initial components',len(cs),flush=True)
 # Greedy nearest-component attachment; every successful route enlarges the backbone.
 while pending:
  distances=[c['geometry'].distance(main) for c in pending];j=int(np.argmin(distances));c=pending.pop(j);gap=distances[j]
  if gap<.8:main=union_all([main,c['geometry']],grid_size=1);continue
  if gap>850:
   unresolved.append({'length_m':c['length_m'],'gap_m':gap,'reason':'No short terrain-safe attachment','geometry':mapping(c['geometry'])});continue
  a,b=nearest_points(c['geometry'],main);g=router.route(a,b)
  if g is None:
   # Nearest pair can be on the wrong side of a building; try exposed junctions.
   pts=[]
   for line in c['parts']:
    pts.extend([Point(line.coords[0]),Point(line.coords[-1])])
   pts=sorted(pts,key=lambda pt:pt.distance(main));used=set()
   for a in pts[:32]:
    key=(round(a.x/8),round(a.y/8))
    if key in used:continue
    used.add(key);b=nearest_points(a,main)[1]
    if a.distance(b)>850:continue
    g=router.route(a,b)
    if g is not None:break
  if g is None:
   unresolved.append({'length_m':c['length_m'],'gap_m':gap,'reason':'Water, intact blocks or buildings obstruct attachment','geometry':mapping(c['geometry'])});continue
  add(g,'new-road',name='Enlace de continuidad viaria',roadclass='residential',source='Conexión de diseño por terreno libre; manzanas y edificios íntegros',network_repair=True)
  added.append({'gap_m':gap,'added_m':g.length});main=union_all([main,c['geometry'],g],grid_size=1)
  if len(added)%30==0:print('NETWORK connected',len(added),'remaining',len(pending),flush=True)
 # Re-node the actual final feature set. Incremental union can land a join on
 # opposite sides of a 1m rounding boundary; close these sub-metre seams explicitly.
 for iteration in range(8):
  final=components(fs)
  if len(final)<2:break
  backbone=final[0]['geometry'];changed=False
  for c in final[1:]:
   a,b=nearest_points(c['geometry'],backbone);gap=a.distance(b)
   if gap>2 or gap<1e-7:continue
   v=np.array(b.coords[0])-np.array(a.coords[0]);v/=gap
   g=LineString([np.array(a.coords[0])-v*1.5,np.array(b.coords[0])+v*1.5])
   if not router.valid(g):continue
   add(g,'new-road',name='Ajuste submétrico de unión',roadclass='residential',network_repair=True,source='Cierre de tolerancia de noding; sin alterar manzanas')
   added.append({'gap_m':gap,'added_m':g.length,'precision_repair':True});changed=True
  if not changed:break
 final=components(fs)
 unresolved=[{'length_m':c['length_m'],'gap_m':c['geometry'].distance(final[0]['geometry']),'reason':'Final planar topology review','geometry':mapping(c['geometry'])} for c in final[1:]]
 # Retain unresolved geometry as an explicit review layer, never hide failure in a percentage.
 (D/'network-unresolved.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':u.pop('geometry'),'properties':u} for u in unresolved]},indent=2))
 report={'connections_added':len(added),'designed_connectors_rerouted':adjusted,'conflicting_design_connectors_trimmed':removed,'unresolved_components':len(unresolved),'unresolved_length_m':sum(u['length_m'] for u in unresolved),'intact_buildings_removed':0,'scope':'Planar cartographic continuity, not lanes, grade separation or turn permissions.'}
 (D/'network-repair.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));return added,report
