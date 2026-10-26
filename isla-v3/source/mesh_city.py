"""Rigid OSM blocks inside an elastic, orientation-checked urban mesh.

The requested scale is a target for distances, never a building scale. Ordinary
blocks are omitted where full-size parcels do not fit. Landmark ensembles have
priority. Streets and river banks share one continuous piecewise-affine field.
"""
import json, pathlib, sys, math, warnings, gzip
warnings.filterwarnings('ignore', category=DeprecationWarning)
import numpy as np
from shapely.geometry import shape, mapping, Point, box, Polygon, LineString
from shapely.ops import unary_union, transform
from shapely.affinity import translate
from shapely import STRtree, make_valid, segmentize
from scipy.spatial import Delaunay
from scipy.optimize import linprog
from scipy.interpolate import RBFInterpolator
from pyproj import Transformer

ROOT=pathlib.Path(__file__).resolve().parents[2]; OLD=ROOT/'isla-v2/data'; D=ROOT/'isla-v3/data'
from rigid_units import source_ensembles, height_info
SCALE=.82; OFFSET=np.array([700.,1500.])
T=Transformer.from_crs(4326,25830,always_xy=True).transform; ORIGIN=np.array(T(-.377,39.4735))
def rel(g):return translate(transform(T,shape(g)),-ORIGIN[0],-ORIGIN[1])
def osm(i):return ('way/' if i[0]=='w' else 'relation/' if i[0]=='r' else 'node/')+i[1:]
def parts(g,kind):
 if g.geom_type==kind:yield g
 elif hasattr(g,'geoms'):
  for p in g.geoms:yield from parts(p,kind)
def fc(fs):return {'type':'FeatureCollection','features':fs}
def feature(g,kind,**p):return {'type':'Feature','geometry':mapping(g),'properties':{'kind':kind,**p}}

class Mesh:
 def __init__(self,src,dst):
  self.src=np.asarray(src);self.dst=np.asarray(dst);self.tri=Delaunay(self.src)
 def points(self,p):
  p=np.asarray(p,float);s=self.tri.find_simplex(p);valid=s>=0;q=p*SCALE+OFFSET
  t=self.tri.transform[s[valid]];b=np.einsum('ijk,ik->ij',t[:,:2],p[valid]-t[:,2]);weights=np.c_[b,1-b.sum(axis=1)]
  q[valid]=np.einsum('ij,ijk->ik',weights,self.dst[self.tri.simplices[s[valid]]]);return q
 def xy(self,x,y,z=None):
  x,y=np.broadcast_arrays(np.asarray(x),np.asarray(y));q=self.points(np.c_[x.ravel(),y.ravel()]);return q[:,0].reshape(x.shape),q[:,1].reshape(y.shape)
 def geometry(self,g):return make_valid(transform(self.xy,segmentize(g,12)))
 def signed_ratios(self):
  a=self.src[self.tri.simplices];b=self.dst[self.tri.simplices]
  det=lambda x:np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0])
  sa,da=det(a),det(b)
  return np.where((abs(sa)<1e-5)&(abs(da)<1e-5),1.,da/sa)

def load_source():
 raw=json.load(gzip.open(D/'osm-urban-source.json.gz'));lookup={o['id']:o for o in raw}
 for o in json.load(open(OLD/'required-landmark-sources.json')):lookup[o['id']]=o
 buildings=[];roads=[];areas=[]
 for o in lookup.values():
  t=o['tags'];g=shape(o['geometry']);c=g.representative_point()
  if not(-.441<c.x<-.310 and 39.419<c.y<39.519):continue
  if t.get('building') not in [None,'no'] or t.get('building:part'):
   if g.geom_type in ['Polygon','MultiPolygon']:buildings.append((o,make_valid(rel(o['geometry']))))
  elif t.get('highway') not in [None,'construction','proposed'] or t.get('railway') in ['rail','tram']:
   if g.geom_type in ['LineString','MultiLineString']:roads.append((o,rel(o['geometry'])))
  elif g.geom_type in ['Polygon','MultiPolygon'] or t.get('waterway'):areas.append((o,make_valid(rel(o['geometry']))))
 print('SOURCE',len(buildings),'buildings',len(roads),'streets',flush=True)
 return raw,lookup,buildings,roads,areas

def prepare_units(lookup,buildings):
 units=source_ensembles(OLD,lookup,rel);bt=STRtree([g for o,g in buildings]);used=set()
 # Keep the medieval fabric as a coherent bulge, including its anonymous houses
 # and alleyways. Alboraia and Saplaya are complete neighbourhood ensembles too.
 zones=json.load(open(D/'district-source.geojson'))['features']
 oldtown=next(shape(f['geometry']) for f in zones if f['properties']['name']=='Ciutat Vella')
 contexts=[('Ciutat Vella · trama histórica',oldtown),('Alboraia · núcleo y mercado',box(1850,2750,2600,3500)),('Port Saplaya · marina y viviendas',box(4350,3800,5100,4700))]
 for label,bounds in [('UPV · campus de Vera',(-.350,39.479,-.335,39.486)),('UV · campus Blasco Ibáñez',(-.365,39.476,-.358,39.482)),('UV · campus dels Tarongers',(-.348,39.4735,-.337,39.479)),('Mercavalència · mercado y logística',(-.355,39.430,-.346,39.440))]:contexts.append((label,rel(mapping(box(*bounds)))))
 for label,mask in contexts:
  units.append({'source':mask,'required':[],'landmarks':[],'buildings':[],'label':label,'mandatory':True})
 # Each full street cell and its houses stay with the protected monument.
 for u in units:
  ids=[int(i) for i in bt.query(u['source'],predicate='intersects') if u['source'].covers(buildings[int(i)][1].representative_point())]
  u['buildings']=[buildings[i] for i in ids];u['source']=unary_union([u['source'],*[g for o,g in u['buildings']]])
  u['mandatory']=True
 # Source ensembles that share an actual house or plaza must move together.
 changed=True
 while changed:
  changed=False
  for i,a in enumerate(units):
   for j in range(i+1,len(units)):
    b=units[j]
    if a['source'].intersection(b['source']).area>2:
     a['source']=a['source'].union(b['source']);a['required']+=b['required'];a['landmarks']=list(dict(a['landmarks']+b['landmarks']).items());a['buildings']=list({o['id']:(o,g) for o,g in a['buildings']+b['buildings']}.values());a['label']=a.get('label',b.get('label'));units.pop(j);changed=True;break
   if changed:break
 for u in units:used.update(o['id'] for o,g in u['buildings']);used.update(i for i,g in u['landmarks'])
 mandatory_source=unary_union([u['source'] for u in units]);candidates=[]
 cells=json.load(open(OLD/'block-selection-source.geojson'))['features']
 for i,f in enumerate(cells):
  g=shape(f['geometry'])
  if not(120<g.area<80000) or g.intersection(mandatory_source).area>2:continue
  ids=[int(j) for j in bt.query(g,predicate='intersects') if g.covers(buildings[int(j)][1].representative_point())]
  bs=[buildings[j] for j in ids if buildings[j][0]['id'] not in used]
  if not bs:continue
  footprint=unary_union([g,*[b for o,b in bs]])
  if footprint.intersection(mandatory_source).area>2:continue
  candidates.append({'source':footprint,'cell':g,'cell_id':i,'buildings':bs,'mandatory':False,'landmarks':[],'required':[]})
 return units,candidates,len(cells)

def place_mandatory(units):
 n=len(units);src=np.array([[u['source'].centroid.x,u['source'].centroid.y] for u in units]);target=src*SCALE+OFFSET
 bounds=np.array([u['source'].bounds for u in units]);lo=bounds[:,:2]-src;hi=bounds[:,2:]-src
 # L1 projection onto geographic separation constraints. Source axis direction
 # determines the separating side; no unrelated nearest-empty-hole placement.
 rows=[];rhs=[]
 for i in range(n):
  for j in range(i+1,n):
   d=src[j]-src[i];gaps=np.array([max(bounds[j,k]-bounds[i,k+2],bounds[i,k]-bounds[j,k+2]) for k in [0,1]])
   if max(gaps)<0:continue  # nonconvex neighbours: exact collision check below
   k=int(np.argmax(gaps/np.maximum(abs(d),1)));sign=1 if d[k]>0 else -1
   distance=(hi[i,k]-lo[j,k] if sign>0 else hi[j,k]-lo[i,k])+3
   row=np.zeros(n*4);row[k*n+i]=sign;row[k*n+j]=-sign;rows.append(row);rhs.append(-distance)
 for j,t in enumerate(target.T.ravel()):
  row=np.zeros(n*4);row[j]=1;row[2*n+j]=-1;rows.append(row);rhs.append(t)
  row=np.zeros(n*4);row[j]=-1;row[2*n+j]=-1;rows.append(row);rhs.append(-t)
 result=linprog(np.r_[np.zeros(n*2),np.ones(n*2)],A_ub=np.array(rows),b_ub=rhs,bounds=[(None,None)]*(n*2)+[(0,None)]*(n*2),method='highs')
 if not result.success:raise RuntimeError(result.message)
 dst=result.x[:2*n].reshape(2,n).T
 for i,u in enumerate(units):u['delta']=dst[i]-src[i];u['placed']=translate(u['source'],*u['delta'])
 for i,u in enumerate(units):
  for j in range(i+1,len(units)):
   v=units[j]
   if u['placed'].intersection(v['placed']).area>2:
    # Interlocking historic parcels cannot be separated by a bounding-box axis.
    # Treat them as a larger recognisable rigid neighbourhood, a local bulge.
    u['source']=u['source'].union(v['source']);u['required']+=v['required'];u['landmarks']=list(dict(u['landmarks']+v['landmarks']).items());u['buildings']=list({o['id']:(o,g) for o,g in u['buildings']+v['buildings']}.values());u['label']=u.get('label',v.get('label'));units.pop(j)
    return place_mandatory(units)
 frame=np.array([[-7000,-7000],[7000,-7000],[7000,7000],[-7000,7000]])
 field=RBFInterpolator(np.r_[src,frame],np.r_[dst,frame*SCALE+OFFSET],smoothing=1200)
 return field

def mesh_controls(units):
 src=[];dst=[];owner=[];seen=set()
 for i,u in enumerate(units):
  coords=[]
  for p in parts(u['source'],'Polygon'):
   coords+=list(segmentize(p.exterior,45).coords)[:-1]
   for ring in p.interiors:coords+=list(segmentize(ring,45).coords)[:-1]
  coords+=[[g.centroid.x,g.centroid.y] for o,g in u['buildings']]
  for p in coords:
   key=tuple(np.round(p,3))
   if key in seen:continue
   seen.add(key);src.append(p);dst.append(np.array(p)+u['delta']);owner.append(i)
 # Exterior anchors preserve the city envelope and prevent unconstrained extrapolation.
 for x in np.linspace(-7000,7000,30):
  for p in [(x,-7000),(x,7000),(-7000,x),(7000,x)]:
   key=tuple(p)
   if key not in seen:seen.add(key);src.append(p);dst.append(np.array(p)*SCALE+OFFSET);owner.append(-1)
 return Mesh(src,dst),np.asarray(owner)

def build_layout(lookup,buildings):
 mandatory,candidates,total=prepare_units(lookup,buildings)
 for iteration in range(30):
  field=place_mandatory(mandatory);mm,owners=mesh_controls(mandatory);bad=np.where(mm.signed_ratios()<=.012)[0]
  if not len(bad):break
  pairs=[]
  for tri in mm.tri.simplices[bad]:
   ids=sorted({int(owners[v]) for v in tri if owners[v]>=0})
   if len(ids)>1:pairs.append(ids)
  if not pairs:raise RuntimeError('Degenerate mandatory mesh')
  ids=pairs[0];u=mandatory[ids[0]]
  for j in reversed(ids[1:]):
   v=mandatory.pop(j);u['source']=u['source'].union(v['source']);u['required']+=v['required'];u['landmarks']=list(dict(u['landmarks']+v['landmarks']).items());u['buildings']=list({o['id']:(o,g) for o,g in u['buildings']+v['buildings']}.values());u['label']=u.get('label',v.get('label'))
  print('PROTECTED mesh · merge neighbouring ensembles',len(mandatory),flush=True)
 else:raise RuntimeError('Protected mesh did not converge')
 units=list(mandatory);occupied=[u['placed'].buffer(2) for u in units];used={o['id'] for u in units for o,g in u['buildings']}
 # Dense medieval and residential blocks take precedence over peripheral lots.
 candidates.sort(key=lambda u:(0 if abs(u['source'].centroid.x)<1100 and -1100<u['source'].centroid.y<900 else 1,-sum(g.area for o,g in u['buildings'])/u['source'].area,-len(u['buildings'])))
 fixed=STRtree(occupied);recent=[]
 for u in candidates:
  if any(o['id'] in used for o,g in u['buildings']):continue
  c=np.array([u['source'].centroid.x,u['source'].centroid.y]);delta=field(c[None,:])[0]-c;placed=translate(u['source'],*delta)
  if len(fixed.query(placed,predicate='intersects')) or any(g.intersects(placed) for g in recent):continue
  u['delta']=delta;u['placed']=placed;units.append(u);recent.append(placed.buffer(2));used.update(o['id'] for o,g in u['buildings'])
  if len(recent)>=80:occupied+=recent;recent=[];fixed=STRtree(occupied)
 print('SELECTED',len(units),'rigid ensembles',sum(len(u['buildings']) for u in units),'buildings',flush=True)
 removed=0
 # A positive triangle Jacobian is required: no folded streets or swapped sides.
 for iteration in range(45):
  mesh,owner=mesh_controls(units);ratios=mesh.signed_ratios();bad=np.where(ratios<=.012)[0]
  if not len(bad):break
  scores={}
  for t in mesh.tri.simplices[bad]:
   ids={int(owner[v]) for v in t if owner[v]>=0 and not units[owner[v]]['mandatory']}
   for i in ids:scores[i]=scores.get(i,0)+1
  if not scores:raise RuntimeError('Mandatory mesh folds; revise ensemble layout')
  # Remove the most implicated unprotected blocks, then triangulate again.
  discard=set(sorted(scores,key=lambda i:(-scores[i],len(units[i]['buildings'])))[:max(1,len(scores)//5)])
  units=[u for i,u in enumerate(units) if i not in discard];removed+=len(discard)
  print('MESH',iteration,'folds',len(bad),'omit',len(discard),flush=True)
 else:raise RuntimeError('Mesh has not converged')
 print('MESH valid',len(mesh.src),'points',len(mesh.tri.simplices),'triangles; minimum Jacobian',float(ratios.min()),flush=True)
 return units,mesh,{'target_distance_factor':SCALE,'selected_ensembles':len(units),'source_blocks':total,'ordinary_blocks':sum(not u['mandatory'] for u in units),'protected_ensembles':len(mandatory),'blocks_removed_to_prevent_mesh_folding':removed,'minimum_triangle_jacobian':float(ratios.min()),'triangles':len(ratios)}

def build():
 raw,lookup,buildings,roads,areas=load_source()
 from cut_layout import build_cut_layout,choose_streets
 units,mesh,review=build_cut_layout(D,OLD,lookup,buildings,rel,Mesh,parts,feature,fc)
 selected_roads,road_selection=choose_streets(roads,units);review.update(road_selection)
 fs=[];landmarks=[];placements=[];emitted=set();records=[];road_pairs=[];protected=[]
 def add(g,k,**p):
  if not g.is_empty:fs.append(feature(g,k,**p))
 for i,u in enumerate(units):
  delta=u['delta'];add(u['placed'],'city-block',city=True,ensemble=i,scale=1,source_cell=u.get('cell_id'),delta=delta.tolist(),protected=u['mandatory'])
  if u.get('label'):landmarks.append({'id':'ensemble-'+str(i),'name':u['label'],'xy':list(u['placed'].representative_point().coords[0]),'zone':'valencia','retention':'Tejido urbano conservado como conjunto a escala 1:1, incluidos edificios y calles.'})
  for o,g in u['buildings']+[(lookup[j],g) for j,g in u['landmarks']]:
   if o['id'] in emitted:continue
   emitted.add(o['id']);ng=translate(g,*delta);t=o['tags'];h,hs=height_info(t)
   if t.get('building') not in [None,'no'] or t.get('building:part') or o['id']=='w625039852':
    add(ng,'building',city=True,rigid_block=True,ensemble=i,osm=osm(o['id']),source_id=o['id'],name=t.get('name',''),height=h,height_source=hs,zone='valencia',scale=1,source='OSM · manzana íntegra 1:1 · malla elástica')
    records.append({'id':o['id'],'ensemble':i,'source':[g.centroid.x,g.centroid.y],'destination':[ng.centroid.x,ng.centroid.y],'delta':delta.tolist(),'area_m2':g.area,'shape_error_m':g.hausdorff_distance(translate(ng,*-delta))})
  for ident,g in u['landmarks']:
   ng=translate(g,*delta);h,hs=height_info(lookup[ident]['tags']);add(ng,'protected-landmark',source_id=ident,ensemble=i,source_area_m2=g.area,area_m2=ng.area,scale=1,delta=delta.tolist(),city=True);protected.append(ng)
   placements.append({'id':ident,'delta':delta.tolist(),'source_area_m2':g.area,'area_m2':ng.area,'height_m':h,'height_source':hs})
  for v in u['required']:
   g=unary_union([translate(dict(u['landmarks'])[j],*delta) for j in v['source_ids']]);add(g,'landmark-footprint',id=v['source_ids'][0],name=v['name'])
   landmarks.append({'id':v['source_ids'][0],'name':v['name'],'xy':list(g.representative_point().coords[0]),'zone':'valencia','osm':osm(v['source_ids'][0]),'required_index':v['index'],'source_ids':v['source_ids'],'scale':1,'area_before_m2':g.area,'area_after_m2':g.area,'retention':'Conjunto OSM a tamaño real, posición guiada por la malla. Huellas y distancias internas conservadas; alturas sin dato OSM aproximadas.'})
 # Every source street uses the same mesh, including its exact shared junctions.
 # The urban selection has no per-road clipping at an arbitrary district border.
 citywindow=box(-5000,-5600,5700,5000)
 selection=shape(json.load(open(D/'urban-selection-source.geojson'))['features'][0]['geometry'])
 for o,g in roads:
  if o['id'] not in selected_roads:continue
  if not citywindow.intersects(g):continue
  t=o['tags'];g=g.intersection(citywindow);ng=mesh.geometry(g);cls=t.get('highway',t.get('railway'));major=cls in ['primary','secondary','primary_link','secondary_link'] or any(x in t.get('name','') for x in ['Avinguda','Gran Via','Ronda','Bulevar'])
  kind='expressway' if cls in ['motorway','trunk','motorway_link','trunk_link'] else 'urban-arterial' if major else 'retained-road'
  if t.get('railway') and not t.get('highway'):kind='railway'
  props=dict(name=t.get('name',''),ref=t.get('ref',''),id=o['id'],osm=osm(o['id']),roadclass=cls,city=True,layer=t.get('layer','0'),bridge=t.get('bridge','no'),tunnel=t.get('tunnel','no'),source='OSM · nodos de cruce compartidos; cortes explícitos de manzanas y cierre de franjas')
  add(ng,kind,**props)
  if major:road_pairs.append((o,g,ng))
  if t.get('bridge') not in [None,'no']:add(ng,'bridge',**props,bridge_evidence='OSM bridge tag')
 # Parks retain their exact source-bank outline through the shared map field.
 river_sources=[];gardens=[]
 for o,g in areas:
  t=o['tags'];n=t.get('name','');kind=None
  if not citywindow.intersects(g):continue
  if t.get('waterway')=='river' and ('Turia' in n or 'Túria' in n):river_sources.append(g.intersection(citywindow));continue
  if g.geom_type not in ['Polygon','MultiPolygon']:continue
  if t.get('leisure') in ['park','garden','nature_reserve']:kind='designed-park' if 'Jardí del Túria' in n else 'green'
  elif t.get('leisure') in ['pitch','playground','sports_centre']:kind='sports'
  elif t.get('natural')=='water':kind='flood-bed' if 'Nuevo Cauce' in n else 'water'
  elif t.get('natural')=='beach':kind='beach'
  elif t.get('landuse') in ['industrial','commercial']:kind='industrial'
  elif t.get('landuse')=='residential':kind='urban-area'
  elif t.get('landuse') in ['farmland','orchard','allotments','plant_nursery']:kind='agriculture'
  if kind:
   if kind=='urban-area':g=g.intersection(selection)
   ng=mesh.geometry(g.intersection(citywindow));add(ng,kind,name=n,osm=osm(o['id']),city=True,source='OSM · superficie y borde guiados por la misma malla urbana')
   if kind=='designed-park':gardens.append(ng)
 if not river_sources:raise RuntimeError('No source Turia river geometry')
 river=unary_union(river_sources);bed=mesh.geometry(river.buffer(95));bank=mesh.geometry(river.buffer(116));water=mesh.geometry(river.buffer(8))
 add(bank,'flood-bank',name='Nuevo cauce del Turia · taludes',source='Eje OSM; anchura de lecho de diseño, no levantamiento hidráulico')
 add(bed,'flood-bed',name='Nuevo cauce del Turia · lecho de avenidas')
 add(water,'river-water',name='Turia · hilo de agua de referencia',source='Representación cartográfica; no caudal real')
 add(mesh.geometry(river),'river-axis',name='Nuevo cauce · eje OSM')
 # All actual road/rail intersections with the floodway receive explicit decks.
 bridges=[];old_corridor=unary_union(gardens).buffer(100)
 for f in list(fs):
  p=f['properties'];g=shape(f['geometry'])
  if p['kind'] not in ['retained-road','urban-arterial','expressway','railway']:continue
  cross=g.intersection(bank)
  old=g.intersects(old_corridor)
  if not cross.is_empty and cross.length>8 and p.get('tunnel')=='no':
   # A service path along the bed is not a bridge. Require crossing both banks.
   for part in parts(g,'LineString'):
    if part.intersects(bed) and not bed.covers(part) and part.difference(bank).geom_type=='MultiLineString':
     deck=part.intersection(bank.buffer(8));add(deck,'bridge',name=p['name'] or 'Cruce del nuevo cauce',osm=p['osm'],roadclass=p['roadclass'],city=True,bridge_evidence='OSM bridge tag' if p['bridge']!='no' else 'Crossing inferred from road and designed floodway; review required',river='new')
  if p.get('bridge')!='no' and (old or g.distance(bank)<80):bridges.append({'osm':p['osm'],'name':p['name'],'river':'old' if old else 'new','geometry':mapping(g),'roadclass':p['roadclass'],'layer':p['layer'],'source':'OSM bridge tag'})
 source_pts=np.array([r['source'] for r in records]);destination_pts=np.array([r['destination'] for r in records]);tri=Delaunay(source_pts);edges=sorted({tuple(sorted((int(a),int(b)))) for t in tri.simplices for a,b in zip(t,np.roll(t,1))})
 mesh_edges=[];angles=[];ratios=[]
 for a,b in edges:
  v=source_pts[b]-source_pts[a];w=destination_pts[b]-destination_pts[a];length=np.linalg.norm(v)
  if length<.1:continue
  angle=math.degrees(math.atan2(np.cross(v,w),np.dot(v,w)));ratio=np.linalg.norm(w)/length;angles.append(abs(angle));ratios.append(ratio)
  mesh_edges.append(feature(LineString([destination_pts[a],destination_pts[b]]),'building-relation',a=records[a]['id'],b=records[b]['id'],source_distance_m=length,destination_distance_m=np.linalg.norm(w),bearing_error_degrees=angle,rigid_group=records[a]['ensemble']==records[b]['ensemble']))
 # Avenue vertices are explicit control nodes; midpoint insertion is interpolatory
 # and therefore leaves the validated field unchanged. Store source and compact
 # positions for every building-to-avenue relationship, including the signed side.
 rt=STRtree([g for o,g,ng in road_pairs]);relations=[];avenue_points=[]
 for o,g,ng in road_pairs:
  for line in parts(segmentize(g,45),'LineString'):
   for p in list(line.coords):avenue_points.append({'osm':osm(o['id']),'source':list(p),'destination':mesh.points([p])[0].tolist()})
 for r in records:
  p=Point(r['source']);j=int(rt.nearest(p));o,g,ng=road_pairs[j]
  line=min(parts(g,'LineString'),key=lambda x:x.distance(p));s=line.project(p);q=line.interpolate(s);a=line.interpolate(max(0,s-2));b=line.interpolate(min(line.length,s+2));v=np.array(b.coords[0])-a.coords[0]
  nq=mesh.points([q.coords[0]])[0];na,nb=mesh.points([a.coords[0],b.coords[0]]);nv=nb-na;w=np.array(r['source'])-q.coords[0];nw=np.array(r['destination'])-nq
  source_side=float(np.cross(v,w));destination_side=float(np.cross(nv,nw));sd=np.linalg.norm(w);dd=np.linalg.norm(nw)
  angle=math.degrees(math.atan2(np.cross(w,nw),np.dot(w,nw))) if sd>.1 and dd>.1 else 0
  planned=float(np.linalg.norm(mesh.points([r['source']])[0]-nq))
  relations.append({'building':r['id'],'ensemble':r['ensemble'],'avenue':o['tags'].get('name',''),'avenue_osm':osm(o['id']),'source_distance_m':float(sd),'compact_distance_to_corresponding_point_m':float(dd),'compact_nearest_distance_m':float(ng.distance(Point(r['destination']))),'target_distance_m':planned,'distance_error_m':float(dd-planned),'bearing_error_degrees':angle,'same_side':bool(source_side*destination_side>=0),'source_building_xy':r['source'],'source_avenue_xy':list(q.coords[0]),'compact_building_xy':r['destination'],'compact_avenue_xy':nq.tolist()})
 # The original guidance graph includes ALL source buildings, including those
 # ultimately omitted, and avenue nodes in the same triangulation. Omitted-node
 # destinations are guidance only, not claims of a placed building.
 all_centres=np.array([[g.centroid.x,g.centroid.y] for o,g in buildings]);av=np.unique(np.round(np.array([v['source'] for v in avenue_points]),4),axis=0);all_nodes=np.r_[all_centres,av];guide=Delaunay(all_nodes)
 guide_edges=np.unique(np.sort(np.r_[guide.simplices[:,[0,1]],guide.simplices[:,[1,2]],guide.simplices[:,[2,0]]],axis=1),axis=0)
 np.savez_compressed(D/'guidance-mesh.npz',source=all_nodes,target=mesh.points(all_nodes),destination=mesh.points(all_nodes),edges=guide_edges,retained=np.r_[[o['id'] in emitted for o,g in buildings],np.ones(len(av),bool)],node_kind=np.r_[np.zeros(len(buildings),np.uint8),np.ones(len(av),np.uint8)])
 (D/'guidance-building-ids.json.gz').write_bytes(gzip.compress(json.dumps([o['id'] for o,g in buildings]).encode(),mtime=0))
 nonrigid=[abs(f['properties']['bearing_error_degrees']) for f in mesh_edges if not f['properties']['rigid_group']]
 review.update({'city_buildings':len(records),'all_source_building_mesh_nodes':len(buildings),'combined_building_avenue_mesh_nodes':len(all_nodes),'combined_mesh_edges':len(guide_edges),'building_relation_edges':len(edges),'avenue_control_nodes':len(avenue_points),'building_avenue_relations':len(relations),'same_side_fraction':sum(r['same_side'] for r in relations)/len(relations),'side_changes_to_review':sum(not r['same_side'] for r in relations),'relation_bearing_error_median_degrees':float(np.median(angles)),'relation_bearing_error_p95_degrees':float(np.percentile(angles,95)),'inter_ensemble_bearing_error_p95_degrees':float(np.percentile(nonrigid,95)),'distance_ratio_median':float(np.median(ratios)),'max_building_shape_error_m':max(r['shape_error_m'] for r in records),'method':'Explicit whole-block deletion and closure strips aligned with the crossing avenues; retained footprints translate at 1:1. The source street graph is pruned with access paths retained.','scope':'Metric footprint and planar geometry checks. No certified heights, driving restrictions or hydraulic simulation. Signed side at a short OSM way endpoint needs manual interpretation.'})
 for name,obj in [('city-mesh-review.json',review),('building-positions.json',records),('avenue-control-nodes.json',avenue_points),('building-avenue-relations.json',relations),('landmark-placement.json',placements),('river-bridges.json',bridges),('city-features.geojson',fc(fs)),('building-mesh.geojson',fc(mesh_edges)),('city-landmarks.json',landmarks)]:
  (D/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
 np.savez_compressed(D/'displacement-mesh.npz',source=mesh.src,destination=mesh.dst)
 print(json.dumps(review,indent=2),flush=True)
 return fs,landmarks,mesh,review

if __name__=='__main__':build()
