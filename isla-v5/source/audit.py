"""Compare V5 independently to the audited 1:1 V4 geometry and fixed city masks."""
from common import *
from shapely import prepare
import collections,csv
BASE=ROOT/'isla-v4/data'

def main():
 fs=json.load(open(D/'isla-metros.geojson'))['features'];old=json.load(gzip.open(BASE/'isla-metros.geojson.gz'))['features'];records=json.load(open(D/'building-positions.json'));bykind=collections.defaultdict(list)
 for f in fs:bykind[f['properties']['kind']].append(f)
 coast=shape(bykind['coast'][0]['geometry']);assert coast.is_valid and abs(coast.area-500e6)<.1
 cover=coast.buffer(.02);prepare(cover)
 prior={f['properties']['source_id']:f for f in old if f['properties']['kind']=='building'};buildings={f['properties']['source_id']:f for f in bykind['building']};assert len(buildings)==len(records)
 maximum=0
 for ident,f in buildings.items():
  g=shape(f['geometry']);b=shape(prior[ident]['geometry']);error=b.hausdorff_distance(g);assert error<1e-8,ident;assert abs(g.area-b.area)<1e-5;assert cover.covers(g),ident;maximum=max(maximum,error)
 masks=json.load(gzip.open(D/'preservation-mask.geojson.gz'))['features'];fixed=unary_union([shape(f['geometry']) for f in masks if f['properties']['kind'] in ['valencia-core','preserved-enclave']]);prepare(fixed)
 preservation={}
 for f in masks:
  if f['properties']['kind'] not in ['valencia-core','preserved-enclave']:continue
  mask=shape(f['geometry']);prepare(mask);ids={i for i,b in prior.items() if b['properties'].get('sector')=='metro' and mask.covers(shape(b['geometry']).representative_point())};assert ids<=buildings.keys();preservation[f['properties'].get('name','Valencia')]={'baseline_buildings':len(ids),'retained':len(ids),'removed':0}
 actual={f['properties']['source_id']:shape(f['geometry']) for f in bykind['protected-landmark']}
 architecture=json.load(open(BASE/'architecture-review.json'))
 for f in old:
  if f['properties']['kind']=='protected-landmark':assert shape(f['geometry']).equals(actual[f['properties']['source_id']])
 assert len(architecture['elements'])==100
 roadkinds={'retained-road','urban-arterial','expressway'}
 def streets(features):
  grouped=collections.defaultdict(list)
  for f in features:
   p=f['properties']
   if p.get('sector')=='metro' and p['kind'] in roadkinds:
    g=shape(f['geometry'])
    if fixed.intersects(g):grouped[p['source_id']].append(g.intersection(fixed))
  return {i:unary_union(gs) for i,gs in grouped.items()}
 src=streets(old);dst=streets(fs);roaderror=0
 for i,g in src.items():
  assert i in dst,('Missing city street',i);err=g.hausdorff_distance(dst[i]);assert err<1e-5,(i,err);roaderror=max(roaderror,err)
 # Original relations remain valid: every retained building and city avenue is unmoved.
 cityids={r['id'] for r in records if r['city']};relations=[r for r in json.load(gzip.open(BASE/'building-avenue-relations.json.gz')) if r['building'] in cityids]
 mesh=json.load(gzip.open(BASE/'building-mesh.geojson.gz'));mesh['features']=[f for f in mesh['features'] if f['properties']['a'] in cityids and f['properties']['b'] in cityids]
 write('building-avenue-relations.json',relations);write('building-mesh.geojson',mesh)
 garden=unary_union([shape(f['geometry']) for f in bykind['designed-park']]);water=unary_union([shape(f['geometry']) for f in bykind['river-water']]);overlap=garden.intersection(water).area;assert overlap<1
 bridge_names={f['properties'].get('name','') for f in bykind['bridge']}
 for name in ['Pont dels Serrans','Pont de la Trinitat','Pont del Real',"Pont de l'Exposició","Pont d'Aragó","Pont de l'Àngel Custodi",'Pont de Montolivet',"Pont de l'Assut de l'Or"]:assert name in bridge_names,name
 for kind in ['airway','airfield']:
  a=[f['geometry'] for f in old if f['properties']['kind']==kind];b=[f['geometry'] for f in bykind[kind]];assert a==b
 runway=next(shape(f['geometry']) for f in bykind['airway'] if f['properties'].get('aeroway')=='runway')
 lake=shape(bykind['lake'][0]['geometry']);oldlake=shape(next(f['geometry'] for f in old if f['properties']['kind']=='lake'));assert abs(lake.area/oldlake.area-.5)<1e-10
 assert lake.difference(oldlake).area<1e-5
 for f in bykind['building']:
  g=shape(f['geometry'])
  if lake.intersects(g):assert lake.intersection(g).area<1,('Lake over building',f['properties']['source_id'])
 rural=json.load(open(D/'rural-revision.json'));assert len(prior)-len(buildings)==rural['suburban_buildings_removed']>20000;assert rural['alfafar_commercial_zone']['after']<rural['alfafar_commercial_zone']['before']*.05
 integration=json.load(open(D/'integration-review.json'));assert len(integration['sites'])==18 and all(r['connected'] for r in integration['sites'])
 scenic=json.load(open(D/'scenic-road-review.json'));assert len(scenic['segments'])==9 and scenic['total_km']>50
 report={'island_km2':coast.area/1e6,'city_scale':1,'all_buildings':len(buildings),'fixed_buildings':len(cityids),'preserved':preservation,'building_shape_error_vs_v4_m':maximum,'city_streets_verified':len(src),'city_street_shape_error_vs_v4_m':roaderror,'protected_architectural_entries':100,'airport_runway_m':runway.length,'old_turia_water_overlap_m2':overlap,'suburban_buildings_removed':rural['suburban_buildings_removed'],'alfafar_commercial_zone':rural['alfafar_commercial_zone'],'lake_area_km2':lake.area/1e6,'lake_area_ratio':lake.area/oldlake.area,'verified_destinations':18,'main_component_fraction':integration['main_component_fraction'],'new_scenic_roads_km':scenic['total_km'],'source_baseline':'isla-v4/data/audit.json; unchanged retained geometry, plus actual Valencia neighbourhood mask','limits':['Connectivity is undirected; road grade, turn restrictions and one-way navigation are not yet engineered.','Terrain is designed, not a surveyed DEM.','Historic F1 course remains an interpretation; unmeasured building heights remain previews.']}
 write('audit.json',report);print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
