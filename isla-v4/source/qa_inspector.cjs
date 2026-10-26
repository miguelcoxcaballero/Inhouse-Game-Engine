const {chromium}=require('/opt/codex/cua_node/lib/node_modules/playwright-core');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..');
(async()=>{
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 const p=await b.newPage({viewport:{width:1500,height:1000}});await p.goto('http://127.0.0.1:8769/isla-levante-editor-300.html');await p.waitForFunction(()=>window.levanteEditorReady&&window.levanteMeshReview,null,{timeout:180000});
 const bounds=JSON.parse(fs.readFileSync(path.join(root,'data/editor-manifest.json'))).editor_city_bounds_m;
 const fit=await p.evaluate(b=>{const geo=(x,y)=>[x/6378137*180/Math.PI,(2*Math.atan(Math.exp(y/6378137))-Math.PI/2)*180/Math.PI];const a=islandMap.project(geo(b[0],b[3])),c=islandMap.project(geo(b[2],b[1]));return {left:a.x,top:a.y,right:c.x,bottom:c.y};},bounds);
 assert(fit.left>=379&&fit.top>=174&&fit.right<=1431&&fit.bottom<=911,JSON.stringify(fit));
 await p.screenshot({path:path.join(root,'previews/editor-encuadre-300.png')});
 await p.locator('#mesh-review summary').click();
 await p.evaluate(()=>{const r=levanteEditor.getBuildings().find(r=>r.osm==='way/135630267');levanteEditor.selectIds([r.id]);islandMap.jumpTo({center:[r.center[0]/111319.4908,r.center[1]/111319.4908],zoom:17,padding:{left:320,right:260,top:130,bottom:40}});});
 await p.waitForFunction(()=>document.getElementById('mesh-help').textContent.includes('w135630267'));
 assert.equal(await p.locator('#mesh-relation tr').count(),5);await p.locator('#avenue-show').check();await p.waitForFunction(()=>islandMap.areTilesLoaded(),null,{timeout:180000});
 await p.screenshot({path:path.join(root,'previews/inspector-editor.png')});fs.writeFileSync(path.join(root,'data/inspector-editor-qa.json'),JSON.stringify({offline_file_open:false,offline_file_limitation:'Managed Chromium blocks file navigation (ERR_BLOCKED_BY_ADMINISTRATOR). Embedded assets tested over localhost without external requests.',expanded_city_fits_initial_view:true,selection_updates_inspector:true,selected_osm:'way/135630267',comparison_rows:5,avenue_layer_visible:await p.evaluate(()=>islandMap.getLayoutProperty('avenue-relations','visibility'))},null,2));await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
