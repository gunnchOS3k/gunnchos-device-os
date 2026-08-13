# Game Development and Interactive Media

Axis-aligned bounding boxes are rectangles that do not rotate. They overlap when they overlap on X and on Y. The minimum translation vector (MTV) is the smallest push that separates them — usually along the shallower axis.

Place A at (0,0) 10×10 and B at (8,2) 10×10. They overlap. Push along X by -2 (or +2 the other way) if that axis is shallower than Y. Feel it: two paper index cards on a desk.
