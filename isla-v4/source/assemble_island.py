"""Fit landscape around unchanged urban footprints; only empty coast is adjusted."""
from common import *
from shapely import contains_xy,concave_hull,segmentize
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource,LinearSegmentedColormap

def main():
 fs=json.load(gzip.open(D/'base-features.geojson.gz'))['features'];landmarks=json.load(open(D/'landmarks.json'))
 runway=next(shape(f['geometry']) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway')
 landmarks=[l for l in landmarks if l['id'] not in ['w22954021','lagoon-300']]
 landmarks.append({'id':'w22954021','name':'Pista 12/30 · aeropuerto a tamaño real','xy':list(runway.centroid.coords[0]),'zone':'valencia','osm':'way/22954021','retention':'Pista OSM completa, trasladada 750 m hacia Valencia; no se acorta.'})
 def add(g,k,**p):
  if not g.is_empty:fs.append(feature(make_valid(g),k,**p))
 # The reviewed outline is a versioned design asset. Fitting its empty
 # margins is separate from rebuilding the source city and its street graph.
 coast=shape(json.load(gzip.open(D/'island-outline.geojson.gz')))
 assert coast.geom_type=='Polygon' and abs(coast.area-300e6)<.1
 metro=[shape(f['geometry']) for f in fs if f['properties']['kind']=='building' and f['properties'].get('sector')=='metro']
 airport=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='airfield'])
 albufera=next(shape(f['geometry']) for f in fs if f['properties'].get('source_id')=='r2786392' and f['properties']['kind']=='lake')
 landmarks.append({'id':'lagoon-300','name':'L’Albufera · laguna y marjal','xy':list(albufera.representative_point().coords[0]),'zone':'albufera','osm':'relation/2786392','retention':'Contorno OSM a tamaño real, reubicado 1,5 km hacia el norte junto con El Saler y El Palmar.'})
 from shapely import prepare
 coast_cover=coast.buffer(.02);prepare(coast_cover);prepare(coast)
 write('coast-candidate.geojson',fc([feature(coast,'coast')]))
 misses=[f['properties'].get('source_id') for f in fs if f['properties']['kind'] in ['building','protected-landmark'] and not coast_cover.covers(shape(f['geometry']))]
 assert not misses,('Outside coast',misses[:15],len(misses))
 print('COAST',coast.area/1e6,coast.bounds,flush=True)
 for f in fs:
  if f['properties']['kind'] not in ['building','protected-landmark','landmark-footprint']:
   g=shape(f['geometry'])
   if not coast.covers(g):f['geometry']=mapping(g.intersection(coast))
 fs[:]=[f for f in fs if not shape(f['geometry']).is_empty];add(coast,'coast',name='Isla Levante · 300 km²')
 # Real beach geometries determine the promenade. Southern fictional links
 # are labelled as design and lie directly on the coastline.
 for name,a,b in [('Devesa · continuidad litoral',-6000,-12800),('Calpe · frente sur',-14700,-16500)]:
  points=[]
  for y in np.linspace(a,b,65):
   line=coast.intersection(LineString([(-18000,y),(18000,y)]));points.append((line.bounds[2],y))
  shore=LineString(points);add(shore.offset_curve(-30).buffer(30,cap_style=2).intersection(coast),'beach',name=name);add(shore.offset_curve(-75).intersection(coast),'promenade',name=name,source='Design shoreline path')
 # Metro stations retain their source locations inside the actual-scale city.
 transit=json.load(gzip.open(ROOT/'isla-v3/data/baseline-49.json.gz'))['transit.json']
 ll={'mislata':(-.4164,39.4755),'cid':(-.4071,39.4698),'guimera':(-.3854,39.469),'xativa':(-.377,39.4667),'colon':(-.3708,39.4704),'alameda':(-.3654,39.4749),'amistat':(-.3487,39.4709),'maritim':(-.3345,39.4668),'neptu':(-.3237,39.4621),'facultats':(-.3619,39.4789),'benimaclet':(-.3625,39.4857),'alboraia':(-.350,39.501),'empalme':(-.4057,39.5),'turia':(-.3904,39.4797),'patraix':(-.3919,39.4595),'upv':(-.3435,39.4814),'tarongers':(-.3449,39.4768),'cabanyal':(-.3288,39.471),'alacant':(-.3775,39.461),'russafa':(-.3715,39.4613),'arts':(-.3524,39.4557),'natzaret':(-.3327,39.4474),'airport':(-.473,39.489),'manises':(-.463,39.492),'bonaire':(-.490,39.469)}
 other={'cofrentes':('cofrentes',(-1.0628,39.23)),'jalance':('jalance',(-1.077,39.1915)),'saler':('albufera',(-.3327,39.383)),'calpe':('calpe',(.0445,38.6444))}
 for s in transit['stations']:
  if s['id'] in ll:s['xy']=point_at(ll[s['id']])
  elif s['id'] in other:r,p=other[s['id']];s['xy']=point_at(p,r)
  else:s['xy']=[0,-12400]
  add(Point(s['xy']),'station',name=s['name'],id=s['id'])
 st={s['id']:s for s in transit['stations']};transit['edges']=[]
 for l in transit['lines']:
  g=LineString([st[i]['xy'] for i in l['stations']]);l['length_m']=round(g.length);add(g,'regional' if l['mode']=='regional' else 'metro',name=l['id'],color=l['color'],source='Fictional service diagram; local station positions follow OSM')
  for a,b in zip(l['stations'],l['stations'][1:]):transit['edges'].append({'a':a,'b':b,'line':l['id'],'length_m':Point(st[a]['xy']).distance(Point(st[b]['xy']))})
 # Synthetic hills leave all real urban fabric and the airport on flat ground.
 extent=[coast.bounds[0]-100,coast.bounds[1]-100,coast.bounds[2]+100,coast.bounds[3]+100];N=1025;X,Y=np.meshgrid(np.linspace(extent[0],extent[2],N),np.linspace(extent[3],extent[1],N));H=np.zeros_like(X)+14
 for x,y,h,sx,sy in [(-7600,8500,850,1500,1800),(-8500,500,700,1800,2300),(-7800,-6200,650,1800,2200),(100,-12900,950,1400,1300),(6100,-16600,330,400,600)]:H+=h*np.exp(-(((X-x)/sx)**2+((Y-y)/sy)**2)/2)
 mask=contains_xy(unary_union([unary_union(metro).convex_hull.buffer(100),airport.buffer(160),albufera.buffer(150)]),X,Y);blend=gaussian_filter(mask.astype(float),6);H=H*(1-blend)+14*blend;H[mask]=14;land=contains_xy(coast,X,Y);H[~land]=0
 for f in fs:
  if f['properties']['kind'] in ['lake','reservoir','water']:H[contains_xy(shape(f['geometry']),X,Y)]=155 if f['properties']['kind']=='reservoir' else 0
 Image.fromarray(np.rint(H*10).astype('uint16')).save(D/'altura-decimetros.png');cmap=LinearSegmentedColormap.from_list('levante',['#7c9b71','#718c59','#969569','#c1b18a','#dfd2b4']);rgb=LightSource(315,45).shade(H,cmap,vert_exag=1.3,dx=(extent[2]-extent[0])/N,dy=(extent[3]-extent[1])/N);rgb[:,:,3]=land;Image.fromarray((rgb*255).astype('uint8')).save(D/'relieve.png')
 fig,ax=plt.subplots();cs=ax.contour(X,Y,H,levels=[60,100,150,200,300,400,500,600,800])
 for h,segments in zip(cs.levels,cs.allsegs):
  for points in segments:
   if len(points)>3:add(LineString(points).simplify(10).intersection(coast),'contour',height=int(h))
 plt.close(fig)
 records=json.load(open(D/'building-positions.json'));city=[r for r in records if r['city']];metrics={'island_area_km2':coast.area/1e6,'city_buildings_final':len(city),'total_buildings':len(records),'removed_blocks':0,'valencia_urban_envelope_km2':unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='building' and f['properties'].get('city')]).convex_hull.area/1e6,'airport_runway_m':next(shape(f['geometry']).length for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway'),'city_scale':1,'airport_closer_m':750,'albufera_closer_m':1500}
 write('isla-metros.geojson',{'coordinate_system':'LOCAL_METRES_FICTIONAL',**fc(fs)});write('metrics.json',metrics);write('transit.json',transit);write('layout.json',{'island':mapping(coast)});write('terrain.json',{'extent':extent,'size':N,'units':'height decimetres; XY metres','source':'Synthetic terrain, not a real DEM'});write('landmarks.json',landmarks)
 print('ASSEMBLED',len(fs),'features',flush=True)

if __name__=='__main__':main()
