"""Join settlement access roads to the city and verify actual graph routes.

Only necessary component joins are added. The previous all-endpoints-to-city
spurs are not retained. Routing avoids buildings, water and the runway; existing
OSM river crossings remain part of the graph. This is planar road connectivity,
not a claim of certified motorway lane movements or height-separated navigation.
"""
import json,pathlib,sys,math
import numpy as np
import networkx as nx
from shapely.geometry import shape,mapping,Point,LineString
from shapely.ops import unary_union,nearest_points,substring
from shapely import STRtree
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data'
sys.path.insert(0,str(P.parent/'isla-v2/source'))
from street_network import GroundRouter
from network_review import components

def main():
 doc=json.load(open(D/'isla-metros.geojson'));fs=doc['features'];landmarks=json.load(open(D/'landmarks.json'));coast=shape(next(f['geometry'] for f in fs if f['properties']['kind']=='coast'))
 fs[:]=[f for f in fs if f['properties'].get('name')!='Enlace de transición a la ciudad' and not f['properties'].get('integration_join')]
 walk={'footway','path','steps','pedestrian','cycleway','track','corridor','platform','elevator'}
 def driving(f):return f['properties']['kind'] in ['retained-road','urban-arterial','expressway','secondary-road','new-road'] and f['properties'].get('roadclass') not in walk
 roads=[f for f in fs if driving(f)]
 def landmark(prefix):return next(l for l in landmarks if prefix.lower() in l['name'].lower())
 definitions=[('Aeropuerto','Aeroport',None),('Bonaire','Bonaire',None),('Chelva','Chelva · iglesia','chelva'),('Benagéber','Embalse de Benagéber',None),('Cofrentes','Castillo de Cofrentes','cofrentes'),('Central nuclear','Central nuclear',None),('El Saler','El Saler','saler'),('El Palmar','El Palmar','palmar'),('Calpe','Calpe · casco','calpe')]
 stations=json.load(open(D/'transit.json'))['stations'];sites=[]
 for name,prefix,sector in definitions:
  xy=next(s['xy'] for s in stations if s['id']=='airport') if name=='Aeropuerto' else landmark(prefix)['xy'];p=Point(xy)
  assert coast.covers(p),'Destination outside island: '+name
  candidates=[f for f in roads if f['properties'].get('sector')==sector] if sector else []
  if not candidates:candidates=[f for f in roads if not f['properties'].get('city') and shape(f['geometry']).distance(p)<650]
  if not candidates:candidates=roads
  chosen=min(candidates,key=lambda f:shape(f['geometry']).distance(p));access=nearest_points(p,shape(chosen['geometry']))[1]
  sites.append({'name':name,'landmark_xy':xy,'access':access,'access_distance_m':p.distance(access)})
 obstacles=unary_union([shape(f['geometry']).buffer(3) for f in fs if f['properties']['kind'] in ['building','lake','reservoir','water','flood-bed']]+[shape(f['geometry']).buffer(95) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway'])
 router=GroundRouter(coast.bounds,obstacles,coast.buffer(-4),8)
 def curved(g):
  p=np.array(g.coords)
  for _ in range(3):
   q=[p[0]]
   for a,b in zip(p,p[1:]):q.extend([.75*a+.25*b,.25*a+.75*b])
   q.append(p[-1]);candidate=LineString(q)
   if not router.valid(candidate):break
   p=np.array(q)
  return LineString(p)
 joins=[]
 for iteration in range(18):
  cs=components(fs);root=cs[0]['geometry'];pending=[]
  for s in sites:
   index=min(range(len(cs)),key=lambda i:cs[i]['geometry'].distance(s['access']))
   if index:pending.append((cs[index]['geometry'].distance(root),s,cs[index]))
  if not pending:break
  made=False
  for gap,site,c in sorted(pending,key=lambda row:row[0]):
   a,b=nearest_points(c['geometry'],root);g=router.route(a,b)
   if g is None:
    # Try the exposed junctions of the destination component rather than
    # forcing a connection through a nearby house or across an unbridged river.
    points=[Point(line.coords[k]) for line in c['parts'] for k in [0,-1]]
    for a in sorted(points,key=lambda p:p.distance(root))[:64]:
     b=nearest_points(a,root)[1];g=router.route(a,b)
     if g is not None:break
   if g is None:continue
   g=curved(g);fs.append({'type':'Feature','geometry':mapping(g),'properties':{'kind':'new-road','name':'Enlace integrado · '+site['name'],'roadclass':'secondary','integration_join':True,'source':'Conexión entre carreteras existentes, sin atravesar edificios, agua ni pista'}})
   joins.append({'site':site['name'],'gap_m':gap,'length_m':g.length,'start':list(g.coords[0]),'end':list(g.coords[-1])});made=True;print('INTEGRATE',site['name'],round(g.length),'m',flush=True);break
  if not made:raise RuntimeError('Unroutable site connections: '+', '.join(s['name'] for gap,s,c in pending))
 else:raise RuntimeError('Site network did not converge')
 cs=components(fs);root=cs[0]['geometry']
 # Repair substantial fragments at the urban/regional seam, not every natural
 # cul-de-sac. Long or obstructed gaps remain explicitly unresolved.
 for c in cs[1:]:
  gap=c['geometry'].distance(root)
  if c['length_m']<400 or gap>150:continue
  a,b=nearest_points(c['geometry'],root);g=router.route(a,b)
  if g is None:
   points=sorted([Point(line.coords[k]) for line in c['parts'] for k in [0,-1]],key=lambda p:p.distance(root))[:12]
   for a in points:
    b=nearest_points(a,root)[1]
    if a.distance(b)>150:continue
    g=router.route(a,b)
    if g is not None:break
  if g is None or g.length>max(40,gap*2.5):continue
  g=curved(g);fs.append({'type':'Feature','geometry':mapping(g),'properties':{'kind':'new-road','name':'Costura entre red urbana y regional','roadclass':'tertiary','integration_join':True,'source':'Conexión de diseño por suelo libre; revisión de cotas pendiente'}})
  joins.append({'site':'Costura de red','gap_m':gap,'length_m':g.length,'start':list(g.coords[0]),'end':list(g.coords[-1])})
 cs=components(fs);root=cs[0]['geometry']
 # Remove only orphaned fragments of previously designed exterior connectors.
 trimmed=0
 for f in list(fs):
  p=f['properties'];g=shape(f['geometry'])
  if p['kind'] not in ['new-road','secondary-road','expressway'] or p.get('city') or p.get('integration_join'):continue
  if g.distance(root)>2 and all(g.distance(s['access'])>120 for s in sites):fs.remove(f);trimmed+=1
 cs=components(fs);root=cs[0];graph=nx.Graph()
 for line in root['parts']:
  a=tuple(np.round(line.coords[0]));b=tuple(np.round(line.coords[-1]));length=line.length
  if a==b:continue
  if not graph.has_edge(a,b) or length<graph[a][b]['weight']:graph.add_edge(a,b,weight=length,geometry=line)
 def insert_access(p):
  edges=list(graph.edges(data=True));tree=STRtree([e[2]['geometry'] for e in edges]);a,b,edge=edges[int(tree.nearest(p))];line=edge['geometry'];distance=line.project(p);q=line.interpolate(distance);node=tuple(q.coords[0])
  if q.distance(Point(a))<.01:return a
  if q.distance(Point(b))<.01:return b
  first,second=substring(line,0,distance),substring(line,distance,line.length)
  if Point(line.coords[0]).distance(Point(a))>.1:a,b=b,a
  graph.remove_edge(a,b);graph.add_edge(a,node,weight=first.length,geometry=first);graph.add_edge(node,b,weight=second.length,geometry=second)
  return node
 origin=Point(landmark('Ayuntamiento')['xy']);start=insert_access(origin);ends=[insert_access(s['access']) for s in sites];paths=[];rows=[]
 for s,end in zip(sites,ends):
  assert root['geometry'].distance(s['access'])<2,s['name']
  path=nx.shortest_path(graph,start,end,weight='weight');coords=[];length=0
  for a,b in zip(path,path[1:]):
   edge=graph[a][b];p=list(edge['geometry'].coords)
   if Point(p[0]).distance(Point(a))>Point(p[-1]).distance(Point(a)):p.reverse()
   coords+=p if not coords else p[1:];length+=edge['weight']
  g=LineString(coords);assert g.difference(root['geometry'].buffer(.01)).length<.01,s['name']
  paths.append({'type':'Feature','geometry':mapping(g),'properties':{'kind':'verified-road-route','name':'Valencia → '+s['name'],'length_m':length}})
  direct=Point(start).distance(Point(end));rows.append({'destination':s['name'],'connected':True,'route_length_m':length,'direct_distance_m':direct,'detour_ratio':length/direct,'landmark_to_access_road_m':s['access_distance_m'],'access_to_graph_node_m':s['access'].distance(Point(end))})
 (D/'integration-routes.geojson').write_text(json.dumps({'type':'FeatureCollection','features':paths},ensure_ascii=False,separators=(',',':')))
 report={'sites':rows,'joins':joins,'orphaned_designed_fragments_removed':trimmed,'planar_components_total':len(cs),'main_drivable_length_km':root['geometry'].length/1000,'main_component_fraction':root['length_m']/sum(c['length_m'] for c in cs),'remaining_components':[{'length_m':c['length_m'],'distance_to_main_m':c['geometry'].distance(root['geometry'])} for c in cs[1:]],'scope':'Shortest paths on the noded road graph, not decorative straight links. Planar connectivity; heights, restrictions and lanes need separate engineering.'}
 (D/'integration-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 doc['features']=fs;(D/'isla-metros.geojson').write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':')))
 metrics=json.load(open(D/'metrics.json'));metrics['integration']=report;(D/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,separators=(',',':')))
 print('VERIFIED',len(rows),'settlement routes',flush=True)

if __name__=='__main__':main()
