"""Package complete OSM objects for the metropolitan area and larger villages."""
from common import *
lookup={};required={o['id'] for o in json.load(open(OLD/'required-landmark-sources.json'))}
for path in [OLD/'osm-selection.json',OLD/'landmark-source-areas.json']:
 for o in json.load(open(path)):
  if o['tags'].get('building:part') and not o['tags'].get('building') and o['id'] not in required:continue
  if region_of(o):lookup[o['id']]=o
for o in json.load(open(OLD/'reference-landmarks/additions.json')):
 if o.get('geometry') and region_of(o):lookup[o['id']]={k:o[k] for k in ['id','tags','geometry']}
for o in json.load(open(OLD/'required-landmark-sources.json')):lookup[o['id']]=o
if (D/'port-source.json.gz').exists():
 for o in json.load(gzip.open(D/'port-source.json.gz')):lookup[o['id']]=o
write('osm-source.json.gz',list(lookup.values()))
nodes=[o for o in json.load(open(OLD/'osm-nodes.json')) if region_of(o)]
write('osm-nodes.json.gz',nodes)
write('regions.json',REGIONS)
print('Packaged',len(lookup),'OSM features and',len(nodes),'named source points',flush=True)
