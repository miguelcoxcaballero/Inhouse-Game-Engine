"""Keep the real V-11/N-220 airport approach and A-3 interchange arrangement."""
import json
from shapely.geometry import shape,mapping,Point,LineString,box
from shapely.ops import transform,unary_union,nearest_points
from shapely.affinity import affine_transform
from corridor_paths import get_path,compact

def add_airport_access(D,fs,landmarks,coast,runway,bed,routes,tr,add,record,curve):
 meta=json.load(open(D/'airport-layout.json'));M=meta['matrix'];raw=json.load(open(D/'osm-selection.json'));access=[];north=[]
 for o in raw:
  t=o['tags'];p=shape(o['geometry']).representative_point();ref=t.get('ref','');cls=t.get('highway','')
  keep=ref in ['V-11','N-220'] or cls.endswith('_link') and -.49<p.x<-.451 and 39.475<p.y<39.498
  if not keep:continue
  g=affine_transform(transform(tr,shape(o['geometry'])),M).intersection(box(-4000,-1800,600,1600)).intersection(coast)
  if g.is_empty:continue
  # V-11 is freeway access; N-220 is the northern Manises approach.
  add(g,'expressway' if ref=='V-11' or cls.endswith('_link') else 'secondary-road',name=ref or 'Enlace aeroportuario OSM',ref=ref,source='OSM · accesos y enlaces del aeropuerto, misma transformación que el recinto',osm_ids=o['id'])
  access.append(g)
  if ref=='N-220':north.append(g)
 for ref in ['V-11','N-220']:
  gs=[shape(f['geometry']) for f in fs if f['properties'].get('ref')==ref]
  if gs:record(ref+' · acceso del aeropuerto',unary_union(gs),note='Trazado OSM de acceso aeroportuario recompuesto junto al recinto. N-220 conecta hacia Manises y V-11 hacia A-3; no certifica giros ni estado operativo.')
 # Join opposite A-3 carriageway ends at the same retained interchange.
 if access:
  a,b=nearest_points(unary_union(access),routes['A-3'])
  if a.distance(b)>1 and a.distance(b)<220:
   g=curve([list(a.coords)[0],[(a.x+b.x)/2,(a.y+b.y)/2+min(20,a.distance(b)*.1)],list(b.coords)[0]])
   if not g.intersects(runway.buffer(100)):add(g,'new-road',name='Enlace V-11 / A-3',source='Costura corta entre calzadas OSM del mismo acceso')
 if north:
  n=unary_union(north);a=nearest_points(n,Point(-600,1600))[0];urban=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='retained-road' and f['properties'].get('city',False)]);b=nearest_points(a,urban)[1]
  source,ids,error=get_path('CV-370',(-.469,39.497),(-.452,39.490));g,m=compact(source,list(a.coords)[0],list(b.coords)[0]);add(g,'secondary-road',name='CV-370 · Manises / acceso norte',ref='CV-370',osm_ids=','.join(ids),source='Curvas OSM; empalme de diseño a N-220 y tejido metropolitano')
 # A-3 crosses the compact flood corridor by an explicit bridge, not a surface ford.
 cross=routes['A-3'].intersection(bed.buffer(25))
 if not cross.is_empty:add(cross,'bridge',name='A-3 / nuevo cauce · puente de diseño')
 graph=unary_union(access+[routes['A-3']]);meta.update({'access_ways':len(access),'access_refs':['V-11','N-220','A-3','CV-370'],'a3_airport_ground_intersection_m':routes['A-3'].intersection(shape(meta['footprint'])).length,'a3_runway_clearance_m':routes['A-3'].distance(runway),'access_runway_clearance_m':unary_union(access).distance(runway)})
 (D/'airport-layout.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 return meta
