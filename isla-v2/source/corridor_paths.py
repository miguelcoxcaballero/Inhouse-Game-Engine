"""Continuous reference routes and bend-preserving length contraction."""
import json,pathlib,heapq,math,collections
import numpy as np
from pyproj import Transformer
from shapely.geometry import LineString,Point
from shapely.ops import transform
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';tr=Transformer.from_crs(4326,25830,always_xy=True).transform
raw=json.load(open(D/'corridors-osm.json'))
def get_path(ref,a,b):
 coord={};adj=collections.defaultdict(list);source={}
 for o in raw:
  t=o['tags']
  if t.get('ref')!=ref:continue
  c=o['nodes']
  for x,y,id in c:coord[id]=tr(x,y)
  for u,v in zip(c,c[1:]):
   un,vn=u[2],v[2];length=math.dist(coord[un],coord[vn]);adj[un].append((vn,length,o['id']));adj[vn].append((un,length,o['id']))
 components=[];seen=set()
 for node in adj:
  if node in seen:continue
  st=[node];component=[]
  while st:
   n=st.pop()
   if n in seen:continue
   seen.add(n);component.append(n);st.extend(v for v,l,id in adj[n])
  components.append(component)
 A=tr(*a);B=tr(*b)
 def nearest(c,p):return min(c,key=lambda n:math.dist(coord[n],p))
 options=[]
 for c in components:
  if len(c)<10:continue
  u,v=nearest(c,A),nearest(c,B);options.append((math.dist(coord[u],A)+math.dist(coord[v],B),u,v))
 score,start,end=min(options);dist={start:0};prev={};q=[(0,start)]
 while q:
  d,u=heapq.heappop(q)
  if d!=dist[u]:continue
  if u==end:break
  for v,l,id in adj[u]:
   if d+l<dist.get(v,float('inf')):dist[v]=d+l;prev[v]=(u,id);heapq.heappush(q,(d+l,v))
 ids=[];path=[end];n=end
 while n!=start:n,id=prev[n];path.append(n);ids.append(id)
 path.reverse();g=LineString([coord[n] for n in path]);return g,sorted(set(ids)),score

def compact(g,A,B):
 # RDP removes sub-12m survey chatter, not the important highway bends.
 c=np.asarray(g.simplify(12).coords);v=np.diff(c,axis=0);length=np.linalg.norm(v,axis=1);unit=v/length[:,None]
 angles=np.arctan2(v[:,1],v[:,0]);turn=np.abs(np.angle(np.exp(1j*np.diff(angles))));bend=np.maximum(np.r_[0,turn],np.r_[turn,0]);f=.16+.84*np.clip(bend/.42,0,1)
 newlength=np.minimum(length*f,230);p=np.vstack([[0,0],np.cumsum(unit*newlength[:,None],axis=0)])
 delta=np.asarray(B)-A;end=p[-1];angle=math.atan2(delta[1],delta[0])-math.atan2(end[1],end[0]);rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);p=p@rot.T*(np.linalg.norm(delta)/np.linalg.norm(end))+A
 # Keep these control vertices: angles are identical to simplified OSM, only leg lengths change.
 return LineString(p),{'original_m':g.length,'simplified_vertices':len(c),'design_m':LineString(p).length,'bearing_rotation_degrees':math.degrees(angle),'method':'Contract long straights more than bends; preserve turn angles at retained OSM vertices'}
if __name__=='__main__':
 for ref,a,b in [('V-30',(-.451,39.509),(-.330,39.439)),('V-21',(-.346,39.495),(-.292,39.56)),('CV-35',(-.431,39.509),(-.61,39.58)),('A-3',(-.507,39.467),(-.414,39.473))]:
  g,ids,e=get_path(ref,a,b);print(ref,round(g.length),len(ids),'endpoint error',round(e),'bounds',g.bounds)
