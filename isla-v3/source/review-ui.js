(() => {
  'use strict';
  const timer=setInterval(()=>{if(window.islandReady){clearInterval(timer);start();}},120);
  function start(){
    const map=window.islandMap,data=window.islandData;
    const el=document.createElement('details');el.id='mesh-review';el.innerHTML='<summary>Malla y avenidas · 100 km²</summary><div class="mesh-controls"><label><input type="checkbox" id="mesh-show"> Malla entre edificios</label><label><input type="checkbox" id="avenue-show"> Relaciones con avenidas</label><button id="park-focus">Jardín del Turia · parque</button><p id="mesh-help">Pulsa un edificio para comparar su relación con la avenida de referencia.</p><div id="mesh-relation"></div><small>Distancias medidas desde el centro de la huella. Las alturas sin dato OSM son aproximadas.</small></div>';
    document.body.append(el);
    const geo=p=>[p[0]/6378137*180/Math.PI,(2*Math.atan(Math.exp(p[1]/6378137))-Math.PI/2)*180/Math.PI];
    map.addSource('mesh-review',{type:'geojson',data:data.relationMesh});
    map.addLayer({id:'mesh-edges',type:'line',source:'mesh-review',filter:['==',['get','kind'],'building-relation'],minzoom:13,layout:{visibility:'none'},paint:{'line-color':'#d59df3','line-width':.7,'line-opacity':.6}});
    map.addLayer({id:'avenue-relations',type:'line',source:'mesh-review',filter:['==',['get','kind'],'avenue-relation'],minzoom:13,layout:{visibility:'none'},paint:{'line-color':['case',['get','same_side'],'#83e5dc','#ff926d'],'line-width':1,'line-opacity':.65}});
    map.addSource('relation-selected',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
    map.addLayer({id:'relation-selected-line',type:'line',source:'relation-selected',paint:{'line-color':'#fff092','line-width':3}});
    document.getElementById('mesh-show').onchange=e=>map.setLayoutProperty('mesh-edges','visibility',e.target.checked?'visible':'none');
    document.getElementById('avenue-show').onchange=e=>map.setLayoutProperty('avenue-relations','visibility',e.target.checked?'visible':'none');
    document.getElementById('park-focus').onclick=()=>{map.jumpTo({center:geo([1450,1700]),zoom:14.8,pitch:0,bearing:0});};
    const rows=new Map(data.avenueRelations.map(r=>[r.building,r]));
    function inspect(id){
      const r=rows.get(id),panel=document.getElementById('mesh-relation');panel.replaceChildren();
      if(!r){document.getElementById('mesh-help').textContent='Este edificio pertenece a un sector exterior; no tiene comparación con las avenidas de Valencia.';return;}
      document.getElementById('mesh-help').textContent='Edificio '+r.building+' · '+(r.avenue||'Enlace principal');
      const table=document.createElement('table');
      for(const [name,value] of [['Distancia real',r.source_distance_m.toFixed(1)+' m'],['Objetivo de la malla',r.target_distance_m.toFixed(1)+' m'],['Distancia compactada¹',r.compact_distance_to_corresponding_point_m.toFixed(1)+' m'],['Cambio de orientación',Math.abs(r.bearing_error_degrees).toFixed(1)+'°'],['Lado local de la vía',r.same_side?'Conservado':'Revisar extremo / curva']]){
        const tr=document.createElement('tr'),th=document.createElement('th'),td=document.createElement('td');th.textContent=name;td.textContent=value;tr.append(th,td);table.append(tr);
      }
      panel.append(table);const note=document.createElement('p');note.textContent='¹ Al mismo punto de referencia de la avenida. Estas cifras describen la base del mapa; tus movimientos se guardan aparte en la ficha exportada.';note.className='mesh-note';panel.append(note);
      map.getSource('relation-selected').setData({type:'FeatureCollection',features:[{type:'Feature',properties:{},geometry:{type:'LineString',coordinates:[geo(r.compact_building_xy),geo(r.compact_avenue_xy)]}}]});
    }
    map.on('click',e=>{
      if(!el.open)return;
      const layers=['buildings','ed-buildings-fill'].filter(id=>map.getLayer(id));const found=map.queryRenderedFeatures(e.point,{layers});const f=found.find(f=>f.properties.source_id||f.properties.osm);
      if(f)inspect(f.properties.source_id||f.properties.osm.replace('way/','w').replace('relation/','r'));
    });
    let editorIds=null,lastSelection='';
    setInterval(()=>{
      if(!window.levanteEditorReady||!el.open)return;
      if(!editorIds)editorIds=new Map(levanteEditor.getBuildings().map(r=>[r.id,(r.osm||'').replace('way/','w').replace('relation/','r')]));
      const id=levanteEditor.getSelection()[0]||'';
      if(id&&id!==lastSelection)inspect(editorIds.get(id));lastSelection=id;
    },250);
    window.levanteMeshReview={inspect,rows:data.avenueRelations};
  }
})();
