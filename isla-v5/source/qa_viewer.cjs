const {chromium}=require('/opt/codex/cua_node/lib/node_modules/playwright-core');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 const page=await browser.newPage({viewport:{width:1700,height:1200}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto('http://127.0.0.1:8770/isla-levante-500.html');await page.waitForFunction(()=>window.islandReady&&window.levanteMeshReview,null,{timeout:180000});
 assert(Math.abs(await page.evaluate(()=>islandData.metrics.island_area_km2)-500)<1e-7);
 assert.equal(await page.evaluate(()=>islandData.verifiedRoutes.features.length),18);
 assert.equal(await page.evaluate(()=>islandData.metrics.city_scale),1);
 await page.evaluate(()=>{document.getElementById('pins').checked=false;document.getElementById('pins').dispatchEvent(new Event('change'));});
 await page.waitForTimeout(350);await page.waitForFunction(()=>islandMap.loaded()&&islandMap.areTilesLoaded(),null,{timeout:180000});await page.evaluate(()=>new Promise(resolve=>{islandMap.once('idle',()=>resolve(true));islandMap.triggerRepaint();}));await page.waitForTimeout(350);
 const fit=await page.evaluate(()=>{const b=islandData.bounds,geo=p=>[p[0]/6378137*180/Math.PI,(2*Math.atan(Math.exp(p[1]/6378137))-Math.PI/2)*180/Math.PI],a=islandMap.project(geo([b[0],b[3]])),c=islandMap.project(geo([b[2],b[1]]));return {left:a.x,top:a.y,right:c.x,bottom:c.y};});assert(fit.left>=0&&fit.top>=90&&fit.right<=1700&&fit.bottom<=1170,JSON.stringify(fit));
 await page.screenshot({path:path.join(root,'previews/isla-500.png')});
 await page.evaluate(()=>{document.getElementById('blind').click();const pts=[];function walk(c){if(typeof c[0]==='number')pts.push(c);else c.forEach(walk);}for(const f of islandData.geojson.features)if(f.properties.kind==='airfield'||f.properties.kind==='building'&&f.properties.city)walk(f.geometry.coordinates);const b=pts.reduce((b,p)=>[Math.min(b[0],p[0]),Math.min(b[1],p[1]),Math.max(b[2],p[0]),Math.max(b[3],p[1])],[Infinity,Infinity,-Infinity,-Infinity]);islandMap.fitBounds([[b[0],b[1]],[b[2],b[3]]],{duration:0,pitch:0,bearing:0,padding:{top:100,bottom:50,left:340,right:35}});});
 await page.waitForTimeout(350);await page.waitForFunction(()=>islandMap.loaded()&&islandMap.areTilesLoaded(),null,{timeout:180000});await page.waitForTimeout(700);
 await page.screenshot({path:path.join(root,'previews/valencia-500.png')});
 await page.evaluate(()=>{islandMap.jumpTo({center:[3900/111319.4908,3500/111319.4908],zoom:15.1,pitch:0,bearing:0});});
 await page.waitForTimeout(350);await page.waitForFunction(()=>islandMap.loaded()&&islandMap.areTilesLoaded(),null,{timeout:180000});await page.waitForTimeout(700);
 await page.screenshot({path:path.join(root,'previews/valencia-detalle.png')});
 for(const [name,center,zoom] of [['aeropuerto-500',[-5000,5000],14.2],['chelva-500',[-6200,7000],15.25],['sur-valencia-500',[3000,-4200],13.3],['albufera-500',[7200,-11200],13.4]]){
  await page.evaluate(({center,zoom})=>{islandMap.jumpTo({center:center.map(v=>v/111319.4908),zoom,pitch:0,bearing:0});},{center,zoom});
  await page.waitForTimeout(350);await page.waitForFunction(()=>islandMap.loaded()&&islandMap.areTilesLoaded(),null,{timeout:180000});await page.waitForTimeout(700);
  await page.screenshot({path:path.join(root,'previews/'+name+'.png')});
 }
 await page.locator('#mesh-review summary').click();await page.locator('#mesh-show').check();await page.locator('#avenue-show').check();
 await page.evaluate(()=>{const r=levanteMeshReview.rows.find(r=>r.building==='w135630267')||levanteMeshReview.rows[0];levanteMeshReview.inspect(r.building);islandMap.jumpTo({center:[r.compact_building_xy[0]/111319.4908,r.compact_building_xy[1]/111319.4908],zoom:16.3,pitch:0,bearing:0});});
 await page.waitForTimeout(350);await page.waitForFunction(()=>islandMap.loaded()&&islandMap.areTilesLoaded(),null,{timeout:180000});await page.evaluate(()=>new Promise(resolve=>{islandMap.once('idle',()=>resolve(true));islandMap.triggerRepaint();}));await page.waitForTimeout(350);
 assert((await page.locator('#mesh-relation').innerText()).includes('Distancia real'));assert.equal(await page.evaluate(()=>islandMap.getLayoutProperty('mesh-edges','visibility')),'visible');
 await page.screenshot({path:path.join(root,'previews/malla-avenidas.png')});
 await page.locator('#mesh-show').uncheck();await page.locator('#avenue-show').uncheck();await page.locator('#routes-show').check();
 await page.evaluate(()=>{islandMap.getSource('relation-selected').setData({type:'FeatureCollection',features:[]});const b=islandData.bounds;islandMap.fitBounds([[b[0]/111319.4908,b[1]/111319.4908],[b[2]/111319.4908,b[3]/111319.4908]],{duration:0,padding:{left:65,right:330,top:90,bottom:50},pitch:0,bearing:0});});
 await page.waitForTimeout(350);await page.waitForFunction(()=>islandMap.loaded()&&islandMap.areTilesLoaded(),null,{timeout:180000});await page.evaluate(()=>new Promise(resolve=>{islandMap.once('idle',()=>resolve(true));islandMap.triggerRepaint();}));await page.waitForTimeout(350);
 assert.equal(await page.evaluate(()=>islandMap.getLayoutProperty('verified-routes','visibility')),'visible');assert((await page.evaluate(()=>islandMap.queryRenderedFeatures({layers:['verified-routes']}).length))>=18);
 await page.screenshot({path:path.join(root,'previews/conexiones-isla.png')});
 assert.deepStrictEqual(errors,[]);fs.writeFileSync(path.join(root,'data/viewer-browser-qa.json'),JSON.stringify({island_area_500:true,full_island_screen_bounds:fit,mesh_toggle:true,avenue_relations_toggle:true,verified_routes:18,route_toggle:true,building_inspector:true,errors},null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
