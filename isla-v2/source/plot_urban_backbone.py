import json,pathlib,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from shapely.geometry import shape
D=pathlib.Path(__file__).resolve().parents[1]/'data';P=D.parent
fig,axs=plt.subplots(1,2,figsize=(16,9),facecolor='#10222b');colors={'historic':'#ec9abd','gran-via':'#f7c27e','ronda':'#8ac9df','outer':'#aec69b','radial':'#eee4c9','junction':'#9caeab'}
def lines(g):
 if g.geom_type=='LineString':yield list(g.coords)
 elif hasattr(g,'geoms'):
  for x in g.geoms:yield from lines(x)
for ax,file,title in zip(axs,['urban-backbone-source.geojson','urban-backbone.geojson'],['VALENCIA · TRAZADOS OSM','ISLA · MISMOS GIROS Y ANILLOS, MENOS DISTANCIA']):
 fs=json.load(open(D/file))['features'];ax.set_facecolor('#10222b')
 for group,color in colors.items():
  seg=[s for f in fs if f['properties']['ring']==group for s in lines(shape(f['geometry']))];ax.add_collection(LineCollection(seg,colors=color,linewidths=1.5 if group!='junction' else .6))
 ax.autoscale();ax.set_aspect('equal');ax.axis('off');
 xmin,xmax=ax.get_xlim();ymin,ymax=ax.get_ylim();bar=1000 if 'source' in file else 400;x=xmin+(xmax-xmin)*.08;y=ymin+(ymax-ymin)*.04;ax.plot([x,x+bar],[y,y],color='#f4ecdf',lw=2);ax.text(x+bar/2,y-(ymax-ymin)*.035,str(bar)+' m',color='#f4ecdf',ha='center',fontsize=9);ax.set_title(title,color='#ecede5',fontsize=12,pad=20)
 for name,label in [('Avinguda del Cid','Av. del Cid'),('Avinguda de Blasco Ibáñez','Blasco Ibáñez'),('Carrer de Guillem de Castro','Ronda histórica'),('Avinguda de Pérez Galdós','Pérez Galdós'),('Avinguda del Primat Reig','Primat Reig')]:
  gs=[shape(f['geometry']) for f in fs if f['properties']['name']==name];g=max(gs,key=lambda g:g.length);pt=g.interpolate(.5,normalized=True);ax.annotate(label,(pt.x,pt.y),xytext=(8,9),textcoords='offset points',fontsize=8,color='#ffffff',bbox={'facecolor':'#10222bdd','edgecolor':'none','pad':3})
fig.text(.5,.06,'Se acortan los ejes viarios; no se escalan manzanas ni edificios. Las anchuras de calle se representan por separado.',ha='center',color='#b3c8cb',fontsize=11)
fig.text(.5,.035,'OSM + recomposición de diseño · No valida carriles, prioridades o cruces a distinto nivel.',ha='center',color='#8ba4a9',fontsize=9)
fig.tight_layout(rect=[.02,.10,.98,.95]);fig.savefig(P/'previews/avenidas-anillos-comparacion.png',dpi=140,facecolor=fig.get_facecolor())
