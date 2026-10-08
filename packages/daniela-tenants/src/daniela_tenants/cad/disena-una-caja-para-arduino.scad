// Caja generica con tapa — Daniela CADStudio (mm)
ancho = 100.0; fondo = 80.0; alto = 40.0;
pared = 2.4;
$fn = 48;

module caja() {
    difference() {
        cube([ancho, fondo, alto]);
        translate([pared, pared, pared])
            cube([ancho - 2*pared, fondo - 2*pared, alto]);
    }
}

module tapa() {
    translate([0, fondo + 5, 0])
        cube([ancho, fondo, pared]);
}

caja();
tapa();
