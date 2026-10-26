"""Metric source coordinates and explicitly rigid destination settlements."""
import json,gzip,pathlib,math,sys
import numpy as np
from shapely.geometry import shape,mapping,Point,LineString,Polygon,box
from shapely.ops import transform,unary_union
from shapely.affinity import translate
from shapely import make_valid
from pyproj import Transformer
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';ROOT=P.parent;OLD=ROOT/'isla-v2/data'
T=Transformer.from_crs(4326,25830,always_xy=True).transform
ORIGIN=np.array(T(-.377,39.4735));OFFSET=np.array([3500.,3000.])
def rel(g):return translate(transform(T,shape(g)),-ORIGIN[0],-ORIGIN[1])
def xy(ll):return np.array(T(*ll))-ORIGIN
def parts(g,kind):
 if g.geom_type==kind:yield g
 elif hasattr(g,'geoms'):
  for p in g.geoms:yield from parts(p,kind)
def fc(fs):return {'type':'FeatureCollection','features':fs}
def feature(g,kind,**p):return {'type':'Feature','geometry':mapping(g),'properties':{'kind':kind,**p}}
def write(name,obj):
 data=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode();path=D/name
 path.write_bytes(gzip.compress(data,compresslevel=9,mtime=0) if name.endswith('.gz') else data)
def osm(ident):return {'w':'way/','r':'relation/','n':'node/'}[ident[0]]+ident[1:]
def height(t):
 try:return min(250,max(3,float(str(t.get('height','')).replace(' m','')))),'OSM height'
 except (ValueError,TypeError):
  try:return min(180,max(3,float(t.get('building:levels',2))*3.2)),'Levels × 3.2 m; preview'
  except (ValueError,TypeError):return 6.4,'Preview only'
# Core Valencia remains a pure translation. The narrow outer strip is outside
# the core and closes just 750 m between the airport/Manises and the city.
WEST_CUT=(-6650.,-5750.,750.)
CITY_BOX=(-.441,39.419,-.310,39.519)
PORT_BOX=(-.344,39.425,-.280,39.469)
METRO_BOXES=[CITY_BOX,PORT_BOX,(-.511,39.474,-.458,39.506),(-.474,39.485,-.451,39.504),(-.452,39.473,-.431,39.488),(-.501,39.450,-.449,39.478),(-.448,39.495,-.422,39.521),(-.414,39.397,-.371,39.434)]
def core_point(c):
 return any(a<c.x<x and b<c.y<y for a,b,x,y in [CITY_BOX,PORT_BOX])
def metro_points(points):
 p=np.asarray(points,float).copy();a,b,loss=WEST_CUT
 p[:,0]+=loss*(1-np.clip((p[:,0]-a)/(b-a),0,1));return p+OFFSET
def metro_geometry(g):
 def f(x,y,z=None):
  x,y=np.broadcast_arrays(np.asarray(x),np.asarray(y));q=metro_points(np.c_[x.ravel(),y.ravel()]);return q[:,0].reshape(x.shape),q[:,1].reshape(y.shape)
 # Include the closure boundaries so long segments do not skip a junction.
 from shapely import segmentize
 return make_valid(transform(f,segmentize(g,15)))
REGIONS={
 'metro':{'name':'Valencia y área metropolitana','box':[-.53,39.395,-.280,39.53],'zone':'valencia'},
 'albufera':{'name':'Albufera · El Saler · El Palmar','box':[-.405,39.298,-.29,39.392],'delta':(OFFSET+[0,1500]).tolist(),'zone':'albufera'},
 'chelva':{'name':'Chelva · barrios y ruta del agua','box':[-1.014,39.735,-.96,39.772],'center':[-.996,39.748],'dest':[-6200,7000],'zone':'chelva'},
 'cofrentes':{'name':'Cofrentes · valle y central','box':[-1.081,39.205,-1.041,39.243],'center':[-1.0628,39.23],'dest':[-1000,-4500],'zone':'cofrentes'},
 'jalance':{'name':'Jalance · casco completo','box':[-1.086,39.184,-1.067,39.200],'center':[-1.077,39.1915],'dest':[-500,-8500],'zone':'cofrentes'},
 'calpe':{'name':'Calpe · casco y frente marítimo','box':[.033,38.635,.060,38.656],'center':[.0445,38.6444],'dest':[3600,-15300],'zone':'sur'},
 'ifac':{'name':'Penyal d’Ifac','box':[.067,38.627,.087,38.644],'center':[.0445,38.6444],'dest':[3600,-15300],'zone':'sur'},
}
for r in REGIONS.values():
 if 'center' in r:r['delta']=(np.array(r['dest'])-xy(r['center'])).tolist()
def region_of(o):
 c=shape(o['geometry']).representative_point()
 for key,r in REGIONS.items():
  a,b,x,y=r['box']
  if a<c.x<x and b<c.y<y:
   if key=='metro':
    q=xy(c.coords[0])
    if q[0]>1000 and q[1]<-6500:return None
    major=o['tags'].get('highway') in ['motorway','trunk','primary','secondary','tertiary','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link']
    if not major and not any(w<c.x<e and s<c.y<n for w,s,e,n in METRO_BOXES):return None
   return key
 return None
def move(g,region):return metro_geometry(g) if region=='metro' else translate(g,*REGIONS[region]['delta'])
def point_at(ll,region='metro'):return list(move(Point(xy(ll)),region).coords[0])
