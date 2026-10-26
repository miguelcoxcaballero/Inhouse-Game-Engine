/* Standalone local proposal editor. Base OSM-derived geometry is immutable. */
(() => {
'use strict';
const META = __EDITOR_META__;
const R = 6378137;
const $ = id => document.getElementById(id);
const copy = value => JSON.parse(JSON.stringify(value));
const fc = features => ({type:'FeatureCollection',features});
const toLocal = p => [p[0]*Math.PI/180*R,Math.log(Math.tan(Math.PI/4+p[1]*Math.PI/360))*R];
const toMap = p => [p[0]/R*180/Math.PI,(2*Math.atan(Math.exp(p[1]/R))-Math.PI/2)*180/Math.PI];
const walkCoords = (c,fn) => typeof c[0]==='number' ? fn(c) : c.map(v=>walkCoords(v,fn));
const convert = (g,fn) => ({type:g.type,coordinates:walkCoords(g.coordinates,fn)});
const norm = s => String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const key = 'levante-editor-v1-'+META.payload_sha256;
const emptyState = () => ({building_offsets:{},streets:[],notes:''});
let map, data, records=[], byId=new Map(), state=emptyState(), selection=new Set();
let mode='buildings', draft=[], roadSelection=null, gesture=null, space=false, drawingFrame=0, noteTimer, saving=true;
let undoStack=[],redoStack=[],suppressedUntil=0;
let savedView=null;
const sourceNames=new Map();
const status = text => { $('ed-status').textContent=text; };
function bbox(g) {let out=[Infinity,Infinity,-Infinity,-Infinity];walkCoords(g.coordinates,p=>{out[0]=Math.min(out[0],p[0]);out[1]=Math.min(out[1],p[1]);out[2]=Math.max(out[2],p[0]);out[3]=Math.max(out[3],p[1]);return p;});return out;}
function center(g){const b=bbox(g);return [(b[0]+b[2])/2,(b[1]+b[3])/2];}
function area(g){const polygons=g.type==='Polygon'?[g.coordinates]:g.coordinates;return polygons.reduce((sum,poly)=>sum+poly.reduce((s,ring,i)=>{let a=0;for(let j=1;j<ring.length;j++)a+=ring[j-1][0]*ring[j][1]-ring[j][0]*ring[j-1][1];return s+(i===0?1:-1)*Math.abs(a/2);},0),0);}
function length(coords){return coords.slice(1).reduce((s,p,i)=>s+Math.hypot(p[0]-coords[i][0],p[1]-coords[i][1]),0);}
function offset(id){return state.building_offsets[id]||[0,0];}
function shiftedLocal(record,delta=offset(record.id)){return convert(record.originalLocal,p=>[p[0]+delta[0],p[1]+delta[1]]);}
function buildingFeature(record,delta=offset(record.id)){
 const changed=Math.hypot(...delta)>.0001;
 return {type:'Feature',id:record.index,geometry:changed?convert(shiftedLocal(record,delta),toMap):record.originalMap,properties:{editor_id:record.id,name:record.name,height:record.height,changed}};
}
function visibleSelected(delta=[0,0]){return [...selection].map(id=>{const r=byId.get(id),d=offset(id);return buildingFeature(r,[d[0]+delta[0],d[1]+delta[1]]);});}
function updateSelection(delta=[0,0]){
 map.setFilter('ed-buildings-fill',['!', ['in',['get','editor_id'],['literal',[...selection]]]]);
 map.getSource('ed-selected').setData(fc(visibleSelected(delta)));
 $('ed-selection-count').textContent=selection.size+' edificio'+(selection.size===1?' seleccionado':'s seleccionados');
 $('ed-selection-names').textContent=selection.size?[...selection].slice(0,8).map(id=>byId.get(id).name).join(' · ')+(selection.size>8?' · …':''):'La selección se moverá como un grupo, sin cambiar sus tamaños.';
 for(const id of ['ed-clear-selection','ed-restore-selection','ed-select-ensemble'])$(id).disabled=!selection.size;
}
function renderBuildings(){
 map.getSource('ed-buildings').setData(fc(records.map(r=>buildingFeature(r))));
 updateSelection();const ghosts=[],arrows=[];
 for(const [id,d] of Object.entries(state.building_offsets)){
  const r=byId.get(id);ghosts.push({type:'Feature',geometry:r.originalMap,properties:{editor_id:id}});
  const c=center(r.originalLocal);arrows.push({type:'Feature',geometry:{type:'LineString',coordinates:[toMap(c),toMap([c[0]+d[0],c[1]+d[1]])]},properties:{}});
 }
 map.getSource('ed-originals').setData(fc(ghosts));map.getSource('ed-movements').setData(fc(arrows));
}
function roadForm(){const width=Number($('ed-road-width').value);return {name:$('ed-road-name').value.trim().slice(0,160),road_type:$('ed-road-kind').value,width_m:Number.isFinite(width)?Math.max(1,Math.min(100,width)):10,note:$('ed-road-note').value.slice(0,3000)};}
function streetFeature(s){return {type:'Feature',geometry:{type:'LineString',coordinates:s.coordinates.map(toMap)},properties:{id:s.id,width_m:s.width_m,selected:s.id===roadSelection}};}
function renderStreets(){
 map.getSource('ed-streets').setData(fc(state.streets.map(streetFeature)));
 const draftFeatures=draft.length>1?[{type:'Feature',geometry:{type:'LineString',coordinates:draft.map(toMap)},properties:{}}]:[];
 map.getSource('ed-draft').setData(fc(draftFeatures));
 map.getSource('ed-vertices').setData(fc(draft.map(p=>({type:'Feature',geometry:{type:'Point',coordinates:toMap(p)},properties:{}}))));
 $('ed-finish-street').disabled=draft.length<2;$('ed-back-point').disabled=!draft.length;$('ed-cancel-street').disabled=!draft.length;
 $('ed-draft-info').textContent=draft.length?draft.length+' puntos · '+Math.round(length(draft))+' m de trazado':'';
 $('ed-street-count').textContent=state.streets.length;
 $('ed-street-list').replaceChildren();
 for(const s of state.streets){const b=document.createElement('button');b.setAttribute('aria-pressed',String(s.id===roadSelection));const label=document.createElement('span');label.textContent=s.name||'Calle propuesta';const meters=document.createElement('span');meters.textContent=Math.round(length(s.coordinates))+' m';b.append(label,meters);b.onclick=()=>selectStreet(s.id,true);$('ed-street-list').append(b);}
 $('ed-update-street').disabled=!roadSelection;$('ed-delete-street').disabled=!roadSelection;
}
function counters(){const n=Object.keys(state.building_offsets).length;$('ed-totals').textContent=n+' edificio'+(n===1?' movido':'s movidos')+' · '+state.streets.length+' calle'+(state.streets.length===1?' propuesta':'s propuestas');$('ed-undo').disabled=!undoStack.length;$('ed-redo').disabled=!redoStack.length;}
function persist(){
 try{localStorage.setItem(key,JSON.stringify({format:'levante-editor-state/v1',base_id:META.base_id,state,view:savedView}));saving=true;$('ed-save').textContent='Guardado en este navegador';}
 catch {saving=false;$('ed-save').textContent='Exporta la ficha para guardar';}
}
function refresh(){renderBuildings();renderStreets();counters();persist();}
function checkpoint(before){undoStack.push(before);if(undoStack.length>80)undoStack.shift();redoStack=[];refresh();}
function change(fn){const before=copy(state);fn();checkpoint(before);}
function undo(){if(!undoStack.length)return;cancelGesture();draft=[];const notes=state.notes;redoStack.push(copy(state));state=undoStack.pop();state.notes=notes;roadSelection=null;$('ed-notes').value=state.notes;refresh();status('Último cambio deshecho.');}
function redo(){if(!redoStack.length)return;cancelGesture();draft=[];const notes=state.notes;undoStack.push(copy(state));state=redoStack.pop();state.notes=notes;roadSelection=null;$('ed-notes').value=state.notes;refresh();status('Cambio rehecho.');}
function selectStreet(id,fly=false){
 if(draft.length){status('Termina o cancela el trazo actual antes de editar otra calle.');return;}
 const s=state.streets.find(s=>s.id===id);if(!s)return;roadSelection=id;setMode('street');
 $('ed-road-name').value=s.name;$('ed-road-kind').value=s.road_type;$('ed-road-width').value=s.width_m;$('ed-road-note').value=s.note;
 renderStreets();if(fly){const b=bbox({coordinates:s.coordinates,type:'LineString'});map.fitBounds([toMap([b[0],b[1]]),toMap([b[2],b[3]])],{padding:window.innerWidth>700?{top:170,bottom:80,left:380,right:80}:80,maxZoom:17,duration:300});}
 status('Edita los detalles de esta calle y pulsa Guardar detalles.');
}
function updateStreet(){if(!roadSelection||draft.length)return;const values=roadForm();const s=state.streets.find(s=>s.id===roadSelection);if(!s)return;if(Object.entries(values).every(([k,v])=>s[k]===v))return;change(()=>Object.assign(s,values));status('Detalles de la calle guardados.');}
function finishStreet(){
 if(draft.length<2)return;
 const coords=draft.filter((p,i)=>!i||Math.hypot(p[0]-draft[i-1][0],p[1]-draft[i-1][1])>.01);
 if(coords.length<2||length(coords)<.1){status('Añade otro punto separado para formar una calle.');return;}
 const form=roadForm(),id='street-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7);const before=copy(state);
 state.streets.push({...form,id,name:form.name||'Calle propuesta '+(state.streets.length+1),coordinates:copy(coords)});draft=[];roadSelection=null;checkpoint(before);
 $('ed-road-name').value='';$('ed-road-note').value='';status('Calle guardada. Puedes dibujar otra o mover edificios.');
}
function setMode(next){
 cancelGesture();mode=next;space=false;
 document.querySelectorAll('[data-ed-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.edMode===next)));
 $('ed-building-panel').hidden=next==='street'||next==='freehand';$('ed-street-panel').hidden=next!=='street'&&next!=='freehand';
 const hints={pan:'Arrastra para recorrer el mapa. Acerca con la rueda o los botones + y −.',buildings:'Pulsa un edificio y arrástralo. Mayús + clic añade o quita edificios. Arrastrar una selección mueve todo el grupo.',box:'Arrastra un recuadro sobre los edificios. Después cambia a Edificios para mover el grupo. Mayús acumula la selección.',street:'Marca puntos con clics para definir curvas y cruces. Pulsa Terminar calle o Enter para guardarla.',freehand:'Mantén pulsado y dibuja la calle. Al soltar se guarda el trazo; añade curvas siguiendo el recorrido deseado.'};
 $('ed-help').textContent=hints[next];status(hints[next]);map.getCanvas().style.cursor=next==='pan'?'grab':next==='buildings'?'default':'crosshair';
 if(['street','freehand','box'].includes(next))map.dragPan.disable();else map.dragPan.enable();
}
function localEvent(e){const r=map.getCanvas().getBoundingClientRect();const ll=map.unproject([e.clientX-r.left,e.clientY-r.top]);return toLocal([ll.lng,ll.lat]);}
function pixelEvent(e){const r=map.getCanvas().getBoundingClientRect();return [e.clientX-r.left,e.clientY-r.top];}
function hitBuilding(e){const p=pixelEvent(e);return map.queryRenderedFeatures(p,{layers:['ed-selected-fill','ed-buildings-fill']}).find(f=>byId.has(f.properties.editor_id))?.properties.editor_id;}
function setSelection(ids){selection=new Set(ids.filter(id=>byId.has(id)));updateSelection();}
function eat(e){e.preventDefault();e.stopImmediatePropagation();}
function startGesture(e,value){map.getCanvas().focus({preventScroll:true});gesture={...value,pointer:e.pointerId,startPixel:pixelEvent(e),start:localEvent(e),last:localEvent(e),moved:false};map.dragPan.disable();map.getCanvasContainer().setPointerCapture(e.pointerId);eat(e);}
function pointerDown(e){
 if(e.button!==0||space||e.isPrimary===false||mode==='pan')return;
 const additive=e.shiftKey||e.ctrlKey||e.metaKey||$('ed-add-selection').checked;
 if(mode==='buildings'){
  const id=hitBuilding(e);
  if(!id){if(e.shiftKey){startBox(e,additive);return;}setSelection([]);return;}
  if(additive){if(selection.has(id))selection.delete(id);else selection.add(id);}else if(!selection.has(id))selection=new Set([id]);
  roadSelection=null;updateSelection();renderStreets();
  startGesture(e,{kind:selection.has(id)?'move':'select',before:copy(state)});return;
 }
 if(mode==='box'){startBox(e,additive);return;}
 if(mode==='street'){startGesture(e,{kind:'point'});return;}
 if(mode==='freehand'){if(draft.length){status('Termina o cancela el trazo por puntos antes de dibujar a mano.');eat(e);return;}roadSelection=null;draft=[localEvent(e)];startGesture(e,{kind:'freehand'});renderStreets();}
}
function startBox(e,additive){const node=document.createElement('div');node.className='ed-box';map.getCanvasContainer().append(node);startGesture(e,{kind:'box',node,additive});}
function pointerMove(e){
 if(!gesture){if(mode==='buildings'&&!space)map.getCanvas().style.cursor=hitBuilding(e)?'move':'grab';return;}
 if(e.pointerId!==gesture.pointer)return;eat(e);gesture.last=localEvent(e);const px=pixelEvent(e);gesture.moved ||= Math.hypot(px[0]-gesture.startPixel[0],px[1]-gesture.startPixel[1])>3;
 if(gesture.kind==='move'){
  const delta=[gesture.last[0]-gesture.start[0],gesture.last[1]-gesture.start[1]];
  if(!drawingFrame)drawingFrame=requestAnimationFrame(()=>{drawingFrame=0;if(gesture?.kind==='move'){const d=[gesture.last[0]-gesture.start[0],gesture.last[1]-gesture.start[1]];updateSelection(d);}});
  status('Moviendo '+selection.size+' edificios · este/oeste '+delta[0].toFixed(1)+' m · norte/sur '+delta[1].toFixed(1)+' m');
 }else if(gesture.kind==='box'){
  const a=gesture.startPixel;Object.assign(gesture.node.style,{left:Math.min(a[0],px[0])+'px',top:Math.min(a[1],px[1])+'px',width:Math.abs(a[0]-px[0])+'px',height:Math.abs(a[1]-px[1])+'px'});
 }else if(gesture.kind==='freehand'){
  if(Math.hypot(gesture.last[0]-draft.at(-1)[0],gesture.last[1]-draft.at(-1)[1])>1.5){draft.push(gesture.last);renderStreets();}
 }
}
function simplify(points,tolerance=1){
 if(points.length<=2)return points;const [a,b]=[points[0],points.at(-1)],dx=b[0]-a[0],dy=b[1]-a[1],den=dx*dx+dy*dy;let far=-1,index=-1;
 for(let i=1;i<points.length-1;i++){const p=points[i],t=den?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)):0,d=Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);if(d>far){far=d;index=i;}}
 if(far<=tolerance)return [a,b];return simplify(points.slice(0,index+1),tolerance).slice(0,-1).concat(simplify(points.slice(index),tolerance));
}
function releaseGesture(){const g=gesture;gesture=null;if(drawingFrame){cancelAnimationFrame(drawingFrame);drawingFrame=0;}g?.node?.remove();if(g&&map.getCanvasContainer().hasPointerCapture(g.pointer))map.getCanvasContainer().releasePointerCapture(g.pointer);if(mode==='pan'||mode==='buildings'||space)map.dragPan.enable();suppressedUntil=performance.now()+350;return g;}
function cancelGesture(){if(!gesture)return;const kind=gesture.kind;releaseGesture();if(kind==='freehand')draft=[];if(map.getSource('ed-selected')){updateSelection();renderStreets();}}
function pointerUp(e){
 if(!gesture||e.pointerId!==gesture.pointer)return;eat(e);const last=localEvent(e),px=pixelEvent(e),g=releaseGesture();
 if(g.kind==='move'&&g.moved){
  const delta=[last[0]-g.start[0],last[1]-g.start[1]];
  for(const id of selection){const d=offset(id);const total=[d[0]+delta[0],d[1]+delta[1]];if(Math.hypot(...total)<.0001)delete state.building_offsets[id];else state.building_offsets[id]=total;}
  checkpoint(g.before);status(selection.size+' edificios desplazados juntos, conservando tamaño y distancias entre ellos.');
 }else if(g.kind==='box'){
  if(g.moved){const ids=map.queryRenderedFeatures([[Math.min(g.startPixel[0],px[0]),Math.min(g.startPixel[1],px[1])],[Math.max(g.startPixel[0],px[0]),Math.max(g.startPixel[1],px[1])]],{layers:['ed-buildings-fill','ed-selected-fill']}).map(f=>f.properties.editor_id);setSelection(g.additive?[...selection,...ids]:ids);}
  status(selection.size+' edificios seleccionados. Usa Edificios para arrastrar el grupo.');
 }else if(g.kind==='point'&&!g.moved){roadSelection=null;draft.push(last);renderStreets();status('Punto añadido. Enter o Terminar calle guarda la propuesta.');
 }else if(g.kind==='freehand'){
  if(g.moved){draft.push(last);draft=simplify(draft,1);finishStreet();}else{draft=[];renderStreets();}
 }else updateSelection();
}
function snapshotProject(){
 const moves=Object.entries(state.building_offsets).map(([id,d])=>{const r=byId.get(id);return {edit_id:id,base_feature_index:r.index,osm:r.osm||null,name:r.name,ensemble:r.ensemble??null,operation:'translate',translation_m:{east:d[0],north:d[1]},original_geometry_local_m:copy(r.originalLocal),proposed_geometry_local_m:shiftedLocal(r,d),footprint_area_m2:r.area,scale:1,rotation_degrees:0};});
 return {format:'levante-feedback',schema_version:1,created_at:new Date().toISOString(),base_map:{id:META.base_id,payload_sha256:META.payload_sha256,feature_count:data.geojson.features.length,coordinate_system:'LOCAL_METRES_FICTIONAL',axes:{x:'east',y:'north'},note:'Coordenadas de la isla ficticia en metros. No son latitud/longitud ni coordenadas OSM reales.'},summary:{moved_buildings:moves.length,proposed_streets:state.streets.length,street_length_m:state.streets.reduce((n,s)=>n+length(s.coordinates),0)},general_notes:state.notes,building_moves:moves,street_suggestions:fc(state.streets.map(s=>({type:'Feature',id:s.id,geometry:{type:'LineString',coordinates:copy(s.coordinates)},properties:{name:s.name,road_type:s.road_type,width_m:s.width_m,note:s.note,length_m:length(s.coordinates),operation:'suggest_street'}}))),editor_state:copy(state),view:savedView,instructions_es:'Aplicar como sugerencias sobre la versión base indicada. Los edificios solo se trasladan, sin escalado. Las calles son propuestas dibujadas por el usuario, no datos OSM ni conexiones ya verificadas.'};
}
function validState(s){
 if(!s||typeof s!=='object'||!s.building_offsets||Array.isArray(s.building_offsets)||!Array.isArray(s.streets)||typeof s.notes!=='string')throw Error('La ficha no contiene un proyecto válido.');
 const next=emptyState();next.notes=s.notes.slice(0,12000);
 for(const [id,d] of Object.entries(s.building_offsets)){if(!byId.has(id))throw Error('La ficha incluye un edificio que no existe en este mapa.');if(!Array.isArray(d)||d.length!==2||!d.every(v=>Number.isFinite(v)&&Math.abs(v)<=100000))throw Error('Desplazamiento de edificio no válido.');if(Math.hypot(...d)>.0001)next.building_offsets[id]=d.slice();}
 if(s.streets.length>1000)throw Error('La ficha contiene demasiadas propuestas.');const ids=new Set();
 for(const s0 of s.streets){
  if(!s0||typeof s0.id!=='string'||s0.id.length>160||ids.has(s0.id)||typeof s0.name!=='string'||typeof s0.note!=='string'||!['street','avenue','highway','path'].includes(s0.road_type)||!Number.isFinite(s0.width_m)||s0.width_m<1||s0.width_m>100||!Array.isArray(s0.coordinates)||s0.coordinates.length<2||s0.coordinates.length>20000||!s0.coordinates.every(p=>Array.isArray(p)&&p.length===2&&p.every(v=>Number.isFinite(v)&&Math.abs(v)<=100000)))throw Error('Una de las calles de la ficha no es válida.');
  ids.add(s0.id);next.streets.push({id:s0.id,name:s0.name.slice(0,160),note:s0.note.slice(0,3000),road_type:s0.road_type,width_m:s0.width_m,coordinates:copy(s0.coordinates)});
 }
 return next;
}
function importProject(project){
 if(project?.format!=='levante-feedback'||project.schema_version!==1)throw Error('Selecciona una ficha JSON exportada por este editor.');
 if(project.base_map?.payload_sha256!==META.payload_sha256||project.base_map?.id!==META.base_id)throw Error('Esta ficha pertenece a otra versión del mapa. Ábrela con el HTML de esa versión para no desplazar edificios equivocados.');
 const next=validState(project.editor_state),before=copy(state);cancelGesture();state=next;selection.clear();draft=[];roadSelection=null;$('ed-notes').value=state.notes;checkpoint(before);status('Ficha importada: '+Object.keys(state.building_offsets).length+' edificios y '+state.streets.length+' calles.');
}
function downloadProject(){if(draft.length>=2)finishStreet();updateStreet();state.notes=$('ed-notes').value;persist();const project=snapshotProject();const blob=new Blob([JSON.stringify(project,null,2)],{type:'application/json;charset=utf-8'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='ficha-levante-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);status('Ficha exportada. Adjunta el archivo JSON en el chat para pasarme tus sugerencias.');}
function fitCity(){map.fitBounds([toMap([-100,-750]),toMap([2850,2380])],{padding:window.innerWidth>700?{left:380,right:70,top:175,bottom:90}:{left:25,right:55,top:185,bottom:$('ed-panel').hidden?85:innerHeight*.47},duration:0,bearing:0,pitch:0});}
function selectEnsemble(){const selected=[...selection].map(id=>byId.get(id));const ensembles=new Set(selected.filter(r=>r.ensemble!==undefined&&r.ensemble!==null).map(r=>String(r.ensemble)));const osms=new Set(selected.map(r=>r.osm).filter(Boolean));setSelection(records.filter(r=>ensembles.has(String(r.ensemble))||osms.has(r.osm)||selection.has(r.id)).map(r=>r.id));status(selection.size+' edificios seleccionados del conjunto.');}
function keyDown(e){
 if(e.target.closest('input,textarea,select,[contenteditable=true]'))return;
 if(e.code==='Space'){e.preventDefault();space=true;map.dragPan.enable();map.getCanvas().style.cursor='grab';return;}
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();e.shiftKey?redo():undo();return;}
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'){e.preventDefault();redo();return;}
 if(e.key==='Escape'){cancelGesture();if(draft.length){draft=[];renderStreets();status('Trazo cancelado.');}else{setSelection([]);roadSelection=null;renderStreets();}return;}
 if(e.key==='Enter'&&draft.length>=2){e.preventDefault();finishStreet();return;}
 if(e.key==='Backspace'&&draft.length){e.preventDefault();draft.pop();renderStreets();return;}
 if(e.key==='Delete'&&roadSelection){e.preventDefault();$('ed-delete-street').click();return;}
 if(mode==='buildings'&&selection.size&&['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)){
  e.preventDefault();const step=e.shiftKey?10:1,dx=e.key==='ArrowLeft'?-step:e.key==='ArrowRight'?step:0,dy=e.key==='ArrowDown'?-step:e.key==='ArrowUp'?step:0;
  change(()=>{for(const id of selection){const d=offset(id);state.building_offsets[id]=[d[0]+dx,d[1]+dy];}});status('Selección desplazada '+step+' m.');
 }
}
function addLayers(){
 for(const layer of ['buildings','buildings-3d','landmarks-fill','landmarks-line','poi-clusters','poi-single'])if(map.getLayer(layer))map.setLayoutProperty(layer,'visibility','none');
 for(const id of ['ed-buildings','ed-selected','ed-originals','ed-movements','ed-streets','ed-draft','ed-vertices'])map.addSource(id,{type:'geojson',data:fc([]),tolerance:0,maxzoom:20});
 map.addLayer({id:'ed-buildings-fill',type:'fill',source:'ed-buildings',minzoom:12.5,paint:{'fill-color':['case',['get','changed'],'#80c9c3','#6d7770'],'fill-opacity':.83}});
 map.addLayer({id:'ed-selected-fill',type:'fill',source:'ed-selected',paint:{'fill-color':'#e4a4cd','fill-opacity':.85}});
 map.addLayer({id:'ed-selected-line',type:'line',source:'ed-selected',paint:{'line-color':'#fff1fa','line-width':2}});
 map.addLayer({id:'ed-originals-line',type:'line',source:'ed-originals',paint:{'line-color':'#e38eae','line-width':1.5,'line-dasharray':[3,2],'line-opacity':.8}});
 map.addLayer({id:'ed-movements-line',type:'line',source:'ed-movements',paint:{'line-color':'#f5bad7','line-width':1,'line-dasharray':[2,2]}});
 map.addLayer({id:'ed-streets-casing',type:'line',source:'ed-streets',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#163b3b','line-width':7}});
 map.addLayer({id:'ed-streets-line',type:'line',source:'ed-streets',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':['case',['get','selected'],'#fff2b3','#7cf0d2'],'line-width':4}});
 map.addLayer({id:'ed-draft-line',type:'line',source:'ed-draft',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#ffe4a3','line-width':3,'line-dasharray':[2,1]}});
 map.addLayer({id:'ed-vertices-circle',type:'circle',source:'ed-vertices',paint:{'circle-color':'#172f3a','circle-radius':4,'circle-stroke-width':2,'circle-stroke-color':'#ffe4a3'}});
}
function setup(){
 map=window.islandMap;data=window.islandData;document.body.classList.add('edit-workshop');window.levanteEditorActive=true;
 document.getElementById('pins').checked=false;document.getElementById('pins').onchange();map.setTerrain(null);map.jumpTo({pitch:0,bearing:0});map.dragRotate.disable();map.touchZoomRotate.disableRotation();map.doubleClickZoom.disable();map.boxZoom.disable();map.keyboard.disable();
 for(const l of data.landmarks){if(l.osm)sourceNames.set(l.osm,l.name);for(const id of l.source_ids||[])sourceNames.set((id[0]==='r'?'relation/':'way/')+id.slice(1),l.name);}
 data.geojson.features.forEach((f,index)=>{if(f.properties.kind!=='building'||!['Polygon','MultiPolygon'].includes(f.geometry.type))return;const p=f.properties,id='building:'+index+':'+(p.osm||'design');const originalLocal=convert(f.geometry,toLocal);const record={id,index,osm:p.osm,ensemble:p.ensemble,name:sourceNames.get(p.osm)||p.name||('Edificio '+(p.osm||index)),height:p.height||9,originalMap:f.geometry,originalLocal,area:area(originalLocal)};records.push(record);byId.set(id,record);});
 addLayers();
 try{const stored=JSON.parse(localStorage.getItem(key)||'null');if(stored&&stored.base_id===META.base_id){state=validState(stored.state);if(stored.view&&Array.isArray(stored.view.center)&&stored.view.center.every(Number.isFinite)&&Number.isFinite(stored.view.zoom))savedView=stored.view;}}catch{status('No se pudo recuperar el guardado local. Puedes importar una ficha.');}
 $('ed-notes').value=state.notes;refresh();setMode('buildings');
 if(savedView)map.jumpTo({center:toMap(savedView.center),zoom:Math.max(11,Math.min(19,savedView.zoom)),pitch:0,bearing:0});else fitCity();
 map.on('moveend',()=>{const c=map.getCenter();savedView={center:toLocal([c.lng,c.lat]),zoom:map.getZoom(),bearing:0,pitch:0};persist();});
 const canvas=map.getCanvasContainer();canvas.addEventListener('pointerdown',pointerDown,{capture:true});canvas.addEventListener('pointermove',pointerMove,{capture:true});canvas.addEventListener('pointerup',pointerUp,{capture:true});canvas.addEventListener('pointercancel',cancelGesture,{capture:true});canvas.addEventListener('lostpointercapture',()=>{if(gesture)cancelGesture();});
 canvas.addEventListener('click',e=>{if(mode!=='pan'||performance.now()<suppressedUntil)eat(e);},true);canvas.addEventListener('dblclick',e=>{if(mode!=='pan')eat(e);},true);
 document.addEventListener('keydown',keyDown);document.addEventListener('keyup',e=>{if(e.code==='Space'&&space){space=false;setMode(mode);}});window.addEventListener('blur',()=>{space=false;cancelGesture();setMode(mode);});
 document.querySelectorAll('[data-ed-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.edMode));
 $('ed-undo').onclick=undo;$('ed-redo').onclick=redo;$('ed-export').onclick=downloadProject;$('ed-finish-street').onclick=finishStreet;$('ed-update-street').onclick=updateStreet;
 $('ed-back-point').onclick=()=>{draft.pop();renderStreets();};$('ed-cancel-street').onclick=()=>{draft=[];renderStreets();status('Trazo cancelado.');};
 $('ed-delete-street').onclick=()=>{if(!roadSelection)return;change(()=>{state.streets=state.streets.filter(s=>s.id!==roadSelection);roadSelection=null;});status('Propuesta de calle eliminada. Puedes deshacerlo.');};
 $('ed-clear-selection').onclick=()=>setSelection([]);$('ed-select-ensemble').onclick=selectEnsemble;
 $('ed-restore-selection').onclick=()=>{change(()=>{for(const id of selection)delete state.building_offsets[id];});status('Selección devuelta a sus posiciones originales.');};
 $('ed-show-originals').onchange=()=>{for(const id of ['ed-originals-line','ed-movements-line'])map.setLayoutProperty(id,'visibility',$('ed-show-originals').checked?'visible':'none');};
 $('ed-toggle-panel').onclick=()=>{$('ed-panel').hidden=!$('ed-panel').hidden;$('ed-toggle-panel').setAttribute('aria-expanded',String(!$('ed-panel').hidden));};
 $('ed-fit-city').onclick=fitCity;
 $('ed-search').oninput=()=>{const q=norm($('ed-search').value.trim());$('ed-search-results').replaceChildren();if(!q)return;const hits=records.filter(r=>norm(r.name+' '+(r.osm||'')).includes(q)).slice(0,18);for(const r of hits){const b=document.createElement('button');b.textContent=r.name;b.onclick=()=>{setMode('buildings');setSelection($('ed-add-selection').checked?[...selection,r.id]:[r.id]);const p=center(shiftedLocal(r));map.easeTo({center:toMap(p),zoom:17,duration:300,padding:window.innerWidth>700?{left:340,right:0,top:0,bottom:0}:{top:0,bottom:$('ed-panel').hidden?0:innerHeight*.35,left:0,right:0}});};$('ed-search-results').append(b);}if(!hits.length)$('ed-search-results').textContent='No hay edificios con ese nombre.';};
 $('ed-notes').oninput=()=>{state.notes=$('ed-notes').value;clearTimeout(noteTimer);noteTimer=setTimeout(persist,250);};
 $('ed-import-button').onclick=$('ed-import-panel').onclick=()=>$('ed-import-file').click();
 $('ed-import-file').onchange=async()=>{const file=$('ed-import-file').files[0];if(!file)return;try{if(file.size>30*1024*1024)throw Error('La ficha supera los 30 MB.');importProject(JSON.parse(await file.text()));}catch(e){status('No se ha importado la ficha: '+e.message);}finally{$('ed-import-file').value='';}};
 window.addEventListener('beforeunload',()=>{state.notes=$('ed-notes').value;persist();});
 window.levanteEditor={getState:()=>copy(state),getSelection:()=>[...selection],getBuildings:()=>records.map(r=>({id:r.id,name:r.name,osm:r.osm,index:r.index,ensemble:r.ensemble,center:center(shiftedLocal(r)),original_center:center(r.originalLocal)})),exportProject:snapshotProject,importProject,selectIds:setSelection,setMode,undo,redo,base:META};
 window.levanteEditorReady=true;
}
const timer=setInterval(()=>{if(window.islandReady&&window.islandMap?.getSource('local-sketch')){clearInterval(timer);try{setup();}catch(e){console.error(e);status('No se pudo iniciar el editor: '+e.message);}}},80);
})();
