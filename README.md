# crease-solver
Allow 3D animations of origami folding parameterized by crease angles.

This project is intended to be a back-end for creating 3D animations of origami
being folded.  

## Setup 

In order to draw origami folding, we need to solve for the location of the
paper.  We represent the initial state of the paper as a unit square in the X-Y
plane.  We assume all folds/creases are straight lines and the paper only bends
on creases. That means the position of the paper can be completely defined by
the 3D coordinates of a set of nodes which represent the ends or intersections
of paper creases.

As input to the code, we need a crease diagram.  This includes the initial 2D
locations of the nodes on the paper, and pairs of nodes that are connected by
creases.  The node labels and their connectivity through creases will remain
constant throughout the folding process, but the crease angles will change.
Once the angles of each crease are known, we can reconstruct the 3D shape of 
paper.

The main problem with solving for crease angles can be reduced to one of
spherical trigonometry.  Consider some node not on the edge of paper, where some
number N of creases meet at that node.  Now think about a tiny sphere centered
on that node (a sphere small enough that its radius is much smaller than the
length of any crease meeting that node).  The intersection of that sphere and
the paper will be a spherical polygon.  In between creases, the flat paper will
intersect the sphere in a segment of a geodesic or great circle; these are the
edges of the polygon, and their "lengths" are the angles that adjacent creases
make at the node.  The creases intersect the sphere at the vertices of the
spherical polygon.  The internal angles of the polygon correspond to the crease
angles.

To make the most use of previously existing formulas in spherical trigonometry,
we define the crease angle to be 180 degrees when the paper is not folded
(flat), greater than 180 degrees for a mountain fold, and less than 180 degrees
for a valley fold.  If we think about the paper as having a top (facing toward
the person folding) and a bottom (facing away from the person folding),
then mountain folds fold the paper away from the person folding.  Then
the "interior" of the spherical polygon is the region above the paper, and the
"exterior" of the spherical polygon is the region below the paper.
This makes the crease angles correspond directly to the interior angles of the
polygon's vertices.







