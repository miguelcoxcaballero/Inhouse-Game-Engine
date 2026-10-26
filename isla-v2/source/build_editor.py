"""Package the review editor against a fixed, already rendered map snapshot.
Does not rebuild the unfinished geography pipeline or change its source data.
"""
import pathlib,re,hashlib,json,gzip,base64
P=pathlib.Path(__file__).resolve().parents[1]
base=(P/'isla-levante-v2.html').read_text()
payload=re.search(r'<script[^>]+id="payload"[^>]*>(.*?)</script>',base,re.S).group(1).strip()
digest=hashlib.sha256(payload.encode()).hexdigest()
meta={'base_id':'isla-levante-'+digest[:16],'payload_sha256':digest,'editor_version':1,'coordinate_system':'LOCAL_METRES_FICTIONAL'}
css=(P/'source/editor.css').read_text();ui=(P/'source/editor.html').read_text();js=(P/'source/editor.js').read_text().replace('__EDITOR_META__',json.dumps(meta))
base=base.replace('<title>Isla Levante · V02 · 49 km²</title>','<title>Levante · Editor de sugerencias</title>')
base=base.replace('function showPlace(l,fly=true){if(!ready)return;', 'function showPlace(l,fly=true){if(!ready||window.levanteEditorActive)return;')
base=base.replace('</head>','<style>'+css+'</style></head>')
base=base.replace('</body>',ui+'<script>'+js.replace('</script','<\\/script')+'</script></body>')
path=P/'isla-levante-editor.html';path.write_text(base)
(P/'data/editor-manifest.json').write_text(json.dumps({**meta,'html_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'html_bytes':path.stat().st_size},indent=2))
print(path,path.stat().st_size,'bytes; base',meta['base_id'])
