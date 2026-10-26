# Isla Levante · criterios anteriores a la recomposición

Consulta: 26-10-2026. Uso: prototipo de mundo abierto contemporáneo, no cartografía para navegar en el territorio real. Límite de **50 km² de envolvente insular, incluidos lagunas y dársenas interiores**. Se conserva norte arriba. Se incorporan los encargos posteriores: Safor, Calpe/Ifac, cascadas de Chelva, transporte regional ficticio y mayor supresión de manzanas céntricas.

## Plan ejecutable

| Fase | Información / tarea | Entregable | Dependencia / cierre |
|---|---|---|---|
| Investigación | OSM, cartografía municipal, estudios de barrio, movilidad, historia, paisaje; contrastar lo que cambia decisiones | Fuentes y hechos separados de propuestas | Consultas realizadas antes de la geometría V2 |
| Inventario | Centro, periferias, actividad productiva, universidad, paisaje y nodos cotidianos | Tabla siguiente | Cada sector tiene vecinos y rasgos propios; lagunas declaradas |
| Reglas | Fijar costa, río, conexiones, secuencias; acciones y pérdidas | Restricciones y matriz | Antes de borrar edificios |
| Compactación | Seleccionar manzanas completas; cerrar huecos; conservar curvas fuera de costuras; construir transiciones | GeoJSON, HTML autónomo, terreno y transportes | Área medida ≤50, obligatorios presentes |
| Auditoría | Geometría, transporte, navegador, lectura sin rótulos y validación local | Resultados y asuntos pendientes | Diferenciar pruebas hechas de validaciones propuestas |

## Investigación: hechos, interpretación y propuesta

**Hechos documentados.** La cartografía municipal distingue 87 barrios y 19 distritos; las Juntas municipales no son esa misma división [S1,S2]. Los estudios municipales describen la persistencia del núcleo de casas bajas de Campanar junto a desarrollos posteriores, el centro propio de Patraix y la avenida del Puerto como eje y barrera de El Grau [S3–S5]. El campus de Vera se organiza alrededor del Ágora, con jardines y equipamientos, junto a la huerta [S8]. La Ruta del Agua incluye Molino Puerto, La Playeta con cascadas y el paso de Olinches [S12]. La Serra de la Safor se relaciona con Villalonga, barrancos y el Circ de la Safor [S14]. Ifac es un promontorio litoral calcáreo unido al frente urbano de Calpe [S15].

**Interpretación.** La reconocibilidad depende de secuencias —casco, ensanche, río-parque, universidades, huerta, barrio marítimo, puerto— y de tejidos diferentes. Las periferias y mercados son parte de esa lectura. Los estudios de barrio ofrecen evidencia localizada y fechada, no una votación de todos los residentes ni una descripción social universal de 2026.

**Propuesta.** Una isla ficticia con València al este/centro, aeropuerto al oeste, Chelva al noroeste, Cofrentes al suroeste, Albufera al sureste y Safor/Calpe en el extremo sur. Se elimina territorio entre núcleos y grupos de manzanas; no se aplica una escala única a todos los edificios. Los ajustes de carreteras en las costuras, el relieve y los servicios de transporte son de diseño. El antiguo F1 se interpreta como memoria de un trazado histórico, no como prueba de que el circuito completo siga operativo.

## Inventario previo de zonas

A = monumentos; B = referencias cotidianas; C = tejido; D = secuencia. Esta división es funcional y no sustituye los límites oficiales. Confianza alta en ubicación cartográfica; media en la selección identitaria; reconocimiento por residentes pendiente.

| Zona / posición | Función y A–B | C: tejido retenible | D: vecinos y secuencia | Evidencia / confianza |
|---|---|---|---|---|
| Ciutat Vella, centro | Catedral, Llotja, torres; Mercat Central, plazas | Calles estrechas, manzanas irregulares, patios | Quart → mercado → catedral → Serrans → Turia | S1, S2, OSM / alta física |
| Extramurs / Botànic, oeste del casco | Estació del Nord, borde comercial | Ensanche y cambios de alineación | Centro → Guillem de Castro → oeste | S1, OSM / media |
| Russafa / Eixample, sur del casco | Mercado, comercio y plazas | Manzana cerrada y calles diagonales | Nord → Russafa → corredor de las Arts | S1, OSM / media |
| Patraix / Jesús, suroeste | Plaza de Patraix, estaciones | Núcleo antiguo dentro de tejido denso | Oeste → Patraix; ferrocarril separa del sureste | S3, OSM / alta física |
| Campanar, noroeste urbano | Plaza e iglesia, Bioparc próximo | Casas bajas históricas y tejido posterior | Acceso oeste → antiguo pueblo → Turia | S4, OSM / alta física |
| Torrefiel / Orriols, norte | Mercado, equipamientos cotidianos | Bloques residenciales ordinarios | Norte urbano → Benimaclet / huerta | S6, OSM / media |
| Benimaclet, noreste | Plaza, estación, comercio | Núcleo antiguo, ensanche, transición a huerta | Centro → Benimaclet → campus / Alboraia | S7, OSM / media |
| Blasco Ibáñez / Mestalla | Campus UV, estadio, jardines | Avenida ajardinada, facultades y residencial | Alameda → Mestalla → universidades | S9, OSM / alta física |
| Vera / Tarongers | UPV, UV, bibliotecas, Ágora | Recintos docentes abiertos, deportes | Benimaclet → campus → Cabanyal / huerta | S8,S9 / alta física |
| Cabanyal / Canyamelar / Malvarrosa | Mercado y playas | Trama alargada paralela a la costa, casas bajas | Campus → Cabanyal → playa; Grau al sur | S1, OSM / media |
| Grau / Marina / Natzaret | Atarazanas, Veles e Vents, memoria F1 | Residencial, frente portuario y transición productiva | Avenida del Puerto → Grau → Marina; Natzaret al sur | S5,S10 / alta física |
| Puerto de València | Muelles, dársenas, logística | Grandes piezas productivas, viales de servicio | Separado de playa, conectado al sur industrial | OSM,S5 / alta geometría; operación pendiente |
| Malilla / Quatre Carreres | La Fe, parques, Ciutat de les Arts | Grandes piezas públicas y residencial | Russafa → Malilla / Arts → sur | S1, estudio Malilla2021 / media |
| Alboraia / huerta | Mercado, acequias, caminos | Núcleo compacto y campos entre núcleos | Benimaclet → huerta → Alboraia → Saplaya | S11,OSM / media |
| Port Saplaya / Patacona | Marina, playa y paseo | Frente residencial alrededor del agua | Alboraia interior → Saplaya costa → Patacona al sur | S11, prensa local2023 / media |
| Aeropuerto / Manises / acceso oeste | Terminal, pista, metro | Plataforma compacta, nodo de transporte | Aeropuerto → Mislata → ciudad | OSM,Aena / alta física |
| Bonaire / Aldaia | Comercio y logística | Gran edificio, patios y aparcamiento reducido | Suroeste del aeropuerto, acceso oeste urbano | OSM / alta física; uso comercial actual no auditado |
| Chelva | Iglesia, palacio, lavaderos, Peña Cortada | Núcleo irregular, caminos de ladera | Pueblo → Molino Puerto → Playeta/cascadas; acueducto por ruta distinta | S12,S13,OSM / media |
| Cofrentes / Jalance | Castillo, central, balneario | Pueblo elevado, confluencia, recinto energético | Castillo → confluencia → central; Jalance al sur | AyuntamientoCofrentes,OSM / media |
| Albufera / Saler / Palmar | Embarcaderos y pueblos | Agua, arrozal, devesa, canales y franja litoral | Ciudad → Saler → laguna / Palmar; mar al este | ParqueNatural,OSM / media |
| Safor / Villalonga, extremo sur interior | Barrancos y circo montañoso | Relieve abrupto, pequeños valles agrícolas | Albufera → pie de sierra → puerto de montaña → Calpe | S14,OSM / media; geomorfología reinterpretada |
| Calpe / Ifac, extremo sur costero | Casco, puerto, salinas, peñón | Muestra corta de casco y frente marítimo | Calpe → puerto → istmo → Ifac | S15,OSM / media |

Lagunas: no se ha inventariado establecimiento por establecimiento; no se promete representar las 87 identidades de barrio en 50 km². Burjassot y municipios metropolitanos intermedios requieren evaluación adicional. Falta participación local y verificación de accesibilidad, usos actuales, materiales y fachadas. La ausencia de entrevista no se usa como motivo para eliminar una zona.

## Reglas espaciales y matriz de decisiones

1. El litoral queda al este. Orden norte–sur: Saplaya/Patacona, Malvarrosa/Cabanyal, Marina/puerto, Devesa/Albufera, Calpe/Ifac.
2. Casco al sur del arco septentrional del antiguo Turia; campus y Benimaclet al norte/noreste. Mantener cruces identificables, no convertir el parque en una autopista.
3. Aeropuerto al oeste; Bonaire al suroeste del aeropuerto. Pista separada del tráfico ordinario.
4. Alboraia interior y Saplaya costera con huerta entre ciudad y núcleos. No fundir todo en una cuadrícula residencial.
5. Chelva tiene pueblo, valle del agua, cascadas y acueducto como secuencia caminable; Peña Cortada no es la cascada.
6. Central protagonista del valle de Cofrentes. Conservar recinto, confluencia y pueblo como elementos distintos.
7. Eliminar grupos completos de manzanas ordinarias en vez de cortar edificios. Conservar intersecciones y curvas fuera de las zonas de cierre; dentro de ellas admitir reconstrucción identificada.
8. Ninguna vista hacia un monumento se da por garantizada. El relieve es propuesto, no un DEM real.
9. Metro compacto inspirado en corredores reales; estaciones omitidas y fusiones declaradas. Cercanías de isla inventado, sin pretensión de reproducir la red real ni conectar todos los pueblos.

| Elemento | Acción | Motivo / evidencia | Pérdida | Mitigación |
|---|---|---|---|---|
| Centro histórico | Conservar hitos y grupos de manzanas; eliminar filas intermedias | Encargo de mayor compresión; S1+OSM | Menos profundidad y calles cotidianas | Mercado, plazas, muestras de trama irregular y orden de puertas |
| Ensanches / periferias | Simplificar y acercar, no excluir por falta de monumentos | Estudios S3–S7 | Menor número de calles y equipamientos | Retener núcleo, mercado/estación, muestras de tipos de manzana |
| Turia / avenidas / cruces | Conservar secuencia; recomponer costuras | S1,PMUS,OSM | Se alteran longitudes y algunos ángulos | Usar polilíneas OSM y localizar reconstrucciones |
| Campus | Simplificar recintos, conservar varios polos | S8–S9 | Menos facultades y deporte | Ágora, bibliotecas, edificios y transición residencial |
| Puerto / F1 / playas | Simplificar superficies y rectas; conservar funciones diferenciadas | S5,S10,OSM | Capacidad logística y longitud histórica | Dársenas, muelles, bucle histórico interpretado, playas separadas |
| Aeropuerto | Eliminar periferia y acortar pista | Encargo expreso | Deja de ser un aeropuerto técnicamente equivalente | Terminal y plataforma reconocibles; no afirmar aptitud aeronáutica |
| Bonaire | Conservar edificio; reducir aparcamientos | OSM | Capacidad comercial/viaria | Mantener acceso y escala de gran equipamiento |
| Huerta / marjal | Eliminar extensión repetida; conservar franjas y acequias | S11, parque y OSM | Menor continuidad ecológica/agroproductiva | Separar los núcleos con paisaje, no solar vacío |
| Albufera | Reinterpretar borde y quitar agua abierta | Restricción ≤50km² | No replica contorno ni dinámica hidrológica | Laguna, canales, devesa y pueblos en orden |
| Chelva / Cofrentes | Acercar valle, pueblos e hitos | S12–S13,OSM | Distancias y orientación exacta de valles | Caminos sinuosos y secuencias, edificios seleccionados sin reducción |
| Safor / Calpe / Ifac | Reinterpretar relieve, retener pequeña muestra urbana | Nuevo encargo,S14–S15 | No cabe todo el litoral intermedio | Extremo sur inequívoco, istmo y peñón separados del casco |
| Cercanías | Crear dos corredores de isla | Permiso expreso del usuario | No es la red real | Nombres C-I, trazos distintos y aviso en mapa |

## Fuentes realmente consultadas

Fecha de consulta común: **2026-10-26**. «s/f» = no se identificó fecha de publicación; no confundir fecha de rastreo web con publicación.

- **S1** [Cartografía de barrios, Ayuntamiento](https://www.valencia.es/cas/estadistica/mapa-barrios), página con cartografía2025/2026; [datos abiertos](https://opendata.vlci.valencia.es/dataset/barris-barrios), GeoJSON descargado.
- **S2** [Juntas municipales](https://www.valencia.es/cas/participacion/juntas-municipales-de-distrito/cual-es-mi-junta), s/f. No equivalen a distritos estadísticos.
- **S3** [Patraix, estudio municipal](https://www.valencia.es/documents/20142/14272312/PATRAIX%2B2023.pdf/6d0528e9-44c8-e59e-34ca-679a123f9d66?t=1725273063356), octubre2023.
- **S4** [Campanar, estudio municipal](https://www.valencia.es/documents/20142/14272312/Campanar.pdf/b7adfe03-3dd2-b11b-ba9b-84096d38b801?t=1725273249727),2023. El documento alterna clasificaciones patrimoniales para un elemento; no se traslada esa clasificación legal al prototipo.
- **S5** [El Grau, estudio municipal](https://www.valencia.es/documents/20142/618951/20200923%2BEstudio%2Bbarrio%2Bde%2BEl%2BGrau%2BFINALIZADO.pdf/5eae9284-1c12-c2a5-1eb9-4e4bfc0df6df?t=1600863612318),2020. Entrevistas fechadas, no validación de este mapa.
- **S6** [Torrefiel2023, índice municipal de estudios](https://www.valencia.es/es/-/estudios-y-documentos),2023. Documento consultado desde ese índice.
- **S7** [Benimaclet, estudio municipal](https://www.valencia.es/documents/20142/14272312/20220131%2BEstudi%2BBenimaclet%2B2022.pdf/eed81755-c756-fcb7-1cf2-c480b26ce1fd?t=1643962226499),2022. Disputas sobre desarrollo de huerta no se interpretan como consenso.
- **S8** [Campus de Vera, UPV](https://www.upv.es/otros/como-llegar-upv/campus-vera/index-es.html),s/f.
- **S9** [Campus Tarongers, UV](https://www.uv.es/uvweb/transparencia-uv/es/institucional-organizativa/estructura-organizativa/campus/campus-tarongers-1285948360201.html),s/f; ubicación de otros campus contrastada con OSM.
- **S10** [FIA, previo GP2012](https://www.fia.com/race-preview-6),2012, longitud histórica5,419km; [proyecto constructor BECSA](https://becsa.es/soluciones/proyectos/circuito-urbano-de-f1-valencia/), obra2009. BECSA indica longitud de su obra, que no se confunde con longitud de vuelta FIA.
- **S11** [Rutas de huerta, Turismo Alboraia](https://www.turismoalboraya.es/es/experiencias/huerta/rutas-por-la-huerta),s/f; [reclamación vecinal de conexión Saplaya](https://www.elperiodicodeaqui.com/valencia/horta/vecinos-de-port-saplaya-reclaman-el-servicio-de-la-emt-para-conectar-con-valencia_329369_102.html),13-11-2023. No establece el servicio actual.
- **S12** [Ruta del Agua, Turismo Chelva](https://www.turismochelva.es/quehacer/ruta-del-agua/),s/f. Cascadas de La Playeta; no se atribuye una cascada a Peña Cortada.
- **S13** [Peña Cortada, Turismo Chelva](https://www.turismochelva.es/quever/acueducto-pena-cortada/),s/f.
- **S14** [Serra de la Safor, Comunitat Valenciana](https://www.comunitatvalenciana.com/es/valencia/vilallonga-villalonga/espacios-naturales/serra-de-la-safor),s/f.
- **S15** [Ifac, Turismo Calpe](https://www.calpe.es/es/descubre-calpe/espacios-naturales/pe%C3%B1on-de-ifach),s/f.
- [PMUS municipal](https://www.valencia.es/web/gobierno-abierto/cas/informacion-institucional/organizaci%C3%B3n/planificacion/plan-movilidad-urbana), aprobado2013. No se utiliza como horario actual.
- [Planeamiento y realidad urbana1939–1989, Cuadernos de Geografía](https://www.uv.es/cuadernosgeo/CG55_063_089.pdf), estudio histórico, no diagnóstico demográfico2026.
- [Castillo de Cofrentes, Ayuntamiento](https://www.cofrentes.es/home/castillo-de-cofrentes),s/f; [Cerro de Agras](https://www.turismocofrentes.com/ruta-al-volcan-cerro-de-agras/),s/f.
- [Parque Natural de l’Albufera](https://parquesnaturales.gva.es/es/web/pn-l-albufera),s/f, descargado; [Aena, metro](https://www.aena.es/es/valencia/como-llegar/metro.html),s/f, descargado.
- [Guía independiente Metrovalencia](https://metrovalencia.org/mapa-metro-valencia/),edición declaradaFGV01/2026. Se usa junto a relaciones OSM; acceso directo a la página FGV falló. No se garantiza explotación, horarios ni estado de servicio.
- **OSM / Geofabrik** [Comunitat Valenciana](https://download.geofabrik.de/europe/spain/valencia.html), instantánea2026-10-25T21:21:21Z descargada,135MB. Geometrías e IDs trazables en los datos. ©OpenStreetMap contributors, ODbL.
