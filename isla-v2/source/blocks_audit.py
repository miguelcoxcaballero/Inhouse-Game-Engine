"""Regression checks for whole-block compaction, not merely building footprints."""
import json,pathlib
from shapely.geometry import shape,Point
from shapely.affinity import translate
from shapely.ops import unary_union
from shapely import STRtree
from network_review import components
D=pathlib.Path(__file__).resolve().parents[1]/'data'
F=json.load(open(D/'isla-metros.geojson'))['features'];base=json.load(open(D/'isla-base.geojson'))['features']
source=[shape(f['geometry']) for f in json.load(open(D/'block-selection-source.geojson'))['features'] if f['properties']['action']=='retener']
B=json.load(open(D/'city-blocks.geojson'))['features'];polys=[shape(f['geometry']) for f in B];errors=[]
for f,g in zip(B,polys):
 p=f['properties'];original=source[p['block_id']];restored=translate(g,-p['delta'][0],-p['delta'][1]);errors.append(original.hausdorff_distance(restored))
count=json.load(open(D/'metrics.json'))['retained_blocks']
assert len(B)==count and max(errors)<1e-7,errors
assert sum(f['properties']['kind']=='city-block' for f in F)==count
index=STRtree(polys);overlaps=[]
for i,g in enumerate(polys):
 for j in index.query(g,predicate='intersects'):
  if j<=i:continue
  area=g.intersection(polys[j]).area
  if area>.01:overlaps.append((i,int(j),area))
assert not overlaps,overlaps
rigid=lambda rows:{f['properties']['osm']:shape(f['geometry']) for f in rows if f['properties'].get('rigid_block')}
expected,actual=rigid(base),rigid(F)
assert expected.keys()==actual.keys(),expected.keys()-actual.keys()
assert all(expected[k].equals_exact(actual[k],1e-8) for k in expected)
protected=unary_union([g.buffer(-4) for g in polys]+[g.buffer(1.4) for g in actual.values()])
repairs=[shape(f['geometry']) for f in F if f['properties'].get('network_repair')]
assert all(not g.intersects(protected) for g in repairs)
cs=components(F);main=cs[0]['geometry'];city=unary_union([shape(f['geometry']) for f in F if f['properties'].get('city') and f['properties']['kind']=='retained-road' and f['properties'].get('roadclass') not in ['footway','pedestrian','path','cycleway','steps','corridor','elevator','platform','track']])
coverage=1-city.difference(main.buffer(1.5)).length/max(1,city.length)
result={'blocks':count,'source_shape_max_error_m':max(errors),'block_overlap_pairs':len(overlaps),'rigid_city_buildings':len(actual),'rigid_buildings_changed_after_packing':0,'repairs_crossing_block_interiors':0,'city_vehicle_streets_on_main_network_fraction':coverage,'global_planar_components':len(cs),'global_main_fraction':cs[0]['length_m']/sum(c['length_m'] for c in cs),'retained_real_street_ends':'Real cul-de-sacs, paths and pedestrian areas are retained. Car connectivity does not imply pedestrian areas allow cars.','scope':'1m planar road topology; source block/building preservation at floating-point tolerance, no lane/grade certification.'}
assert coverage>.99,result
(D/'blocks-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
