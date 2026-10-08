// Carcasa Raspberry Pi 5 + VESA — generado por Daniela CADStudio
// Unidades: mm. Edita los parametros y re-renderiza.
ancho = 90.0; fondo = 65.0; alto = 28.0;
pared = 2.0; tol = 0.2;
vesa = 75.0; d_vesa = 4.0;
hex_r = 3.0; hex_dx = 8.0;
$fn = 64;

module base() {
    difference() {
        cube([ancho, fondo, alto]);
        translate([pared, pared, pared])
            cube([ancho - 2*pared, fondo - 2*pared, alto]);
    }
}

module agujeros_vesa() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([ancho/2 + sx*vesa/2, fondo/2 + sy*vesa/2, -1])
            cylinder(h = pared + 2, d = d_vesa);
}

module ventilacion() {
    for (ix = [0 : floor((ancho - 20) / hex_dx)])
        for (iy = [0 : floor((fondo - 20) / hex_dx)])
            translate([10 + ix*hex_dx, 10 + iy*hex_dx, alto - 1])
                cylinder(h = pared + 2, r = hex_r, $fn = 6);
}

module separadores_pcb() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([ancho/2 + sx*29, fondo/2 + sy*24.5, pared])
            difference() {
                cylinder(h = 6, d = 6 + tol*2);
                translate([0, 0, -1])
                    cylinder(h = 8, d = 2.75);
            }
}

difference() {
    base();
    agujeros_vesa();
    ventilacion();
}
separadores_pcb();
