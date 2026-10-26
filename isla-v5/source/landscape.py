"""Add 200 km² of interior country, replace suburban land cover and make relief."""
from common import *
from shapely import contains_xy,prepare,voronoi_polygons
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource,LinearSegmentedColormap

def main():
 fs=json.load(gzip.open(D/'base-features.geojson.gz'))['features'];old=shape(json.load(gzip.open(ROOT/'isla-v4/data/island-outline.geojson.gz')))
 ys=np.array([-15800,-13500,-9500,-4000,1500,6500,11500,14500]);west=np.array([1000,-4500,-8000,-11000,-12000,-11000,-6500,-2000]);yy=np.linspace(ys[0],ys[-1],300)
 protected_shore=box(6500,-3100,18000,8300);allowed=box(-45000,-30000,30000,25000).difference(protected_shore).union(old)
 def outline(width):
  xx=PchipInterpolator(ys,np.where(west<0,west*width,west))(yy)
  patch=Polygon([*zip(xx,yy),(300,13500),(0,8500),(500,-5000),(4000,-12000),(4000,-15000)]).buffer(-700,quad_segs=16).buffer(700,quad_segs=16).buffer(500,quad_segs=16).buffer(-500,quad_segs=16)
  g=old.union(patch);g=old.union(g.buffer(600,quad_segs=16).buffer(-600,quad_segs=16).intersection(allowed));return Polygon(g.exterior)
 lo,hi=.3,3.
 print('COAST RANGE',outline(lo).area/1e6,outline(hi).area/1e6,flush=True)
 assert outline(lo).area<500e6<outline(hi).area
 for _ in range(40):
  mid=(lo+hi)/2
  if outline(mid).area<500e6:lo=mid
  else:hi=mid
 coast=outline((lo+hi)/2);assert abs(coast.area-500e6)<.1 and old.difference(coast).area<1e-4
 write('island-outline.geojson.gz',mapping(coast));write('layout.json',{'island':mapping(coast)})
 fs.append(feature(coast,'coast',name='Isla Levante · 500 km²'))
 masks=json.load(gzip.open(D/'preservation-mask.geojson.gz'))['features'];keep=shape(next(f['geometry'] for f in masks if f['properties']['kind']=='urban-retention'));released=shape(next(f['geometry'] for f in masks if f['properties']['kind']=='reclaimed-suburbs'))
 water=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind'] in ['water','lake','reservoir','flood-bed']]);lake=shape(next(f['geometry'] for f in fs if f['properties']['kind']=='lake'));airport=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='airfield'])
 extent=[coast.bounds[0]-100,coast.bounds[1]-100,coast.bounds[2]+100,coast.bounds[3]+100];N=1537;X,Y=np.meshgrid(np.linspace(extent[0],extent[2],N),np.linspace(extent[3],extent[1],N));H=np.zeros_like(X)+14
 peaks=[(-10200,8500,1180,1900,2300),(-7000,11600,900,1800,1500),(-11300,1000,1150,2100,2600),(-8500,-4500,1050,2000,2500),(-5200,-10300,920,2100,2100),(-2000,-13100,1000,2300,1800),(6100,-16600,330,400,600)]
 for x,y,h,sx,sy in peaks:H+=h*np.exp(-(((X-x)/sx)**2+((Y-y)/sy)**2)/2)
 rng=np.random.default_rng(500);noise=gaussian_filter(rng.normal(size=H.shape),12);noise/=max(.01,noise.std());H+=np.clip((H-40)/500,0,1)*(35*noise+45*np.sin(X/650+Y/1200)*np.sin(Y/900))
 flat=unary_union([keep.buffer(90),airport.buffer(450),lake.buffer(500),box(6000,-14500,13000,-4500)]);mask=contains_xy(flat,X,Y);blend=gaussian_filter(mask.astype(float),5);H=H*(1-blend)+14*blend;H[mask]=14;land=contains_xy(coast,X,Y);H[~land]=0
 for f in fs:
  if f['properties']['kind'] in ['lake','reservoir','water']:H[contains_xy(shape(f['geometry']),X,Y)]=155 if f['properties']['kind']=='reservoir' else 0
 fig,ax=plt.subplots();cs=ax.contour(X,Y,H,levels=[170]);woods=[]
 for seg in cs.allsegs[0]:
  if len(seg)>5:
   g=make_valid(Polygon(seg)).intersection(coast)
   if g.area>20000:woods.append(g)
 forest=unary_union(woods).difference(keep.buffer(120)).difference(water.buffer(40));plt.close(fig)
 # Broad ecological layers go beneath the retained source detail.
 ground=coast.difference(keep).difference(water)
 fs.insert(0,feature(ground,'green',name='Campo abierto · extensión de la isla',designed_landscape=True))
 fs.append(feature(forest,'forest',name='Sierras del interior · pinares y monte',designed_landscape=True))
 fields=released.difference(forest).difference(water.buffer(25)).intersection(coast)
 sites=[]
 for x in np.arange(fields.bounds[0]-500,fields.bounds[2]+500,375):
  for y in np.arange(fields.bounds[1]-500,fields.bounds[3]+500,375):sites.append((x+rng.uniform(-110,110),y+rng.uniform(-110,110)))
 from shapely.geometry import MultiPoint
 if sites:
  for i,g in enumerate(voronoi_polygons(MultiPoint(sites),extend_to=fields.envelope).geoms):
   g=g.intersection(fields).buffer(-3)
   if g.area>500:fs.append(feature(g,'agriculture',name='Huerta y cultivos · suelo recuperado',crop=['orchard','arable','fallow'][i%3],designed_landscape=True))
 Image.fromarray(np.rint(np.maximum(H,0)*10).astype('uint16')).save(D/'altura-decimetros.png')
 cmap=LinearSegmentedColormap.from_list('levante',['#9db187','#698655','#778453','#a39870','#c5b58f']);rgb=LightSource(315,45).shade(H,cmap,vert_exag=1.2,dx=(extent[2]-extent[0])/N,dy=(extent[3]-extent[1])/N);rgb[:,:,3]=land;Image.fromarray((rgb*255).astype('uint8')).save(D/'relieve.png')
 fig,ax=plt.subplots();cs=ax.contour(X,Y,H,levels=[60,100,150,200,300,400,500,600,800,1000,1200])
 for h,segments in zip(cs.levels,cs.allsegs):
  for points in segments:
   if len(points)>3:
    g=LineString(points).simplify(12).intersection(coast)
    if not g.is_empty:fs.append(feature(g,'contour',height=int(h)))
 plt.close(fig)
 records=json.load(open(D/'building-positions.json'));metrics={'island_area_km2':coast.area/1e6,'city_buildings_final':sum(r['city'] for r in records),'total_buildings':len(records),'removed_blocks':0,'valencia_urban_envelope_km2':unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='building' and f['properties'].get('city')]).convex_hull.area/1e6,'airport_runway_m':next(shape(f['geometry']).length for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway'),'city_scale':1,'airport_closer_m':750,'albufera_closer_m':1500,'lake_area_km2':lake.area/1e6,'new_interior_km2':coast.difference(old).area/1e6,'mountain_forest_km2':forest.area/1e6,'reclaimed_fields_km2':fields.area/1e6}
 write('isla-metros.geojson',{'coordinate_system':'LOCAL_METRES_FICTIONAL',**fc(fs)});write('metrics.json',metrics);write('terrain.json',{'extent':extent,'size':N,'units':'height decimetres; XY metres','source':'Designed mountain relief, not a real DEM'});write('landscape-review.json',metrics)
 print('LANDSCAPE',json.dumps(metrics),flush=True)

if __name__=='__main__':main()
