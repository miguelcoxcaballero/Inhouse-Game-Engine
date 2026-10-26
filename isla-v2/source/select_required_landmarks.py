"""Curated OSM identities. A node label alone is never treated as a building footprint."""
import json,pathlib
from shapely.geometry import shape,Point,mapping
from shapely import STRtree
from landmark_requirements import ITEMS
D=pathlib.Path(__file__).resolve().parents[1]/'data';rows={}
for fn in ['osm-nodes.json','osm-selection.json','landmark-source-areas.json','address-nodes.json']:
 if (D/fn).exists():
  for o in json.load(open(D/fn)):rows[o['id']]=o
# IDs verified against names, geometry type and geographic location in the source snapshot.
ids={0:['w23377876'],1:['w135630267'],2:['w9281502'],3:['w5007139'],4:['w23433773'],5:['w10153012'],6:['w13073736'],8:['w625039852'],9:['r14693200'],10:['w23433774'],11:['w515082661'],12:['w515256276'],13:['r11137438'],14:['w135630265'],15:['w10120283'],16:['w135638445','w165580724'],17:['w8082830'],18:['w513696236'],19:['r11026210'],20:['w514601809'],21:['w183237709'],22:['r18681030'],23:['w37523471'],24:['w150244048'],25:['w23433776'],26:['r11164787'],27:['w1286369610','w23377877'],28:['w515350925'],29:['w23377878'],30:['w23167750'],31:['w218841695'],32:['w227916537'],33:['w512378878'],34:['r18681032'],36:['r11177870','w813424045'],37:['w514000994'],38:['r8082637'],39:['w770701568','w770701567'],40:['w514894836'],42:['w150277194'],43:['r11289994'],44:['w279478350'],45:['r3865968'],46:['w661320825'],48:['r21033515'],49:['w23509879'],51:['r9603911'],52:['w239784943'],53:['w513977884'],54:['w218841696'],55:['w416210407'],56:['w1014385791'],57:['w495038787'],58:['r7286126'],59:['w416210393'],60:['w1074266732'],62:['w497514270'],63:['w1303164127'],64:['w495233207'],66:['w23433784'],67:['w15218699'],68:['w216891044'],69:['w807759872'],70:['w624143436'],71:['r8216452'],72:['r11270791'],73:['w23413021'],74:['w492626775'],75:['r12211578'],76:['w23761819'],77:['w298794518'],78:['w23761809'],79:['w15218692'],80:['w686349139'],81:['r7356910'],82:['w809242074'],83:['w495741186'],84:['w413044569'],86:['w627769637'],88:['w1550827165'],89:['w1115796656'],90:['w414889062'],91:['w493777443'],94:['w12403536'],95:['w243447549'],97:['w515327993'],99:['w554720470']}
# Resolve labels with point-in-building evidence, never a nearest-building guess.
bs=[o for o in rows.values() if o['tags'].get('building') not in [None,'no'] and shape(o['geometry']).geom_type in ['Polygon','MultiPolygon']];gs=[shape(o['geometry']) for o in bs];tree=STRtree(gs)
labelnodes={7:'n12335957118',41:'n13198848139',47:'n12248484372'}
for index,node in labelnodes.items():
 if node not in rows:continue
 pt=shape(rows[node]['geometry']);hits=tree.query(pt,predicate='intersects');matches=sorted([bs[int(j)] for j in hits],key=lambda o:shape(o['geometry']).area)
 if matches:ids[index]=[matches[0]['id']]
 print('CONTAINING',index,node,[(o['id'],o['tags']) for o in matches])
# Exact source barracas in El Palmar, not unrelated names elsewhere in Valencia.
ids[96]=[o['id'] for o in rows.values() if 'barraca' in o['tags'].get('name','').lower() and o['tags'].get('building') and -.322<shape(o['geometry']).representative_point().x<-.312 and 39.30<shape(o['geometry']).representative_point().y<39.32]
if (D/'required-landmark-overrides.json').exists():ids.update({int(k):v for k,v in json.load(open(D/'required-landmark-overrides.json')).items()})
manifest=[];selected={}
for i,(name,_) in enumerate(ITEMS):
 selected_ids=ids.get(i,[]);sources=[rows[id] for id in selected_ids if id in rows]
 for o in sources:selected[o['id']]=o
 manifest.append({'index':i,'name':name,'source_ids':[o['id'] for o in sources],'status':'source-footprint-identified' if sources else 'needs-source-identification','evidence':'Named OSM area or documented address with point-in-building match; see research/edificios-escala-real.md.','source_centres':[[shape(o['geometry']).representative_point().x,shape(o['geometry']).representative_point().y] for o in sources]})
(D/'required-landmarks.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(D/'required-landmark-sources.json').write_text(json.dumps(list(selected.values()),ensure_ascii=False,separators=(',',':')))
print('IDENTIFIED',sum(bool(x['source_ids']) for x in manifest),'/',len(manifest));print('MISSING',[(x['index'],x['name']) for x in manifest if not x['source_ids']])
