const {chromium}=require('/opt/codex/cua_node/lib/node_modules/playwright-core');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..');
(async()=>{
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 const context=await b.newContext({viewport:{width:1550,height:1050},acceptDownloads:true});const page=await context.newPage();const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith('http://127.0.0.1:8767'))external.push(r.url());});
 await page.goto('http://127.0.0.1:8767/isla-levante-editor.html');await page.waitForFunction(()=>window.levanteEditorReady,null,{timeout:90000});
 await page.evaluate(()=>{islandMap.jumpTo({center:[1300/111319.4908,1200/111319.4908],zoom:16.4,padding:{left:300,right:0,top:100,bottom:40}});});await page.waitForTimeout(1500);
 await page.screenshot({path:path.join(root,'previews/editor-inicial.png')});
 const points=await page.evaluate(()=>{
  const rows=[];
  for(const r of levanteEditor.getBuildings()){
   const f=islandData.geojson.features[r.index],ring=f.geometry.type==='Polygon'?f.geometry.coordinates[0]:f.geometry.coordinates[0][0];
   const mx=ring.reduce((n,p)=>n+p[0],0)/ring.length,my=ring.reduce((n,p)=>n+p[1],0)/ring.length;
   for(const q of [[mx,my],...ring.slice(0,6).map(p=>[(p[0]+mx)/2,(p[1]+my)/2])]){
    const p=islandMap.project(q);if(p.x<470||p.x>1250||p.y<230||p.y>820)continue;
    const found=islandMap.queryRenderedFeatures(p,{layers:['ed-buildings-fill']});
    if(found[0]?.properties.editor_id===r.id){rows.push({id:r.id,p:[p.x,p.y],center:r.center});break;}
   }
   if(rows.length>=30)break;
  }
  for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++)if(Math.hypot(rows[i].p[0]-rows[j].p[0],rows[i].p[1]-rows[j].p[1])>30&&Math.hypot(rows[i].p[0]-rows[j].p[0],rows[i].p[1]-rows[j].p[1])<280)return [rows[i],rows[j]];
  throw Error('No pair of visible test buildings');
 });
 await page.mouse.click(...points[0].p);await page.keyboard.down('Shift');await page.mouse.click(...points[1].p);await page.keyboard.up('Shift');
 assert.equal((await page.evaluate(()=>levanteEditor.getSelection())).length,2,'Shift-click selection');
 await page.mouse.move(...points[0].p);await page.mouse.down();await page.mouse.move(points[0].p[0]+62,points[0].p[1]+38,{steps:9});await page.mouse.up();await page.waitForTimeout(500);
 let project=await page.evaluate(()=>levanteEditor.exportProject());assert.equal(project.building_moves.length,2,'group drag records two buildings');
 const a=project.building_moves[0],c=project.building_moves[1];assert(Math.abs(a.translation_m.east-c.translation_m.east)<1e-6);assert(Math.abs(a.translation_m.north-c.translation_m.north)<1e-6);assert(Math.hypot(a.translation_m.east,a.translation_m.north)>5);
 function coords(c){return typeof c[0]==='number'?[c]:c.flatMap(coords)}
 for(const move of project.building_moves){const before=coords(move.original_geometry_local_m.coordinates),after=coords(move.proposed_geometry_local_m.coordinates);assert.equal(before.length,after.length);before.forEach((p,i)=>{assert(Math.abs(after[i][0]-p[0]-move.translation_m.east)<1e-6);assert(Math.abs(after[i][1]-p[1]-move.translation_m.north)<1e-6);});}
 await page.locator('#ed-undo').click();assert.equal(Object.keys(await page.evaluate(()=>levanteEditor.getState().building_offsets)).length,0);await page.locator('#ed-redo').click();assert.equal(Object.keys(await page.evaluate(()=>levanteEditor.getState().building_offsets)).length,2);
 // Rectangle selection over multiple actual rendered footprints.
 await page.locator('[data-ed-mode="box"]').click();await page.mouse.move(650,350);await page.mouse.down();await page.mouse.move(1080,690,{steps:10});await page.mouse.up();let rectangleCount=(await page.evaluate(()=>levanteEditor.getSelection())).length;assert(rectangleCount>=2,'rectangle selects buildings');
 // The entire rectangular selection can move together; undo restores the prior two moves.
 await page.locator('[data-ed-mode="buildings"]').click();await page.keyboard.press('ArrowRight');assert(Object.keys(await page.evaluate(()=>levanteEditor.getState().building_offsets)).length>=rectangleCount);await page.locator('#ed-undo').click();assert.equal(Object.keys(await page.evaluate(()=>levanteEditor.getState().building_offsets)).length,2);
 // A point-based curved street with metadata and notes.
 await page.locator('[data-ed-mode="street"]').click();await page.locator('#ed-road-name').fill('Conexión propuesta del centro');await page.locator('#ed-road-kind').selectOption('avenue');await page.locator('#ed-road-width').fill('18');await page.locator('#ed-road-note').fill('Mantener esta curva y conectar ambos extremos.');
 for(const p of [[750,740],[840,700],[970,735],[1070,805]])await page.mouse.click(...p);
 await page.locator('#ed-finish-street').click();assert.equal((await page.evaluate(()=>levanteEditor.getState().streets)).length,1);
 let street=(await page.evaluate(()=>levanteEditor.getState().streets))[0];assert.equal(street.coordinates.length,4);assert.equal(street.width_m,18);assert.equal(street.road_type,'avenue');
 // Freehand preserves a non-straight multi-vertex trace.
 await page.locator('[data-ed-mode="freehand"]').click();await page.mouse.move(1160,440);await page.mouse.down();for(const p of [[1180,470],[1210,480],[1240,460],[1270,490],[1290,530]])await page.mouse.move(...p,{steps:3});await page.mouse.up();
 assert.equal((await page.evaluate(()=>levanteEditor.getState().streets)).length,2);assert((await page.evaluate(()=>levanteEditor.getState().streets[1].coordinates.length))>2);
 await page.locator('#ed-notes').fill('Respetar la posición de la Catedral respecto al Ayuntamiento.');
 // Undoing geometry must not erase general instructions typed afterwards.
 await page.locator('#ed-undo').click();assert((await page.locator('#ed-notes').inputValue()).includes('Catedral'));await page.locator('#ed-redo').click();
 const downloadPromise=page.waitForEvent('download');await page.locator('#ed-export').click();const download=await downloadPromise;const downloaded=await download.path();project=JSON.parse(fs.readFileSync(downloaded,'utf8'));assert.equal(project.summary.moved_buildings,2);assert.equal(project.summary.proposed_streets,2);assert(project.general_notes.includes('Catedral'));assert.equal(project.base_map.coordinate_system,'LOCAL_METRES_FICTIONAL');
 fs.copyFileSync(downloaded,path.join(require('os').tmpdir(),'levante-editor-test-feedback.json'));
 // Import is atomic, rejects wrong baselines, and preserves exact coordinates.
 const roundtrip=await page.evaluate(p=>{const prior=levanteEditor.exportProject();let rejected=false;try{levanteEditor.importProject({...p,base_map:{...p.base_map,id:'wrong-base'}})}catch{rejected=true}const unchanged=JSON.stringify(levanteEditor.getState())===JSON.stringify(prior.editor_state);levanteEditor.importProject(p);return {rejected,unchanged,state:levanteEditor.getState()};},project);
 assert(roundtrip.rejected&&roundtrip.unchanged);assert.deepStrictEqual(roundtrip.state,project.editor_state);
 // Actual file chooser import also works.
 await page.locator('#ed-import-file').setInputFiles(path.join(require('os').tmpdir(),'levante-editor-test-feedback.json'));await page.waitForTimeout(300);
 // User text must remain literal, not executable markup.
 await page.evaluate(()=>{const p=levanteEditor.exportProject();p.editor_state.streets[0].name='<img src=x onerror="window.editorInjected=true">';levanteEditor.importProject(p);});assert.equal(await page.evaluate(()=>!!window.editorInjected),false);await page.evaluate(p=>levanteEditor.importProject(p),project);
 await page.screenshot({path:path.join(root,'previews/editor-sugerencias.png')});
 await page.reload();await page.waitForFunction(()=>window.levanteEditorReady,null,{timeout:90000});assert.deepStrictEqual(await page.evaluate(()=>levanteEditor.getState()),project.editor_state,'local reload restore');
 // Mobile layout and gesture selection remain accessible.
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(500);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.locator('#ed-toggle-panel').click();await page.screenshot({path:path.join(root,'previews/editor-movil.png')});
 assert.deepStrictEqual(errors,[]);assert.deepStrictEqual(external,[]);
 const report={base:project.base_map.id,buildings:await page.evaluate(()=>levanteEditor.getBuildings().length),multi_selection:2,rectangle_selection:rectangleCount,group_translation_m:a.translation_m,footprints_preserved:true,undo_redo:true,streets:2,point_vertices:4,freehand:true,export_download:true,json_roundtrip:true,wrong_base_rejected:true,local_reload:true,mobile_no_overflow:true,external_requests:external,errors};
 fs.writeFileSync(path.join(root,'data/editor-browser-qa.json'),JSON.stringify(report,null,2));console.log(report);await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
