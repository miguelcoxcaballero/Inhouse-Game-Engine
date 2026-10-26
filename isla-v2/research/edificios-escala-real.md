# Arquitectura a escala real · inventario de 100 elementos

Revisión: 26 de octubre de 2026. La lista del usuario incluye la Lonja de la Seda y 99 entradas numeradas; el Miguelete se considera una pieza independiente, asociada espacialmente a la Catedral. Se conservan las huellas presentes en la instantánea OSM del 25-10-2026, no reconstrucciones de estados históricos desaparecidos.

## Identificación y medidas

Los nombres, etiquetas multilingües y áreas OSM se cruzan con la lista solicitada. Se extraen también las relaciones multipolígono, que faltaban en la lectura inicial de vías: Ayuntamiento, Museu de les Ciències, Generalitat, Bellas Artes, Patriarca y otros conjuntos se resuelven así. Un punto de interés aislado no se toma como perímetro de edificio.

En los casos sin nombre en la huella, se identifica el inmueble mediante la dirección documental y su posición en OSM. Ayuntamiento, IVAM y Hortensia Herrero se comprueban con sus puntos de interés dentro de las áreas correspondientes. Para IVAM se elige el edificio completo Centre Julio González, no una cubierta interior menor. El palacio Hortensia Herrero no se confunde con el distinto Palau dels Català de Valeriola.

Las superficies se calculan en EPSG:25830 antes de trasladarlas al sistema ficticio local de la isla. La auditoría invierte cada traslación y comprueba forma, área, perímetro y dimensiones. Las 100 entradas corresponden a 151 geometrías fuente; varias entradas son conjuntos de edificios o recintos. No se suman estas superficies como una superficie urbana sin solapamientos: el Miguelete, por ejemplo, forma parte del conjunto catedralicio.

- [Inventario con identidades OSM](../data/required-landmarks.json).
- [Geometrías fuente seleccionadas](../data/required-landmark-sources.json).
- [Medidas y alturas por edificio](../ESCALA-EDIFICIOS.csv).
- [Resultado de conservación 1:1](../data/architecture-review.json).

## Fuentes para resolver huellas sin nombre y conjuntos

| Elemento | Identificación documental | Huella OSM |
|---|---|---|
| Casa de los Dragones | [Ajuntament](https://cultural.valencia.es/es/monument/casa-de-los-dragones/) y [CTAV, Cortina II](https://arquitectosdevalencia.es/arquitectura/edificio-cortina-ii/): esquina Sorní/Jorge Juan. Coordenada auxiliar de [Wikipedia](https://es.wikipedia.org/wiki/Casa_de_los_Dragones_%28Valencia%29); se contrasta con esa esquina. | w496338533 |
| Casas Chapa | [CTAV](https://arquitectosdevalencia.es/arquitectura/edificios-chapa/): ocho parcelas en Gran Vía 65–71, Cánovas y Gravador Esteve. [Ficha municipal](https://cultural.valencia.es/es/monument/casa-chapa/). Se preservan las ocho piezas y sus posiciones relativas. | Ocho IDs en el inventario |
| Banco de España | [Banco de España](https://www.bde.es/f/webbde/Secciones/Publicaciones/Folletos/Fic/valencia.pdf), calle Barcas 6; nodo de dirección OSM n12335950792 dentro del inmueble. | w416487480 |
| La Unión y el Fénix | [CTAV](https://arquitectosdevalencia.es/arquitectura/edificio-de-la-union-y-el-fenix/), Xàtiva 13; etiqueta OSM «Propietat La Unió del Fènix Espanyol». | w409877331 |
| Hotel Reina Victoria | [Turisme Comunitat Valenciana](https://www.comunitatvalenciana.com/es/valencia/valencia/alojamientos/hoteles/one-shot-reina-victoria), Barcas 4; nodo de dirección n12335950791. | w416210411 |
| Edificio Ferrer | [Ajuntament](https://cultural.valencia.es/es/monument/casa-ferrer/) y [CTAV](https://arquitectosdevalencia.es/arquitectura/edificio-ferrer/), Cirilo Amorós 29/Pizarro 16. Coordenada auxiliar de [Commons](https://commons.wikimedia.org/wiki/Category:Ferrer_Building) dentro de la huella. | w496518123 |
| Casa Ortega | [CTAV](https://arquitectosdevalencia.es/arquitectura/edificio-ortega/), Gran Vía Marqués del Turia 9; punto OSM con esa dirección n5905297187 dentro del edificio. Se conserva la huella actual, sin afirmar que todo el interior histórico sobreviva. | w496729374 |
| Iglesia del Salvador | OSM identifica «Reial Església del Santíssim Crist del Salvador», Trinitaris 1; no se confunde con otros inmuebles que contienen «Salvador». | w493974568 |
| Misericordia de Campanar | [Parroquia](https://www.parroquiadecampanar.es/contacto/) y [Ajuntament](https://cultural.valencia.es/monument/esglesia-nostra-senyora-de-la-misericordia-de-campanar/), plaza de la Iglesia 11. | r7356910 |
| Lonja del Pescado del Cabanyal | [CTAV](https://arquitectosdevalencia.es/arquitectura/antigua-lonja-de-pescado/), Eugenia Viñes 133–171. Se identifica la manzana completa entre ambas entradas OSM y se mantienen todas sus piezas edificadas y el espacio central en una misma traslación. No se utiliza el punto de un restaurante homónimo. | Piezas de la manzana en el inventario |

Las demás identidades se conservan con sus nombres/etiquetas OSM, área completa e ID verificable. Las barracas elegidas pertenecen a El Palmar; no se incorporan por error las alquerías o barracas homónimas de otros municipios.

## Huella real y altura de vista previa

«Escala 1:1» se refiere a la geometría en planta. OSM aporta altura explícita en 11 de las 151 geometrías seleccionadas y número de plantas en otras. Se mantienen los valores de altura presentes; no se convierten estimaciones por plantas en mediciones verificadas. Miguelete: 51 m en OSM, con su huella independiente y el mismo desplazamiento que la Catedral. Las cubiertas, cúpulas, fachadas y volúmenes escultóricos aún requieren modelado arquitectónico.

La vista 3D usa extrusiones de previsualización cuando falta una altura. El CSV y el JSON distinguen altura OSM, estimación por plantas y valor de previsualización. Por tanto, esta entrega no certifica los 100 modelos tridimensionales completos a escala real.
