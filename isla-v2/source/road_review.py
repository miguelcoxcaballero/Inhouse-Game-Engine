"""Compare bends at retained vertices of continuous OSM highway references."""
import pathlib,json
import numpy as np
from shapely.geometry import shape
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';F=json.load(open(D/'continuous-corridors.geojson'))['features'];rows=[]
def turns(c):
 v=np.diff(np.asarray(c),axis=0);a=np.arctan2(v[:,1],v[:,0]);return np.angle(np.exp(1j*np.diff(a)))
for ref in ['A-7','V-30','V-21','A-3','CV-35']:
 a=shape(next(f['geometry'] for f in F if f['properties']=={'ref':ref,'stage':'source'})).simplify(12)
 b=shape(next(f['geometry'] for f in F if f['properties']=={'ref':ref,'stage':'compact'}));u,v=turns(a.coords),turns(b.coords);assert len(u)==len(v)
 e=np.abs(np.rad2deg(np.angle(np.exp(1j*(u-v)))));rows.append({'ref':ref,'retained_turns':len(u),'max_turn_change_after_simplification_deg':float(e.max()) if len(e) else 0,'reference_m':a.length,'compact_m':b.length})
report={'method':'Continuous OSM paths;12m simplification. Main corridors contract straights preferentially; V-30 moves the central valley up to450m north and A-3 shares the airport transform.','limitation':'Angles refer only to retained vertices AFTER simplification. Final bank offsets, bridges, lane widths, driving radii and grades are not certified.','corridors':rows}
(D/'road-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
