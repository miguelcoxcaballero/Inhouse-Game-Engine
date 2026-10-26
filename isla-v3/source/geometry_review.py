"""Compare actual source avenue tangents and explicitly removed source blocks."""
import json,gzip
import numpy as np
from shapely.geometry import shape,Point
from shapely import STRtree
from mesh_city import D,Mesh,rel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection,PolyCollection

def main():
 raw=json.load(gzip.open(D/'osm-urban-source.json.gz'))
 current=np.load(D/'displacement-mesh.npz');mesh=Mesh(current['source'],current['destination'])
 previous=np.load(D/'comparison-before-mesh.npz')
 old=Mesh(previous['source'],previous['destination'])
 avenues={}
 for name,label in [('Blasco Ibáñez','Blasco Ibáñez · Valencia'),('del Cid','Avenida del Cid')]:
  ways=[]
  for o in raw:
   if name not in o['tags'].get('name','') or o['tags'].get('highway') not in ['primary','secondary','tertiary']:continue
   g=rel(o['geometry'])
   if name=='Blasco Ibáñez' and not (0<g.centroid.x<4100 and -800<g.centroid.y<1400):continue
   if g.geom_type=='LineString':ways.append(g)
  def stats(field):
   angles=[]
   for g in ways:
    p=np.array(g.simplify(2).coords);q=field.points(p)
    for a,b in zip(np.diff(p,axis=0),np.diff(q,axis=0)):
     if np.linalg.norm(a)<12:continue
     angles.append(abs(np.degrees(np.arctan2(a[0]*b[1]-a[1]*b[0],np.dot(a,b)))))
   return {'length_sum_m':sum(field.geometry(g).length for g in ways),'tangent_error_median_degrees':float(np.median(angles)),'tangent_error_p95_degrees':float(np.percentile(angles,95)),'tangent_error_max_degrees':float(max(angles))}
  avenues[label]={'osm_way_ids':[o['id'] for o in raw if name in o['tags'].get('name','') and o['tags'].get('highway') in ['primary','secondary','tertiary'] and any(rel(o['geometry']).equals(g) for g in ways)],'source_length_sum_m':sum(g.length for g in ways),'previous':stats(old),'current':stats(mesh),'scope':'OSM way lengths include parallel carriageways. Tangents use source segments >12 m after 2 m simplification; Valencia Blasco excludes homonymous avenues in neighbouring towns.'}
  if name=='Blasco Ibáñez':blasco=ways
 assert avenues['Blasco Ibáñez · Valencia']['current']['tangent_error_p95_degrees']<3
 assert avenues['Avenida del Cid']['current']['tangent_error_p95_degrees']<10
 ledger=json.load(gzip.open(D/'block-removal-ledger.geojson.gz'))['features'];removed=[shape(f['geometry']) for f in ledger if f['properties']['action']=='remove-and-close'];tree=STRtree(removed)
 positions=json.load(open(D/'building-positions.json'))
 assert all(not len(tree.query(Point(r['source']),predicate='within')) for r in positions),'A deleted block still contains a retained building centre'
 before=json.load(open(D/'revision-before.json'))['metrics'];after=json.load(open(D/'metrics.json'))
 report={'avenues':avenues,'removed_complete_blocks':len(removed),'retained_building_centres_in_removed_blocks':0,'previous_urban_envelope_km2':before['valencia_urban_envelope_km2'],'current_urban_envelope_km2':after['valencia_urban_envelope_km2'],'urban_envelope_measure':'Convex hull of retained urban units, buffered 100 m in both versions.'}
 (D/'geometry-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 # Same-scale source/previous/current panels, each centred on the same avenue.
 fig,axes=plt.subplots(3,1,figsize=(16,10),facecolor='#101f2a');colors=['#e8d5a0','#ef957b','#69d9c5']
 raw_build=[rel(o['geometry']) for o in raw if o['tags'].get('building') not in [None,'no'] and o['geometry']['type'] in ['Polygon','MultiPolygon']]
 lookup={o['id']:rel(o['geometry']) for o in raw if o['tags'].get('building') not in [None,'no'] and o['geometry']['type'] in ['Polygon','MultiPolygon']}
 for i,(ax,field,title) in enumerate(zip(axes,[None,old,mesh],['OSM real · misma escala','Versión publicada anterior','Revisión · manzanas suprimidas y espacio cerrado'])):
  lines=[np.array(g.coords) if field is None else np.array(field.geometry(g).coords) for g in blasco];allp=np.concatenate(lines);centre=(allp.min(axis=0)+allp.max(axis=0))/2
  ax.set_facecolor('#162b37');ax.add_collection(LineCollection(lines,colors=colors[i],linewidths=2.2,zorder=3))
  if i==0:
   polys=[g for g in raw_build if 200<g.centroid.x<3900 and -650<g.centroid.y<1300]
  elif i==2:
   from shapely.affinity import translate
   polys=[translate(lookup[r['id']],*r['delta']) for r in positions if r['id'] in lookup and 200<r['source'][0]<3900 and -650<r['source'][1]<1300]
  else:polys=[]
  ax.add_collection(PolyCollection([np.array(p.exterior.coords) for g in polys for p in ([g] if g.geom_type=='Polygon' else g.geoms)],facecolors='#54727a',edgecolors='none',alpha=.7))
  ax.set_xlim(centre[0]-2050,centre[0]+2050);ax.set_ylim(centre[1]-650,centre[1]+650);ax.set_aspect('equal');ax.set_title(title,color='#edf2e8',loc='left',fontsize=13);ax.tick_params(colors='#a2b8bb');ax.grid(alpha=.08);ax.set_xlabel('Metros · norte arriba',color='#a2b8bb')
 fig.suptitle('Blasco Ibáñez · comparación de geometría a escala 1:1',color='white',fontsize=19,y=.99)
 fig.text(.08,.005,'OSM © OpenStreetMap contributors · La fila anterior muestra el trazado; las otras filas incluyen huellas de edificios.',color='#a2b8bb',fontsize=10)
 fig.tight_layout(rect=[0,.025,1,.96]);fig.savefig(D.parent/'previews/blasco-comparacion.png',dpi=130);plt.close(fig)
 print(json.dumps({k:v for k,v in report.items() if k!='avenues'},indent=2));print(json.dumps({k:{'old':v['previous']['tangent_error_p95_degrees'],'new':v['current']['tangent_error_p95_degrees']} for k,v in avenues.items()},indent=2))

if __name__=='__main__':main()
