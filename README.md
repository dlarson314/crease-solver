# crease-solver
Allow 3D animations of origami folding parameterized by crease angles.

This project is intended to be a back-end for creating 3D animations of origami
being folded.  I'm writing the README first; code will come later, if at all.

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
edges of the polygon, and their arc lengths are the angles that adjacent creases
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

Our problem will involve finding the angles of the polygon, when the arc lengths
of the spherical polygon edges are known.  The problem is directly solvable when
N=3, and we can apply formulas for spherical triangles (assuming arc lengths for
triangle edges allow a solution to exist).  When N > 3, there will typically be
many solutions for crease angles.  At each vertex, we will therefore want to
specify enough crease angles that there are only three unknown angles.  When a
crease angle is known/specified, the two edges adjacent to a known crease angle
can be replaced with a single edge whose arc length we can calculate.  This
allows us to replace a problem with a spherical N-gon with a spherical
(N-1)-gon.  

To animate an origami fold, we will typically want to specify only one degree of
freedom, or one crease angle, which will increase or decrease with time.  If we
have a vertex that requires many crease angles to be specified, we can either
hold some of them fixed at 180 degrees, or specify that several changing crease
angles are equal to each other.

For many folds, we may want to specify that most creases are kept at the same
angle they were before the fold, and we only list a much smaller set of creases
that will change their angle.

We may find that there are some degeneracies in the solution, even if all but
three crease angles are known.  In that case, it will be useful to know which
folds are intended to be mountain folds and which folds are intended to be
valley folds.  If we know three edge arc lengths of a triangle, then there are
two solutions (where vertex indices that were ordered counter-clockwise [on the
unfolded paper as seen from the top] proceed in a clockwise or a
counterclockwise solution on the sphere, again as seen from the top).  It turns
out that we need to consider both solutions.  Because we want to be able to take
spherical N-gons and progressively reduce N down to 3, the sides of the final
triangle can have a handedness that they would not otherwise have, if they were
not based on multiple arcs.  This means we will be able to tell the difference
between the clockwise and counter-clockwise solutions.  We will also find that
both solutions can be valid (with the paper not self-intersecting) answers.
If one solution has crease angles of A, B, C, then the other solution will have
angles 360 - A, 360 - B, and 360 - C.

Now, if we specify enough angles at one node that all crease angles are known,
then those crease angles are now known at the nodes at other ends of each of
these creases, and the solution can propagate outward from a single node.
To solve for the entire set of crease angles, we will need to search for a
solvable node (with only 3 unknown crease angles), solve it, and then check to
see if the new known crease angles allow crease angle solutions at other nodes.

## Solving for Node Locations from Crease Angles

Once we know all of the crease angles, we will want to solve for the 3D
locations of each node.  We pick some triangle to remain fixed in the original
plane of the unfolded paper, or give it some known location.  Then we locate all
the rest of the triangles with respect to that one.  To reduce numerical error,
we pick the first reference triangle to be one close to the center of the paper.

Then, we determine a reference frame for each triangular section of paper.  The
reference frame consists of three unit vectors, two of which are in the plane of
the paper, and one of which is orthogonal to the paper.  We can choose the two
in the plane of the paper to be ones originally pointing (before folding) in the
directions of the X and Y axes.  The reference frame for the first fixed
triangle will be unit vectors in the X, Y, and Z axes.  To obtain a reference
frame for a triangle adjacent to a known triangle, rotate all three unit vectors
by (crease angle - 180) around the edge between the two triangles.  We take a
right handed rotation around the edge direction determined by traversing the
nodes of the known triangle in a counter-clockwise fashion, as seen from the top.
(By this method, the first two unit vectors in the reference frame travel by parallel
transport from one triangle to the next, and the original flatness of the paper
[lack of curvature] means there should be no ambiguity arising from the order in
which we traverse triangles.)

Determining the reference frame for all triangles involves a breadth-first
search among neighboring triangles, starting from the original triangle, 
propagating the reference frame as we go.

This method will accumulate some small amount of numerical error.  If we want to
reduce that error, we can write down a set of equations in the reference frame
matrices (thought of as 3x3 matrices) that include small error terms in 
infinitesimal (or very small) rotations.  There will be one matrix equation for
every crease between two triangles.  Each matrix equation will be 9 actual
equations.  This can be solved by linear least squares for the small rotation
adjustments that make a best fit to all crease angles.  If that's not good
enough, we can re-orthogonalize the reference frames and repeat the procedure.

Once the reference frames are known for each triangle, we can either do a
similar propagation of node locations away from the reference triangle, or we
can write down three sets of linear least squares problems (one each for the X,
Y, and Z coordinates of each node), based on the reference frames and the 2D
vectors along each crease.  This will be only one equation per crease.  There
will be an extra equation giving the X, Y, or Z coordinate of a known node.
I'll probably use the linear least squares methods, because I don't plan on
having that many creases, and I like reducing numerical error.  However, it is
unclear whether the accumulated numerical error will be significant.

## Data Structures

These data structures will be useful in the code.

* Original node locations in 2D (Z = 0)
* New node locations in 3D, at a given time step
* List of edges (pairs of node indices) to represent creases
* Crease angle for each edge
* For each node, a list of node neighbors, listed counter-clockwise as seen from
  "above" (on the +Z axis, looking in the -Z direction, at the original unfolded
  paper in the XY plane).
* Triangles (triples of node indices) useful for plotting later on, but also for
  calculating 3D locations from crease angles.

Because the topology of the nodes and creases does not change, the edges (pairs of
indices) and triangles (triples of indices) will not change during the folding
process.  Only the 3D node locations will change.

The list of edges will have to be augmented by a constrained Delaunay
triangulation to make sure that the square of paper is broken down into
triangles.  New edges/creases formed in this process can be kept at 180 degrees
throughout the fold; they don't have to bend.  They only exist for the
convenience of the person who will be rendering the origami later on a graphics
card, because they will only have to deal with triangles.  Constrained Delaunay
triangulations don't seem to be built into python, so I will use the external
package "triangle", available here: http://dzhelil.info/triangle/

## Functions to Implement

* Plot locations of nodes, with node labels
* Solve a node for crease angles
* Iterate through nodes to complete the solution
* Given a set of edges, find a set of triangles to represent the paper, 
  using those edges
* Given a set of crease angles, and a single triangle to hold fixed, 
  find 3D locations of nodes
* Render 3D origami, given triangles and 3D node locations.
  This is harder, since it requires picking a camera viewpoint, colors, output
  format, etc.



