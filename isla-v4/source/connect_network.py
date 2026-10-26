"""Connect actual source junctions. Crossing lines alone never imply a junction."""
from common import *
import networkx as nx
from scipy.spatial import cKDTree
from shapely.ops import nearest_points
from shapely import STRtree
sys.path.insert(0,str(ROOT/'isla-v2/source'))
from street_network import GroundRouter
from corridor_paths import get_path,compact
WALK={'footway','path','steps','pedestrian','cycleway','track','corridor','platform','elevator','bridleway','via_ferrata'}
KINDS={'retained-road','urban-arterial','expressway','new-road','secondary-road'}
def drivable(f):return f['properties']['kind'] in KINDS and f['properties'].get('roadclass') not in WALK
def key(p):return tuple(round(float(v),2) for v in p[:2])

def make_graph(fs):
 graph=nx.Graph()
 for index,f in enumerate(fs):
  if not drivable(f):continue
  p=f['properties']
  for line in parts(shape(f['geometry']),'LineString'):
   coords=list(line.coords)
   for a,b in zip(coords,coords[1:]):
    a,b=key(a),key(b)
    if a==b:continue
    length=math.dist(a,b)
    if not graph.has_edge(a,b) or graph[a][b]['weight']>length:graph.add_edge(a,b,weight=length,feature=index,sector=p.get('sector','design'),roadclass=p.get('roadclass','secondary'),ref=p.get('ref',''),layer=p.get('layer','0'))
 return graph

def main():
 doc=json.load(open(D/'isla-metros.geojson'));fs=[f for f in doc['features'] if not f['properties'].get('integration_join') and f['properties']['kind']!='circuit'];coast=shape(next(f['geometry'] for f in fs if f['properties']['kind']=='coast'));landmarks=[l for l in json.load(open(D/'landmarks.json')) if l['id'] not in ['f1-300','safor-300']];graph=make_graph(fs)
 def landmark(name):return next(l for l in landmarks if name.lower() in l['name'].lower())
 print('JUNCTION GRAPH',len(graph),graph.number_of_edges(),flush=True)
 # Source streets include their surveyed shared vertices; road decks crossing
 # another line at a different level do not magically acquire graph edges.
 obstacles=unary_union([shape(f['geometry']).buffer(2) for f in fs if f['properties']['kind'] in ['building','lake','reservoir','water','flood-bed']]+[shape(f['geometry']).buffer(95) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway'])
 router=GroundRouter(coast.bounds,obstacles,coast.buffer(-8),14)
 def smooth(line):
  p=np.array(line.coords)
  for _ in range(3):
   q=[p[0]]
   for a,b in zip(p,p[1:]):q.extend([a*.75+b*.25,a*.25+b*.75])
   q.append(p[-1]);g=LineString(q)
   if not router.valid(g):break
   p=np.array(q)
  return LineString(p)
 def local_route(a,b,margin=350):
  direct=LineString([a,b])
  if router.valid(direct):return direct
  bounds=(min(a[0],b[0])-margin,min(a[1],b[1])-margin,max(a[0],b[0])+margin,max(a[1],b[1])+margin)
  return GroundRouter(bounds,obstacles,coast.buffer(-8),8).route(Point(a),Point(b))
 templates={'chelva':('CV-35',(-.431,39.509),(-.61,39.58)),'cofrentes':('N-330',(-1.06,39.24),(-1.07,39.20)),'jalance':('N-330',(-1.06,39.23),(-1.077,39.19)),'albufera':('CV-500',(-.332,39.42),(-.331,39.38)),'calpe':('CV-755',(-.17,38.66),(-.06,38.65)),'ifac':('CV-749',(-.03,38.68),(.01,38.72))}
 references={}
 for region,args in templates.items():
  try:references[region]=get_path(*args)[0]
  except (ValueError,KeyError,IndexError):pass
 joins=[]
 def add_road(g,name,kind='new-road',reference=None):
  coords=[key(p) for p in g.coords];g=LineString(coords);index=len(fs)
  fs.append(feature(g,kind,name=name,roadclass='secondary',integration_join=True,source='Real OSM road bend template fitted to existing junctions' if reference else 'Designed junction connection through free ground',template=reference or 'ground routing'))
  for a,b in zip(coords,coords[1:]):
   if a!=b:graph.add_edge(a,b,weight=math.dist(a,b),feature=index,sector='design',roadclass='secondary',ref='',layer='0')
  joins.append({'name':name,'length_m':g.length,'source_template':reference,'start':coords[0],'end':coords[-1]});print('JOIN',name,round(g.length),'m',flush=True)
 def components():return sorted(nx.connected_components(graph),key=len,reverse=True)
 def candidates(nodes,sector=None,ref=None):
  rows=[]
  for n in nodes:
   edges=graph[n].values()
   if sector and not any(e['sector']==sector for e in edges):continue
   if ref and not any(e['ref']==ref for e in graph[n].values()):continue
   if not any(e['roadclass'] in ['primary','secondary','tertiary','trunk','motorway','unclassified','residential','primary_link','secondary_link','motorway_link'] for e in graph[n].values()):continue
   rows.append(n)
  return rows
 def exposed(nodes):
  # New links start on accessible surveyed pavement, outside buildings,
  # water and the coast margin. A bridge vertex is not a land junction.
  return [n for n in nodes if router.land.covers(Point(n)) and not obstacles.intersects(Point(n))]
 def endpoint_pairs(town,main,limit=48):
  town=exposed(town);main=exposed(main)
  if not town or not main:return []
  tree=cKDTree(main);dist,ix=tree.query(town,k=min(4,len(main)));pairs=[];used=set()
  for flat in np.argsort(np.asarray(dist).ravel()):
   j,k=np.unravel_index(flat,np.asarray(dist).shape) if np.asarray(dist).ndim==2 else (flat,0)
   a=main[int(ix[j,k] if np.asarray(ix).ndim==2 else ix[j])];b=town[int(j)]
   cell=tuple(round(v/100) for p in [a,b] for v in p)
   if cell in used:continue
   used.add(cell);pairs.append((a,b))
   if len(pairs)>=limit:break
  return pairs
 # Join the major street component of each town to the metropolitan network.
 for region in ['chelva','cofrentes','jalance','albufera','calpe','ifac']:
  cs=components();root=cs[0];source_nodes={n for a,b,e in graph.edges(data=True) if e['sector']==region for n in [a,b]};target=max(cs,key=lambda c:len(c&source_nodes));town=candidates(target&source_nodes)
  if target is root or target==root:continue
  preferred={'chelva':'CV-35','cofrentes':'A-3','albufera':'CV-500'}.get(region);main=candidates(root,ref=preferred) if preferred else candidates(root)
  if not main:main=candidates(root)
  pairs=endpoint_pairs(town,main);accepted=None
  print('CONNECT',region,'candidate pairs',len(pairs),'nearest',round(math.dist(*pairs[0])) if pairs else None,flush=True)
  # Candidate endpoints must be existing road vertices, not visually close
  # line crossings. Keep the source bend profile when it fits the landscape.
  for a,b in pairs:
   if region in references:
    ref=references[region];curve,_=compact(ref,a,b)
    for amount in [1,.75,.5]:
     p=np.array(curve.coords);t=np.linspace(0,1,len(p))[:,None];straight=np.array(a)*(1-t)+np.array(b)*t;p=straight+(p-straight)*amount;p[0]=a;p[-1]=b;g=LineString(p)
     if router.valid(g) and g.length<math.dist(a,b)*2:accepted=(smooth(g),templates[region][0]);break
   if accepted:break
  if accepted is None:
   fallback=endpoint_pairs(town,candidates(root),24)
   for a,b in sorted(fallback[:12]+pairs[:6],key=lambda ab:math.dist(*ab)):
    g=local_route(a,b,1200)
    if g is not None:accepted=(smooth(g),None);break
  if accepted is None:
   for a,b in fallback:
    g=router.route(Point(a),Point(b))
    if g is not None:accepted=(smooth(g),None);break
  if accepted is None:raise RuntimeError('No safe road connection for '+region)
  add_road(accepted[0],'Acceso integrado · '+REGIONS[region]['name'],reference=accepted[1])
 # Reservoir approach ends on land beside the dam, rather than at the centre
 # of a lake. The crossing of the dam itself is not invented as a drivable road.
 reservoir=next(shape(f['geometry']) for f in fs if f['properties']['kind']=='reservoir');dam=Point(landmark('Presa de Benagéber')['xy']);shore=reservoir.buffer(45).boundary;q=nearest_points(dam,shore)[1];access=key(q.coords[0]);root=components()[0];nodes=exposed(candidates(root));order=np.argsort(np.linalg.norm(np.array(nodes)-access,axis=1));g=None;starts=[];seen=set()
 for j in order:
  n=nodes[int(j)];cell=tuple(round(v/100) for v in n)
  if cell in seen:continue
  seen.add(cell);starts.append(n)
  if len(starts)>=32:break
 for n in starts:
  g=local_route(n,access,1500)
  if g is not None:break
 if g is None:
  for n in starts[:12]:
   g=router.route(Point(n),Point(access))
   if g is not None:break
 if g is None:raise RuntimeError('Reservoir approach cannot reach the shore')
 add_road(smooth(g),'Benagéber · acceso a la presa');reservoir_access=access
 # Secondary mountain routes are continuous real bend templates between
 # existing junctions. They form alternative routes rather than loose stubs.
 mountain_specs=[('Chelva – Benagéber','CV-390',(-1.097,39.727),(-1.05,39.77),(-6200,7000),reservoir_access),('Benagéber – Cofrentes','CV-580',(-.78,39.17),(-.82,39.29),reservoir_access,(-1000,-4500)),('Jalance – Safor – Calpe','CV-700',(-.30,38.80),(-.17,38.83),(-500,-8500),(3600,-15300))]
 for name,ref,ll_a,ll_b,near_a,near_b in mountain_specs:
  root=components()[0];nodes=candidates(root);tree=cKDTree(nodes);a=nodes[int(tree.query(near_a)[1])];b=nodes[int(tree.query(near_b)[1])]
  try:template=get_path(ref,ll_a,ll_b)[0];curve,_=compact(template,a,b)
  except (ValueError,KeyError,IndexError):continue
  for amount in [1,.7,.45]:
   p=np.array(curve.coords);t=np.linspace(0,1,len(p))[:,None];straight=np.array(a)*(1-t)+np.array(b)*t;p=straight+(p-straight)*amount;p[0]=a;p[-1]=b;g=LineString(p)
   if router.valid(g) and g.length<math.dist(a,b)*2:add_road(smooth(g),name,'secondary-road',ref);break
 # Reattach newly cut rural edges to surveyed local street vertices. Endpoints
 # inside the protected city were never moved by the regional seam pass.
 seam_file=D/'regional-seams.json'
 if seam_file.exists():
  root=components()[0];nodes=exposed(candidates(root));tree=cKDTree(nodes);seen=set()
  for row in json.load(open(seam_file))['attachment_ends']:
   a=key(row['xy'])
   if a in seen or a not in graph or graph.degree[a]!=1:continue
   seen.add(a);own={e['feature'] for e in graph[a].values()};dist,ix=tree.query(a,k=min(24,len(nodes)))
   for distance,j in zip(np.atleast_1d(dist),np.atleast_1d(ix)):
    if distance>180:break
    b=nodes[int(j)]
    if distance<.05 or any(e['feature'] in own for e in graph[b].values()):continue
    g=local_route(a,b,120)
    if g is not None and g.length<350:add_road(smooth(g),'Encuentro entre pueblo y entorno');break
 # Close short source extraction gaps, retaining natural dead ends. Junctions
 # at different levels are never merged just because they cross on the map.
 cs=components();root=cs[0];rootnodes=np.array(list(root));tree=cKDTree(rootnodes)
 for c in cs[1:]:
  length=sum(e['weight'] for a,b,e in graph.subgraph(c).edges(data=True))
  if length<250:continue
  tips=[n for n in c if graph.degree[n]==1]
  if not tips:continue
  distances,ids=tree.query(tips);order=np.argsort(distances)
  for j in order[:5]:
   if distances[j]>35:break
   a=tips[int(j)];b=tuple(rootnodes[int(ids[int(j)])]);line=LineString([a,b])
   if router.valid(line):add_road(line,'Continuidad de calle · borde de selección');break
 # A labelled harbour-street interpretation remains available. Do not present
 # it as the surveyed historic F1 alignment.
 port=Point(point_at((-.329,39.452)));portnodes=[n for n in graph if Point(n).distance(port)<2100];cycles=[]
 for c in nx.cycle_basis(graph.subgraph(portnodes)):
  if len(c)<5:continue
  ring=LineString(c+[c[0]])
  if 1500<ring.length<6500 and ring.is_ring and Polygon(ring).area>80000:cycles.append(ring)
 if cycles:
  ring=min(cycles,key=lambda g:abs(g.length-5419));fs.append(feature(ring,'circuit',name='Antiguo F1 · propuesta sobre calles portuarias',source='Closed loop on OSM harbour streets; historic course still requires reconstruction'))
  landmarks.append({'id':'f1-300','name':'Antiguo circuito de Fórmula 1 · interpretación','xy':list(ring.interpolate(.2,normalized=True).coords[0]),'zone':'valencia','retention':'Circuito cerrado sobre calles reales del puerto; trazado histórico pendiente.'})
  write('circuit-review.json',{'closed':True,'length_m':ring.length,'historical_fidelity':'Interpretation on source harbour streets, not exact historical course'})
 else:raise RuntimeError('No closed harbour street loop found')
 landmarks.append({'id':'safor-300','name':'Montañas de la Safor · relieve de diseño','xy':[0,-12400],'zone':'sur','retention':'Montañas al sur de la isla; relieve sintético, no DEM real.'});write('landmarks.json',landmarks)
 # Verify all requested settlements and major facilities against this graph.
 definitions=[('Aeropuerto','Aeropuerto · Terminal 1','metro'),('Bonaire','Bonaire','metro'),('Manises','Manises','metro'),('Quart de Poblet','Quart de Poblet','metro'),('Alboraia','Alboraia','metro'),('Port Saplaya','Port Saplaya','metro'),('Sedaví','Sedaví','metro'),('Alfafar','Alfafar','metro'),('Catarroja','Catarroja','metro'),('Pinedo','Pinedo','metro'),('Chelva','Chelva · iglesia','chelva'),('Cofrentes','Castillo de Cofrentes','cofrentes'),('Central nuclear','Central nuclear','cofrentes'),('Jalance','Jalance','jalance'),('El Saler','El Saler','albufera'),('El Palmar','El Palmar','albufera'),('Calpe','Calpe · casco','calpe')]
 root=components()[0];rootnodes=np.array(list(root));tree=cKDTree(rootnodes);origin=Point(landmark('Ayuntamiento')['xy']);start=tuple(rootnodes[int(tree.query(origin.coords[0])[1])]);paths=[];rows=[]
 for name,prefix,region in definitions+[('Benagéber','Presa de Benagéber','design')]:
  p=Point(landmark(prefix)['xy']);assert coast.covers(p),name
  nodes=candidates(root,sector=region) if region!='design' else [reservoir_access]
  if not nodes:raise RuntimeError('No connected streets in '+region)
  end=min(nodes,key=lambda n:Point(n).distance(p));distance=Point(end).distance(p)
  assert distance<650,(name,'No local access',distance)
  path=nx.shortest_path(graph,start,end,weight='weight');line=LineString(path);paths.append(feature(line,'verified-road-route',name='Valencia → '+name,length_m=line.length));rows.append({'destination':name,'connected':True,'route_length_m':line.length,'landmark_to_road_m':distance,'junctions':len(path)})
 all_length=sum(e['weight'] for a,b,e in graph.edges(data=True));main_length=sum(e['weight'] for a,b,e in graph.subgraph(root).edges(data=True));cs=components()
 report={'sites':rows,'joins':joins,'main_component_fraction':main_length/all_length,'main_drivable_length_km':main_length/1000,'components_total':len(cs),'junction_method':'Shared OSM coordinate vertices plus explicitly constructed road endpoints, 1 cm tolerance. Geometric crossings alone do not connect.','scope':'Undirected junction graph. Turn restrictions, one-way routing and engineered ramp/bridge elevations require separate validation.'}
 write('integration-review.json',report);write('integration-routes.geojson',fc(paths));doc['features']=fs;write('isla-metros.geojson',doc);metrics=json.load(open(D/'metrics.json'));metrics['integration']=report;write('metrics.json',metrics)
 print('VERIFIED',len(rows),'routes; main network',round(main_length/all_length*100,2),'%',flush=True)

if __name__=='__main__':main()
