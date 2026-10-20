// Embodied Data Relay — reference open-frame tray
// Units: millimeters. Reference only; measure your hardware before printing.
// License: CERN-OHL-S-2.0

$fn = 48;

base_w = 340;
base_d = 330;
base_t = 6;
lip_h = 16;
lip_t = 4;

hdd_w = 101.6;
hdd_d = 147;
hdd_h = 26.1;
hdd_gap = 10;

pc_w = 130;
pc_d = 130;
pc_h = 50;

fan = 120;
fan_t = 25;

module rounded_plate(w, d, h, r = 6) {
    hull() {
        for (x = [r, w - r]) {
            for (y = [r, d - r]) {
                translate([x, y, 0]) cylinder(h = h, r = r);
            }
        }
    }
}

module base_plate() {
    difference() {
        union() {
            rounded_plate(base_w, base_d, base_t, 8);
            // perimeter lip
            difference() {
                rounded_plate(base_w, base_d, base_t + lip_h, 8);
                translate([lip_t, lip_t, base_t])
                    rounded_plate(base_w - 2 * lip_t, base_d - 2 * lip_t, lip_h + 1, 5);
            }
        }
        // ventilation slots
        for (x = [30 : 24 : base_w - 30]) {
            translate([x, 30, -1]) cube([10, base_d - 60, base_t + 2]);
        }
        // cable pass-through
        translate([base_w / 2 - 30, base_d - lip_t - 1, base_t - 1])
            cube([60, lip_t + 2, lip_h + 2]);
    }
}

module hdd_rails(x, y) {
    translate([x, y, base_t]) {
        for (dx = [0, hdd_w - 8]) {
            difference() {
                cube([8, hdd_d, hdd_h + 8]);
                for (dy = [18, hdd_d - 18]) {
                    translate([-1, dy, 8]) rotate([0, 90, 0]) cylinder(h = 10, r = 1.8);
                }
            }
        }
        // front stop
        cube([hdd_w, 8, hdd_h + 8]);
        // rubber pads
        for (dx = [12, hdd_w - 20]) translate([dx, hdd_d - 18, 0]) cube([8, 8, 2]);
    }
}

module standoff(x, y, h = 8, r = 5) {
    translate([x, y, base_t]) {
        difference() {
            cylinder(h = h, r = r);
            translate([0, 0, h - 6]) cylinder(h = 7, r = 1.8);
        }
    }
}

module fan_plate(x, y) {
    translate([x, y, base_t]) {
        difference() {
            rounded_plate(fan + 16, fan + 16, 5, 4);
            translate([8, 8, -1]) cylinder(h = 7, r = fan / 2 - 2);
            for (dx = [8, fan + 8]) for (dy = [8, fan + 8])
                translate([dx, dy, -1]) cylinder(h = 7, r = 2.1);
        }
    }
}

module assembly() {
    base_plate();
    // two HDDs side by side
    hdd_rails(18, 18);
    hdd_rails(18 + hdd_w + hdd_gap, 18);
    // mini PC standoffs (measure your model)
    for (dx = [0, pc_w - 10]) for (dy = [0, pc_d - 10])
        standoff(18 + dx, 190 + dy, 8);
    // fan plate at the right rear
    fan_plate(200, 190);
}

assembly();
