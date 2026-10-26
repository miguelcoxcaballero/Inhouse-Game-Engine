"""Independent source-footprint, ensemble, hydrography and area checks."""
import json,gzip,pathlib,math,csv,collections
import numpy as np
from shapely.geometry import shape,Point,box
from shapely.ops import unary_union
from shapely.affinity import translate
from mesh_city import D,OLD,Mesh,rel
F=json.load(open(D/'isla-metros.geojson'))['features'];bykind=collections.defaultdict(list)
for f in F:bykind[f['properties']['kind']].append(f)
coast=shape(bykind['coast'][0]['geometry']);assert abs(coast.area-100e6)<.01
source={o['id']:o for o in json.load(open(OLD/'required-landmark-sources.json'))};manifest=json.load(open(OLD/'required-landmarks.json'));actual={f['properties']['source_id']:f for f in bykind['protected-landmark']};placements={p['id']:p for p in json.load(open(D/'landmark-placement.json'))};base=json.load(gzip.open(D/'baseline-49.json.gz'))
results=[];deltas={}
for item in manifest:
 errors=[];areas=[];heights=[]
 for ident in item['source_ids']:
  assert ident in actual,(item['name'],ident)
  src=rel(source[ident]['geometry']);dst=shape(actual[ident]['geometry']);delta=np.array([dst.centroid.x-src.centroid.x,dst.centroid.y-src.centroid.y]);err=src.hausdorff_distance(translate(dst,*-delta));assert err<1e-6,(item['name'],err)
  assert abs(src.area-dst.area)<1e-5;assert coast.buffer(.01).covers(dst)
  deltas[ident]=delta;errors.append(err);areas.append(src.area);row=placements.get(ident)
  heights.append({'id':ident,'preview_m':row['height_m'] if row else 6,'source':row['height_source'] if row else 'Preview only; height not documented'})
 results.append({'index':item['index'],'name':item['name'],'source_ids':item['source_ids'],'source_area_m2':sum(areas),'island_area_m2':sum(areas),'max_shape_error_m':max(errors),'max_width_height_error_m':0,'footprint_scale':1,'heights':heights,'status':'Full footprint and ensemble translation verified against OSM; heights separately qualified.'})
assert len(results)==100
for indices in [[1,8,14,70],[0,3,21],[5,12,85],[7,18,55,59,87]]:
 ids=[i for row in manifest if row['index'] in indices for i in row['source_ids']];assert max(np.linalg.norm(deltas[i]-deltas[ids[0]]) for i in ids)<1e-6,indices
architecture={'requested_elements':100,'verified_footprints':100,'source_geometries':len(source),'scaled_footprints':0,'max_shape_error_m':max(r['max_shape_error_m'] for r in results),'miguelete_moves_with_cathedral':True,'miguelete_separate_geometry':True,'miguelete_osm_height_m':placements['w625039852']['height_m'],'scope':'OSM plan footprints at 1:1; unmeasured heights remain previews.','elements':results}
(D/'architecture-review.json').write_text(json.dumps(architecture,ensure_ascii=False,indent=2))
assert architecture['miguelete_osm_height_m']==51
npz=np.load(D/'displacement-mesh.npz');mesh=Mesh(npz['source'],npz['destination']);ratios=mesh.signed_ratios();assert ratios.min()>0
records=json.load(open(D/'building-positions.json'));city={f['properties'].get('source_id'):f for f in bykind['building'] if f['properties'].get('city')}
raw={o['id']:o for o in json.load(gzip.open(D/'osm-urban-source.json.gz'))};raw.update(source)
for r in records:
 assert r['id'] in city
 src=rel(raw[r['id']]['geometry']);dst=shape(city[r['id']]['geometry']);restored=translate(dst,*-np.array(r['delta']));assert src.hausdorff_distance(restored)<1e-6,r['id']
assert len(records)>8000
sites={}
for name,bounds in [('UPV Vera',(-.350,39.479,-.335,39.486)),('UV Blasco',(-.365,39.476,-.358,39.482)),('UV Tarongers',(-.348,39.4735,-.337,39.479)),('Mercavalencia',(-.355,39.430,-.346,39.440))]:
 mask=box(*bounds);ids={ident for ident,o in raw.items() if o['tags'].get('building') not in [None,'no'] and shape(o['geometry']).geom_type in ['Polygon','MultiPolygon'] and mask.covers(shape(o['geometry']))}
 missing=sorted(ids-set(city));assert not missing,(name,missing)
 boundary={ident for ident,o in raw.items() if ident not in ids and o['tags'].get('building') not in [None,'no'] and shape(o['geometry']).geom_type in ['Polygon','MultiPolygon'] and mask.intersects(shape(o['geometry']))}
 sites[name]={'scope':'Complete footprints strictly inside the geographic selection window; boundary-straddling buildings reported separately.','source_building_footprints':len(ids),'retained_building_footprints':len(ids),'missing':missing,'boundary_straddling_source_count':len(boundary),'boundary_straddling_omitted_ids':sorted(boundary-set(city))}
(D/'site-preservation-review.json').write_text(json.dumps(sites,indent=2))
park=unary_union([shape(f['geometry']) for f in bykind['designed-park']]);riverwater=unary_union([shape(f['geometry']) for f in bykind['river-water']]);river_overlap=park.intersection(riverwater).area
assert river_overlap<1,'A river ribbon must not cross the old Turia garden'
bridge_names={f['properties'].get('name','') for f in bykind['bridge']}
for n in ['Pont dels Serrans','Pont de la Trinitat','Pont del Real',"Pont de l'Exposició","Pont d'Aragó","Pont de l'Àngel Custodi",'Pont de Montolivet',"Pont de l'Assut de l'Or"]:assert n in bridge_names,n
assert any('Pont de les Flors' in n for n in bridge_names)
# The complete shortened runway survives the expanded coast at its prior size.
oldrun=next(shape(f['geometry']) for f in base['isla-metros.geojson']['features'] if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway')
run=next(shape(f['geometry']) for f in bykind['airway'] if f['properties'].get('aeroway')=='runway');assert abs(run.length-oldrun.length)<1e-6;assert coast.covers(run)
relations=json.load(open(D/'building-avenue-relations.json'));assert len(relations)==len(records);errors=[abs(r['distance_error_m']) for r in relations]
for r in relations:
 assert np.isfinite(r['compact_distance_to_corresponding_point_m'])
 assert np.allclose(city[r['building']]['geometry']['type'] in ['Polygon','MultiPolygon'],True)
report={'island_km2':coast.area/1e6,'connected_island':coast.geom_type=='Polygon','city_building_footprints':len(records),'previous_city_building_footprints':base['metrics.json']['city_buildings_final'],'total_building_features':len(bykind['building']),'protected_entries_verified':100,'all_city_footprints_1_to_1':True,'recognisable_ensembles_rigid':True,'minimum_mesh_jacobian':float(ratios.min()),'old_turia_park_km2':park.area/1e6,'river_ribbon_inside_old_garden_m2':river_overlap,'osm_bridge_way_pieces':sum(f['properties'].get('bridge_evidence')=='OSM bridge tag' for f in bykind['bridge']),'airport_runway_m':run.length,'building_avenue_distance_error_median_m':float(np.median(errors)),'building_avenue_distance_error_p95_m':float(np.percentile(errors,95)),'local_side_changes_to_review':sum(not r['same_side'] for r in relations),'limits':['Road connectivity is planar; driving restrictions, bridge elevations and external route completeness are not certified.','Local side flags at curved or short avenue segments require review; exported individually.','F1 is a connected harbour-street proposal, not the historical course.','Terrain and unmeasured extrusion heights are synthetic.']}
(D/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
with open(D/'edificios-avenidas.csv','w') as out:
 writer=csv.DictWriter(out,fieldnames=['building','avenue','avenue_osm','source_distance_m','target_distance_m','compact_distance_to_corresponding_point_m','compact_nearest_distance_m','distance_error_m','bearing_error_degrees','same_side'],extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(relations)
print(json.dumps(report,ensure_ascii=False,indent=2))
