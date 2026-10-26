"""Independent source comparison: actual-scale city, full towns and architecture."""
from common import *
from shapely import STRtree,prepare
from scipy.spatial import Delaunay
import collections,csv,hashlib

def main():
 fs=json.load(open(D/'isla-metros.geojson'))['features'];lookup={o['id']:o for o in json.load(gzip.open(D/'osm-source.json.gz'))};records=json.load(open(D/'building-positions.json'));bykind=collections.defaultdict(list)
 for f in fs:bykind[f['properties']['kind']].append(f)
 coast=shape(bykind['coast'][0]['geometry']);assert coast.geom_type=='Polygon' and abs(coast.area-300e6)<.1
 coast_cover=coast.buffer(.02);prepare(coast_cover);prepare(coast)
 city={f['properties']['source_id']:f for f in bykind['building']};assert len(city)==len(records)
 maximum=0;source_buildings={};source_core=[]
 for r in records:
  src=make_valid(rel(lookup[r['id']]['geometry']));dst=shape(city[r['id']]['geometry']);error=src.hausdorff_distance(translate(dst,*-np.array(r['delta'])));assert error<1e-6,r['id'];assert coast_cover.covers(dst),r['id'];maximum=max(maximum,error);source_buildings[r['id']]=src
  if r['city']:assert np.allclose(r['delta'],OFFSET,atol=1e-7,rtol=0);source_core.append(r)
 expected_core={o['id'] for o in lookup.values() if o['tags'].get('building') not in [None,'no'] and o['geometry']['type'] in ['Polygon','MultiPolygon'] and core_point(shape(o['geometry']).representative_point())}
 missing_core=expected_core-city.keys();assert not missing_core,('Source city buildings omitted',sorted(missing_core)[:20])
 # Verify the requested architectural set separately, including building parts.
 manifest=json.load(open(OLD/'required-landmarks.json'));actual={f['properties']['source_id']:shape(f['geometry']) for f in bykind['protected-landmark']};elements=[]
 for item in manifest:
  errors=[];area=0
  for ident in item['source_ids']:
   src=rel(lookup[ident]['geometry']);dst=actual[ident];delta=np.array(dst.centroid.coords[0])-src.centroid.coords[0];err=src.hausdorff_distance(translate(dst,*-delta));assert err<1e-6;assert abs(src.area-dst.area)<1e-5;assert coast_cover.covers(dst);area+=src.area;errors.append(err)
  elements.append({'index':item['index'],'name':item['name'],'source_ids':item['source_ids'],'footprint_scale':1,'source_area_m2':area,'island_area_m2':area,'max_shape_error_m':max(errors)})
 assert len(elements)==100
 write('architecture-review.json',{'requested_elements':100,'verified_footprints':100,'scope':'Source plan footprints at 1:1; heights without OSM measurements remain previews.','elements':elements})
 # Every city street, including main avenues and rings, is the same geometry
 # and orientation as the source, translated by the one common city offset.
 metro_mask=rel(mapping(box(*REGIONS['metro']['box']))).difference(box(1000,-20000,20000,-6500)).buffer(120)
 core_mask=unary_union([rel(mapping(box(*b))) for b in [CITY_BOX,PORT_BOX]]);island_core=translate(core_mask,*OFFSET)
 errors=[];avenues=[];named=collections.defaultdict(lambda:{'source_m':0.,'island_m':0.,'pieces':0,'max_shape_error_m':0.})
 for f in fs:
  p=f['properties']
  if p.get('sector')!='metro' or p['kind'] not in ['retained-road','urban-arterial','expressway']:continue
  src=rel(lookup[p['source_id']]['geometry']).intersection(metro_mask).intersection(core_mask);dst=shape(f['geometry']).intersection(island_core)
  if src.is_empty and dst.is_empty:continue
  expected=translate(src,*OFFSET)
  if not coast.covers(expected):expected=expected.intersection(coast)
  if expected.is_empty and dst.is_empty:continue
  err=expected.hausdorff_distance(dst);assert err<1e-5,(p.get('name'),err);errors.append(err)
  if p['roadclass'] in ['primary','secondary','tertiary']:
   avenues.append((p,src,dst));row=named[p.get('name') or p.get('ref') or 'Vía principal'];row['source_m']+=expected.length;row['island_m']+=dst.length;row['pieces']+=1;row['max_shape_error_m']=max(row['max_shape_error_m'],err)
 # Building/avenue inspection remains available and now reports actual scale.
 tree=STRtree([g for p,g,d in avenues]);relations=[]
 for r in source_core:
  c=Point(r['source']);j=int(tree.nearest(c));p,g,d=avenues[j];q=g.interpolate(g.project(c));nq=np.array(q.coords[0])+OFFSET;distance=c.distance(q)
  relations.append({'building':r['id'],'ensemble':r['ensemble'],'avenue':p['name'],'avenue_osm':p['osm'],'source_distance_m':distance,'target_distance_m':distance,'compact_distance_to_corresponding_point_m':distance,'compact_nearest_distance_m':distance,'distance_error_m':0,'bearing_error_degrees':0,'same_side':True,'source_building_xy':r['source'],'source_avenue_xy':list(q.coords[0]),'compact_building_xy':r['destination'],'compact_avenue_xy':nq.tolist()})
 pts=np.array([r['source'] for r in source_core]);tri=Delaunay(pts);edges=np.unique(np.sort(np.r_[tri.simplices[:,[0,1]],tri.simplices[:,[1,2]],tri.simplices[:,[2,0]]],axis=1),axis=0);mesh=[]
 for a,b in edges:
  mesh.append(feature(LineString([source_core[a]['destination'],source_core[b]['destination']]),'building-relation',a=source_core[a]['id'],b=source_core[b]['id'],source_distance_m=float(np.linalg.norm(pts[a]-pts[b])),bearing_error_degrees=0))
 write('building-mesh.geojson',fc(mesh));write('building-avenue-relations.json',relations)
 with open(D/'edificios-avenidas.csv','w') as out:
  fields=['building','avenue','avenue_osm','source_distance_m','compact_distance_to_corresponding_point_m','bearing_error_degrees','same_side'];w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(relations)
 garden=unary_union([shape(f['geometry']) for f in bykind['designed-park']]);water=unary_union([shape(f['geometry']) for f in bykind['river-water']]);overlap=garden.intersection(water).area;assert overlap<1,'Water in the dry Turia garden'
 bridge_names={f['properties'].get('name','') for f in bykind['bridge']}
 for name in ['Pont dels Serrans','Pont de la Trinitat','Pont del Real',"Pont de l'Exposició","Pont d'Aragó","Pont de l'Àngel Custodi",'Pont de Montolivet',"Pont de l'Assut de l'Or"]:assert name in bridge_names,name
 runway=next(shape(f['geometry']) for f in bykind['airway'] if f['properties'].get('aeroway')=='runway');assert abs(runway.length-rel(lookup['w22954021']['geometry']).length)<1e-6
 stats=json.load(open(D/'region-review.json'))
 for key in ['chelva','cofrentes','jalance','calpe','ifac','albufera']:assert stats[key]['source_buildings']==stats[key]['buildings']+stats[key].get('outer_edge_omissions',0),key
 seams=json.load(open(D/'regional-seams.json'));assert seams['foreign_building_overlaps']==0 and seams['foreign_road_building_crossings']==0
 # Full campuses, including every parent building footprint in the source.
 sites={}
 for name,b in [('UPV Vera',(-.350,39.479,-.335,39.486)),('UV Blasco',(-.365,39.476,-.358,39.482)),('UV Tarongers',(-.348,39.4735,-.337,39.479)),('Mercavalència',(-.355,39.430,-.346,39.440))]:
  ids={o['id'] for o in lookup.values() if o['tags'].get('building') not in [None,'no'] and o['geometry']['type'] in ['Polygon','MultiPolygon'] and box(*b).covers(shape(o['geometry']))};missing=ids-city.keys();assert not missing,(name,missing);sites[name]={'source_parent_buildings':len(ids),'retained':len(ids),'omitted':0}
 integration=json.load(open(D/'integration-review.json'));assert len(integration['sites'])==18 and all(s['connected'] for s in integration['sites'])
 report={'island_km2':coast.area/1e6,'city_scale':1,'city_translation_m':OFFSET.tolist(),'city_buildings':len(source_core),'all_buildings':len(records),'building_shape_error_max_m':maximum,'city_road_pieces':len(errors),'city_road_shape_error_max_m':max(errors),'protected_architectural_entries':100,'towns':stats,'campuses':sites,'airport_runway_m':runway.length,'airport_shift_toward_city_m':750,'old_turia_water_overlap_m2':overlap,'verified_destinations':18,'road_connectivity_method':integration['junction_method'],'main_component_fraction':integration['main_component_fraction'],'limits':['City means the continuous Valencia urban core and adjacent unchanged metropolitan fabric; El Saler/El Palmar are in the relocated Albufera group.','Reservoir shore is a landscape interpretation at 0.32; terrain and unmeasured heights are synthetic.','Road verification uses shared junction vertices, but not turn restrictions or directed one-way navigation.','Historic F1 route remains an interpretation.']}
 write('audit.json',report);write('avenue-review.json',dict(named));print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
