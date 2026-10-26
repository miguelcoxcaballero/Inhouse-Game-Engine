# Propuesta compactada y auditoría · V02

Leer primero [supuestos, plan, investigación, inventario y reglas](research/criterios-previos.md). Esta entrega es un prototipo cartográfico interactivo; no es todavía un nivel jugable ni un mapa validado por residentes.

## Transformación medible

- Envolvente insular: **49.00 km²**; incluye las aguas interiores y portuarias, por lo que es una medida conservadora.
- Manzanas detectadas por poligonización de calles en el ámbito de selección: **4120**; seleccionadas **440**; eliminadas **3680** (89.3%). No es un censo oficial de manzanas: incluye celdas viarias y excluye recintos sin cierre.
- Edificios urbanos candidatos: **27871**; retenidos tras selección/conflictos: **1826**. Se conservan sus huellas completas, no se miniaturizan. El prototipo elimina edificios que invaden las costuras viarias, pero falta revisión de todos los encuentros.
- Pista: 2.918 → **2.200 km**, acortada por petición expresa. No se afirma que cumpla requisitos aeronáuticos.
- Laguna de diseño: **1.64 km²**. Su contorno se reinterpreta; no es una reducción topográfica fiel.
- Bucle F1 de diseño: **2.75 km**, frente a la referencia histórica FIA de5,419km. La fidelidad curva a curva sigue pendiente.

- Envolvente del tejido viario urbano de València: **6.75 km²** (envolvente convexa). Su huella de corredores con margen de25m suma 3.80 km²; no son superficies catastrales ni el presupuesto de la franja central.
- Benagéber: **0.274 km²** de lámina de diseño, conservando los brazos del contorno OSM. Chelva queda a **1.55 km** de la costa.
- Nuevas carreteras secundarias/de montaña: **20 tramos / 31.7 km**, recompuestos desde secuencias continuas OSM.

La reducción inicial de «10 veces» queda superada en varias zonas por el límite posterior de50km² y la ampliación del ámbito. **No se afirma una relación global exacta**: el antiguo ámbito descargado de2.642,6km² no incluye toda la incorporación de Safor/Calpe. El porcentaje de manzanas eliminadas no es un porcentaje de superficie ni de tiempo de viaje.

Se retienen mercados, plazas, estación, campus, hospital, barrios residenciales y muestras de casas/tramas ordinarias. Se pierden calles, profundidad de barrio, capacidad aeroportuaria/portuaria, extensión agrícola y distancias regionales. La costa, relieve y vecindad de Safor/Albufera son ficción de diseño.

## Presupuesto de superficie medido y sin solapamientos

Estas unidades contables son cortes territoriales del prototipo, no límites de barrios ni reparto de usos de suelo.

| Unidad | km² |
|---|---:|
| Chelva y sierra norte | 6.644 |
| Franja central: ciudad, aeropuerto e interior | 22.927 |
| Cofrentes y valle occidental | 6.897 |
| Albufera y costa | 6.675 |
| Safor / Calpe / Ifac | 5.060 |
| Transiciones restantes | 0.798 |
| **Total** | **49.000** |

## Recorridos antes / después

Comparaciones de secuencia, no tiempos reales calculados. La vista permite recorrer los corredores y consultar conexiones entre estaciones. La distancia del planificador suma segmentos entre estaciones; es aproximada y no sustituye una ruta viaria por carriles.

| Recorrido | Referencia real / antes | Isla / después | Conservación y pérdida |
|---|---|---|---|
| A pie: Quart → Mercat → Catedral → Serrans | Calles irregulares y varias manzanas intermedias | Mismo orden, menos profundidad entre hitos | Plazas y curvas locales; costuras y algunos cruces reinterpretados |
| Bici: Campanar → Turia → Arts | Parque del antiguo cauce y puentes sucesivos | Corredor continuo más corto | Se conserva arco y cambio de ambiente; no todos los puentes |
| Metro: aeropuerto → centro → Marítim | Corredor de L5 con estaciones intermedias | M-A omite paradas; retiene acceso oeste, centro e intercambio marítimo | Red de juego, no horario ni explotación FGV |
| Tranvía: Benimaclet → Vera/Tarongers → playa | Campus, barrios marítimos y bucle tranviario | T-U fusiona tramos y simplifica el bucle | Conserva polos, pierde servicios y sentidos originales |
| Paseo: Alboraia → huerta → Saplaya | Núcleos separados y caminos agrícolas | Franja agrícola y conexión corta | Se conserva interior/costa; menos campos y acequias |
| Coche: Chelva → Cofrentes | Trayecto regional largo entre valles | Ruta occidental sinuosa, pueblos acercados | No reproduce todo el itinerario real; pendientes y radios por verificar |
| A pie: Chelva → Molino Puerto → Playeta | Pueblo, ribera y cascadas | Paseo corto por el valle, acueducto por ramal distinto | Salto de agua conceptual, no modelo topográfico de cascada |
| Cercanías: Nord → Cofrentes/Jalance | No existe esa línea directa de referencia | C-I1 inventada con Bonaire intermedio | Ficción explícita autorizada por el usuario |
| Cercanías: Nord → Saler → Safor → Calpe | No existe esa línea directa de referencia | C-I2 inventada, termina antes de Ifac | Reduce distancia; no conecta todos los pueblos |

## Auditoría

«Cumple» significa la prueba indicada, no validación completa del mundo. Resultados numéricos en [audit.json](data/audit.json).

| Criterio | Estado | Evidencia / trabajo restante |
| ≤50 km² | Cumple | Medición de envolvente en metros locales. |
| Presupuesto sin doble conteo | Cumple | Intersección y diferencia sucesivas. |
| Eliminar manzanas; no círculos de ciudad | Cumple | Selección de bloques completos y cierre no uniforme de franjas. Sectores de pueblos con bordes poligonales. |
| Curvas e intersecciones tan próximas al original como sea posible | Pendiente | Campo continuo aplicado a vértices y cruces OSM; comparación angular en road-review.json. Falta revisión manual por cruce, radios y rasantes. |
| Hitos y tejidos cotidianos | Cumple en inventario; reconocimiento pendiente | Mercados, plazas, residencia, campus, industria y huerta además de monumentos. |
| Todos los elementos dentro de costa | Cumple | Consultar lista exacta de salidas geométricas en audit.json. |
| Geometrías válidas | Cumple | Validación GEOS. |
| Aeropuerto más compacto | Cumple | Pista acortada y recinto periférico retirado. |
| Metro y Cercanías | Cumple como grafo conceptual | 30/30 estaciones conectadas. No implica túneles/rasantes construibles. |
| F1 | Pendiente | Bucle histórico interpretado presente y cerrado; no se garantiza identidad de cada curva. |
| Puentes, túneles, pendientes y colisiones de vías | Pendiente | Señalados algunos cruces; no hay auditoría exhaustiva de rasantes, navegación ni gálibos. |
| Reconocimiento local | Pendiente | No se ha entrevistado ni probado con residentes. |
| Terreno real y vistas verificadas | Pendiente | Relieve sintético; no se prometen panoramas reales. |
| HTML autónomo y vista móvil | Cumple | Chromium: carga,2D/3D,búsqueda,transporte,planificador,modo sin rótulos,ajustes,medición,dibujo y móvil390px. Informe en data/browser-qa.json. |

## Prueba conceptual sin etiquetas

La vista incluye «Sin rótulos ni hitos» para retirar marcadores, nombres regionales y contornos monumentales. Hipótesis a evaluar: el arco del Turia, trama irregular central, cambio al ensanche, franja marítima, puerto, huerta, laguna y montañas siguen orientando. **No equivale a una prueba ciega con personas**. Se sustituyó el cierre en franjas por un campo continuo para evitar corredores artificialmente paralelos. Las tramas rectas que pertenecen a ensanches reales se conservan; no se añaden curvas decorativas para ocultarlas.

## Validación con residentes: protocolo previo a resultados

Reclutar al menos20 participantes, incluyendo residentes del centro, periferia oeste/norte, frente marítimo y municipios exteriores; registrar años de residencia y frecuencia de desplazamiento, sin atribuir consenso a un solo grupo. Dos condiciones contrabalanceadas: mapa sin nombres/hitos y mapa completo. No mostrar el nombre del sector antes de la respuesta.

Umbrales provisionales fijados **antes de recoger datos**: reconocer al menos70% de las zonas funcionales sin etiquetas; ordenar correctamente al menos80% de las secuencias prioritarias; menos de10% de inversiones costa/interior o lados del Turia; ningún obligatorio ausente. Si un sector queda por debajo del60%, conservar más tejido cotidiano de ese sector o rehacer sus transiciones, aunque eso exija retirar repetición de otra zona. Registrar falsas identificaciones y tiempos como datos, sin convertirlos automáticamente en «identidad auténtica».

Siguiente trabajo: corregir incidencias geométricas; comparar cruces OSM y costuras; trazar F1 con referencia histórica georreferenciada; revisar radios y cruces de los enlaces de montaña ya derivados de carreteras fuente; estudiar rasantes/puentes y preparar navegación; después ejecutar la prueba de residentes. No presentar esta versión como mapa final listo para conducción.

## Corredores de autovía y nuevo cauce

La revisión final reemplaza los recortes de autovía por cinco corredores continuos OSM: A-7,V-30,V-21,A-3 y CV-35. Se simplifican detalles inferiores a12m y se contraen preferentemente las rectas, salvo el tramo A-3 registrado con el aeropuerto. En A-7,V-21 y CV-35 los giros conservan sus ángulos antes de colocar las calzadas. La V-30 se acerca al borde sur urbano mediante un ajuste central de hasta450m, manteniendo entrada occidental y desembocadura. La A-3 comparte la transformación longitudinal del aeropuerto para respetar su posición respecto a pista y V-11; la orientación global, las distancias y los enlaces locales se adaptan a la isla. Esto no certifica radios de conducción ni rasantes. [Comparación](previews/vias-osm-comparacion.png), [datos](data/continuous-corridors.geojson) y [auditoría](data/road-review.json).

El nuevo cauce tiene **6.07km** de eje de diseño, lecho, taludes, hilo de agua conceptual, cuatro cruces principales y V-30 en ambas márgenes. Se retira tejido urbano meridional repetido y se recoloca el hospital para mantenerlo al norte del cauce. La separación mínima del eje A-7 respecto a la pista es **318m**; no es una certificación aeroportuaria.

La componente principal contiene **95.5%** de la longitud viaria analizada como red plana. Algunas piezas menores siguen desconectadas. El análisis redondea nodos a1m y no resuelve niveles de puentes, carriles, sentidos o giros prohibidos. [Informe de red](data/network-review.json).

## Más detalle sin miniaturizar edificios

Se conservan huellas completas y orientaciones de edificios OSM. Cuando una huella ordinaria invadía una calle, se buscó un emplazamiento libre próximo, hasta145m; si no encajaba, se eliminó. Estas recolocaciones mantienen tamaño, pero alteran relaciones de fachada y parcela: todavía deben revisarse por grupos de manzanas. No se atribuye reconocimiento local garantizado a esta operación.

La vista incorpora **136 referencias cotidianas OSM** además de los hitos y corredores principales, nombres de calles al acercar, textura de terreno, cobertura forestal propuesta y curvas de nivel. La distribución forestal y las elevaciones son sintéticas.

## Interfaz y referencia State of Leonida

Se descargó e inspeccionó la página pública solicitada. No se encontró una licencia que permitiera reutilizar íntegramente su código propio. La UI entregada es una implementación propia: mapa a pantalla completa, herramientas flotantes, paneles plegables, filtros, agrupación de marcadores, medición, dibujo, deshacer, exportación de imagen y ajustes locales. [Referencia y alcance](research/referencia-state-of-leonida.md).

**No se declara alcanzada una equivalencia de detalle o realismo con State of Leonida.** Esta entrega permite revisar el avance; falta un pase fino de costa, continuidad urbana, F1, enlaces y validación con residentes. Tampoco es un nivel de juego listo para conducir.

## Interior, costa y prioridad viaria

Benagéber usa la relación OSM85608, girada y compactada para encajar entre aeropuerto, Chelva y el borde occidental de la ciudad. Se conserva el desarrollo de sus brazos; la presa usa la vía OSM227206826 con su longitud original. El nivel155m es una cota de diseño. El relieve circundante, ubicación y accesos son ficticios. La ficha oficial [CHJ–SAIH](https://saih.chj.es/embalses/293), consultada el26-10-2026, confirma su identidad sobre el Turia; no se usan niveles en tiempo real. [Mediciones y20 tramos](data/interior-review.json).

Las vías primarias, secundarias y terciarias urbanas se retienen antes de seleccionar calles locales. Las huellas edificadas ceden ante estos corredores. La V-21 parte del norte de la ciudad, por encima del Cabanyal, enlazando el entorno de la avenida de Catalunya con el eje hacia Alboraia/Saplaya; conserva los13 giros simplificados del tramo OSM de referencia, con distancias y orientación global adaptadas. La UI resalta las vías principales y muestra nombres/referencias al acercar. Los radios finos y enlaces multinivel siguen pendientes.

Los paseos se reconstruyen siguiendo la costa real de esta isla de diseño, junto a la arena: el eje queda a unos7m del borde terrestre de la playa, ocupado por la anchura del propio paseo. El aeropuerto dispone de etiqueta persistente y botón de enfoque. Se reconstruye desde el recinto OSM con terminales, plataformas y rodajes, pista de2,20km y una llanura a18m de cota de diseño. A-3,V-11,N-220 y CV-370 organizan sus accesos. [Control de playas](data/beach-review.json).

## Reequilibrio de ciudad y transición sur

La envolvente urbana actual mide **6.75 km²**, frente a5,406km² en la captura anterior: **1.249 veces**. La selección pasa de350 a440 manzanas y profundidad occidental mediante recomposición local; los edificios mantienen sus huellas. Se selecciona tejido OSM real de Mercavalència, Sedaví, Alfafar, Catarroja, Castellar y Pinedo, conectándolo con huerta y marjal. No se afirma igualdad de densidad demográfica: se conserva la trama y escala del fragmento seleccionado. [Fuentes](research/aeropuerto-y-transicion-sur.md) y [comprobaciones espaciales](data/revision-review.json).

## Último ajuste de posición

El tejido de València se traslada300m hacia la costa, sin escalar calles ni edificios; se libera la franja de playa de piezas incompatibles. Chelva se desplaza100m al oeste y200m al sur, aumentando su separación de la costa. La CV-35 parte del noroeste urbano y usa el corredor OSM continuo hasta Chelva, con un viaducto de diseño sobre un brazo estrecho de Benagéber. Sustituye como acceso principal el rodeo por A-7 y la sierra occidental, que queda como alternativa paisajística. El tramo central del nuevo cauce y ambas márgenes V-30 se desplazan hasta450m hacia el borde sur de València; se mantienen la entrada occidental y la desembocadura junto al puerto.
