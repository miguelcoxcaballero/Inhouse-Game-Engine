"""Spatial acceptance checks for the latest airport, shoreline and city revision."""
import json,pathlib
import numpy as np
from PIL import Image
from shapely.geometry import shape,Point
from shapely.ops import unary_union
from shapely import contains_xy
D=pathlib.Path(__file__).resolve().parents[1]/'data';F=json.load(open(D/'isla-metros.geojson'))['features'];m=json.load(open(D/'metrics.json'));coast=shape(json.load(open(D/'layout.json'))['island']);a=json.load(open(D/'airport-layout.json'));ground=shape(a['footprint'])
t=json.load(open(D/'terrain.json'));E=t['extent'];N=t['size'];X,Y=np.meshgrid(np.linspace(E[0],E[2],N),np.linspace(E[3],E[1],N));H=np.asarray(Image.open(D/'altura-decimetros.png'))/10;heights=H[contains_xy(ground,X,Y)]
beaches=[{'name':f['properties'].get('name'),'distance_to_sea_m':shape(f['geometry']).distance(coast.boundary),'area_m2':shape(f['geometry']).area} for f in F if f['properties']['kind']=='beach']
cityroads=unary_union([shape(f['geometry']) for f in F if f['properties']['kind']=='retained-road' and 'deformación continua' in f['properties'].get('source','')])
sectors=json.load(open(D/'sectors.json'));towns=[]
for id in ['mercavalencia','sedavi','alfafar','catarroja','castellar','pinedo']:
 s=next(s for s in sectors if s['id']==id);pt=Point(s['dest']);bs=[f for f in F if f['properties']['kind']=='building' and pt.distance(shape(f['geometry']))<340]
 towns.append({'name':s['name'],'whole_buildings_near_anchor':len(bs),'nearest_main_network_m':json.load(open(D/'network-review.json'))['landmark_distance_to_main_road_m'][s['name']]})
r={'previous_city_envelope_km2':5.406253563,'current_city_envelope_km2':m['valencia_urban_envelope_km2'],'city_area_ratio':m['valencia_urban_envelope_km2']/5.406253563,'selected_blocks':m['retained_blocks'],'airport_elevation_min_m':float(heights.min()),'airport_elevation_max_m':float(heights.max()),'airport_runway_m':a['runway_m'],'a3_runway_clearance_m':a['a3_runway_clearance_m'],'independent_city_roads_inside_airport_m':cityroads.intersection(ground).length,'beaches':beaches,'southern_transition':towns,'scope':'Geometry and terrain checks only; not airport certification, drivable lane navigation or resident recognition.'}
assert 1.20<r['city_area_ratio']<1.30,r
assert heights.max()-heights.min()<.2,r
assert r['independent_city_roads_inside_airport_m']<1,r
assert all(b['distance_to_sea_m']<1 for b in beaches),beaches
assert all(t['whole_buildings_near_anchor']>=5 and t['nearest_main_network_m']<80 for t in towns),towns
assert a['a3_airport_ground_intersection_m']<1,a
(D/'revision-review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
