"""Verify every requested architectural footprint against its OSM source."""
import json,pathlib,csv
from shapely.geometry import shape
from shapely.ops import transform
from shapely.affinity import translate,affine_transform
from pyproj import Transformer
D=pathlib.Path(__file__).resolve().parents[1]/'data';P=D.parent
tr=Transformer.from_crs(4326,25830,always_xy=True).transform;origin=tr(-.377,39.4735)
source={o['id']:o for o in json.load(open(D/'required-landmark-sources.json'))};manifest=json.load(open(D/'required-landmarks.json'));F=json.load(open(D/'isla-metros.geojson'))['features'];actual={f['properties']['source_id']:f for f in F if f['properties']['kind']=='protected-landmark'}
placements={x['id']:x for x in json.load(open(D/'landmark-placement.json'))};results=[]
for item in manifest:
 assert item['source_ids'],item
 areas_before=[];areas_after=[];shape_errors=[];width_errors=[];heights=[]
 for id in item['source_ids']:
  assert id in actual,(item['name'],id)
  src=translate(transform(tr,shape(source[id]['geometry'])),-origin[0],-origin[1]);dst=shape(actual[id]['geometry']);delta=placements[id]['delta'];restored=translate(dst,-delta[0],-delta[1]);err=src.hausdorff_distance(restored)
  assert err<1e-7,(item['name'],id,err)
  assert abs(src.area-dst.area)<1e-5,(item['name'],id)
  assert abs(src.length-dst.length)<1e-6,(item['name'],id)
  areas_before.append(src.area);areas_after.append(dst.area);shape_errors.append(err);width_errors.append(max(abs((src.bounds[i+2]-src.bounds[i])-(dst.bounds[i+2]-dst.bounds[i])) for i in [0,1]))
  heights.append({'id':id,'preview_m':placements[id]['height_m'],'source':placements[id]['height_source']})
 results.append({'index':item['index'],'name':item['name'],'source_ids':item['source_ids'],'source_area_m2':sum(areas_before),'island_area_m2':sum(areas_after),'max_shape_error_m':max(shape_errors),'max_width_height_error_m':max(width_errors),'footprint_scale':1,'heights':heights,'status':'Footprint preserved exactly; height evidence listed separately'})
assert len(results)==100
assert placements['w625039852']['delta']==placements['w135630267']['delta'],'Miguelete must remain attached to cathedral'
assert placements['w625039852']['height_m']==51
summary={'requested_elements':100,'verified_footprints':100,'source_geometries':len(source),'scaled_footprints':0,'max_shape_error_m':max(x['max_shape_error_m'] for x in results),'miguelete_separate_geometry':True,'miguelete_moves_with_cathedral':True,'miguelete_osm_height_m':51,'scope':'OSM plan footprints at full metric size. Heights from OSM where present; other extrusion heights are explicitly unverified previews, not measured architecture.','elements':results}
(D/'architecture-review.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
with open(P/'ESCALA-EDIFICIOS.csv','w') as out:
 w=csv.writer(out);w.writerow(['Elemento','IDs OSM','Superficie fuente m2','Superficie isla m2','Escala huella','Error maximo forma m','Alturas y procedencia'])
 for x in results:w.writerow([x['name'],';'.join(x['source_ids']),round(x['source_area_m2'],3),round(x['island_area_m2'],3),1,x['max_shape_error_m'],'; '.join(f"{h['id']}: {h['preview_m']}m ({h['source']})" for h in x['heights'])])
print({k:v for k,v in summary.items() if k!='elements'})
# Primary road alignments must survive the final enhancer unchanged.
backbone=json.load(open(D/'urban-backbone.geojson'))['features'];final_roads={f['properties']['id']:shape(f['geometry']) for f in F if f['properties']['kind']=='urban-arterial'}
for f in backbone:assert shape(f['geometry']).equals_exact(final_roads[f['properties']['id']],1e-8)
names={f['properties']['name'] for f in backbone}
for name in ['Avinguda del Cid','Avinguda de Blasco Ibáñez','Gran Via de Ferran el Catòlic','Avinguda de Pérez Galdós','Avinguda del Primat Reig','Carrer de Guillem de Castro']:assert name in names,name
print('Primary urban OSM alignments unchanged:',len(backbone))
