# Isla Levante · propuesta y auditoría

Prototipo cartográfico de **49.00 km²**. Incluye Valencia, Alboraia, Port Saplaya, aeropuerto, Bonaire, Chelva, Benagéber, Cofrentes y su central, Albufera, Safor, Calpe e Ifac. No es todavía un nivel jugable. Los estudios de investigación de la carpeta `research` documentan fuentes y decisiones anteriores; esta revisión sustituye el método de deformación urbana.

## Manzanas a tamaño real

Se conservan **231 de 4120 celdas viarias** detectadas en OSM y se eliminan 3889. No es un censo catastral: algunas celdas son plazas o recintos delimitados por vías. Las manzanas y la arquitectura protegida se organizan en 213 conjuntos y se trasladan sin escala, giro, cizalladura ni deformación. Los edificios y calles interiores se desplazan con su conjunto. La superficie conjunta de las manzanas sigue siendo **1.24689 km²**; la envolvente urbana mide **6.38 km²**.

Las 231 geometrías conservan su forma, superficie y perímetro de origen. La comprobación invierte la traslación y compara cada polígono con la fuente. Error máximo de forma: **4.63e-13 m**. Solapamientos entre manzanas: **0**. Edificios urbanos íntegros: **1374**; ninguno se elimina o se mueve por separado después de colocar su conjunto.

Esta revisión reemplaza la compresión elástica que achataba la ciudad. El objetivo aproximado anterior de aumentar su extensión un 25 % cede ante la conservación exacta de las manzanas: se mantiene una envolvente comparable sin estirar geometrías. En Ajustes → **Manzanas conservadas · escala 1:1**, se puede pulsar cada bloque y ver ambas superficies.

## Los 100 elementos de arquitectura solicitados

Se identifican y conservan **100/100 elementos**, representados mediante **151 geometrías fuente** (varios son conjuntos). La tabla [ESCALA-EDIFICIOS.csv](ESCALA-EDIFICIOS.csv) incluye nombres, IDs OSM, superficies de origen y destino, escala y procedencia de las alturas. [Auditoría completa](data/architecture-review.json).

El Miguelete tiene huella independiente y comparte la traslación de la Catedral; OSM registra 51 m de altura. Los conjuntos Catedral/Basílica, Lonja/Mercado/Santos Juanes, Nord/Plaza de Toros y plaza del Ayuntamiento permanecen juntos. Casas Chapa y Lonja del Pescado conservan sus piezas en una única composición. Las barracas se mantienen en El Palmar.

La conservación 1:1 se verifica en planta: forma, superficie, perímetro y dimensiones. No se presentan como medidas reales las extrusiones sin altura documentada. La vista 3D utiliza alturas OSM cuando existen; niveles o valores de vista previa en los demás casos. [Identificación y fuentes](research/edificios-escala-real.md).

## Avenidas y anillos

La estructura principal de Valencia usa 1695 tramos OSM: Cid, Blasco Ibáñez, Grandes Vías, rondas, Port, França, Aragó, Catalunya y otros ejes. Una transformación de semejanza compartida acorta sus distancias al 40 % y conserva los giros y la relación entre cruces. **Solo se acortan estos ejes: las manzanas y los edificios no reciben ese escalado.** Los anchos de calzada son una representación independiente. Se colocan las piezas a escala real en el espacio restante, retirando más tejido secundario.

[Comparación visual](previews/avenidas-anillos-comparacion.png) y [fuentes y medidas](data/urban-backbone-review.json). La comprobación valida que estos trazados no cambian durante los ajustes posteriores. No certifica prioridades ni carriles.

## Continuidad de calles

Los cortes del tejido se detienen en los bordes de manzana. Se reconstruyen las uniones por el espacio que dejan los bloques eliminados. El generador añade 215 enlaces de continuidad, rodea obstáculos y conserva las huellas edificadas. Los contornos de plazas no se convierten automáticamente en carreteras: se mantienen las categorías peatonales de OSM, incluidos pasajes y escaleras.

La red principal reúne el **100.000 %** del viario de vehículos representado; en Valencia, **100.000 %**. Componentes viarios finales: **1**. Son comprobaciones de topología plana a 1 m, no un certificado de navegación por carriles. Los finales de calle reales y los recorridos peatonales se mantienen. [Auditoría de manzanas](data/blocks-audit.json), [conectividad](data/network-review.json) y [reparaciones](data/network-repair.json).

Las autovías A-7, V-21, A-3, V-30 y CV-35 siguen corredores continuos OSM recompuestos. Las curvas originales se conservan en los tramos seleccionados, con las adaptaciones descritas en [comparación viaria](data/road-review.json). Las nuevas costuras son geometría de diseño, no datos reales. Los enlaces multinivel, prioridades, radios y rasantes requieren revisión.

## Paisajes y conexiones regionales

- Playas y paseos siguen la costa de la isla; el puerto interrumpe la franja marítima. El antiguo F1 permanece como interpretación compacta cerrada, con fidelidad curva a curva pendiente.
- Aeropuerto con pista de **2.20 km**, terminales, plataformas y rodajes OSM; llanura a 18 m y accesos V-11/N-220/A-3/CV-370. La pista se acorta por petición expresa; no se aplica esta excepción a las manzanas urbanas.
- Chelva está en el interior, con Peña Cortada, Playeta, cascada, Molino Puerto y Remedio. CV-35 enlaza con la ciudad; Benagéber conserva los brazos del contorno OSM en una lámina de diseño de 0.274 km². Hay 20 tramos secundarios/de montaña, 31.7 km en total.
- El nuevo cauce del Turia y las dos márgenes V-30 quedan junto al sur urbano. Mercavalència, Sedaví, Alfafar, Catarroja, Castellar y Pinedo forman la transición a huerta y marjal.
- Metro/tranvía compactado y dos líneas ficticias de Cercanías, con 30/30 estaciones conectadas. El planificador calcula conexiones ferroviarias conceptuales; no horarios reales.

## Límites y siguientes revisiones

Faltan navegación por carriles, comprobación de todos los cruces a distinto nivel, ajuste fino del parque del Turia y espacios entre conjuntos, mayor fidelidad del antiguo circuito y validación con residentes. El relieve y la costa son de diseño. No se afirma igualdad de detalle con State of Leonida ni una relación global exacta de compresión 10:1.

State of Leonida se inspeccionó como referencia visual; no se encontró licencia para copiar su código propio. La interfaz de este repositorio es propia, con búsqueda, filtros, medición, dibujo, exportación y vista 2D/3D. [Referencia y alcance](research/referencia-state-of-leonida.md).

## Fuentes, reproducción y revisión

Fuente geométrica: OSM, instantánea 2026-10-25T21:21:21Z; [procedencia](data/provenance.json). Documentación municipal de Valencia/Chelva, CHJ, Aena y otras fuentes oficiales en [investigación](research/criterios-previos.md) y [aeropuerto/transición sur](research/aeropuerto-y-transicion-sur.md). Las consultas documentales no sustituyen levantamientos topográficos.

[Auditoría geométrica](data/audit.json), [aeropuerto/costa](data/revision-review.json), [navegador](data/browser-qa.json). Todos los datos derivados se ofrecen con atribución © OpenStreetMap contributors, ODbL; MapLibre bajo BSD-3-Clause.
