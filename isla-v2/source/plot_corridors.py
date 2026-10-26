import pathlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import shape
P=pathlib.Path(__file__).resolve().parents[1];features=json.load(open(P/'data/continuous-corridors.geojson'))['features'];rows=json.load(open(P/'data/corridor-review.json'));colors={'A-7':'#efbb79','V-30':'#85ccd0','V-21':'#d698be','A-3':'#d7d39a','CV-35':'#8ec799'}
fig,axs=plt.subplots(1,2,figsize=(16,10),facecolor='#102230')
for ax,stage,title in zip(axs,['source','compact'],['OSM · tramos continuos seleccionados','ISLA · rectas acortadas, giros conservados']):
 ax.set_facecolor('#203d43')
 for f in features:
  if f['properties']['stage']!=stage:continue
  g=shape(f['geometry']);ref=f['properties']['ref'];ax.plot(*g.xy,color=colors[ref],lw=2,label=ref)
 ax.set_aspect('equal');ax.set_title(title,color='#f3e5ce',pad=15);ax.tick_params(colors='#c6cfc9',labelsize=9);ax.grid(alpha=.1);ax.legend(facecolor='#213b46',labelcolor='#eee',edgecolor='none');ax.set_xlabel('Metros locales',color='#c6cfc9')
fig.suptitle('Nueva red de autovías · V-30 y nuevo cauce al sur',color='#f5e7d6',fontsize=21)
text=' · '.join(f"{r['ref']}: {r['original_m']/1000:.1f} → {r['design_m']/1000:.1f} km" for r in rows)
fig.text(.06,.065,text,color='#d0c9be',fontsize=10);fig.text(.06,.035,'Curvas OSM simplificadas a12m; A-3 comparte la compactación del aeropuerto. Colocación de diseño. No certifica radios ni rasantes. © OpenStreetMap contributors',color='#9fafb2',fontsize=9)
fig.subplots_adjust(top=.86,bottom=.15,wspace=.18);fig.savefig(P/'previews/vias-osm-comparacion.png',dpi=140,facecolor=fig.get_facecolor())
