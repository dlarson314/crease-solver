import re
import numbers
import unittest
import copy

import numpy as np
import matplotlib.pyplot as mpl

def load_creasepattern(filename):
    with open(filename) as f:
        lines = f.readlines()
        f.close()

    read_nodes = False
    read_creases = False
    node_list = []
    crease_list = []
    crease_types = []
    for line in lines:
        if re.search('begin', line):
            read_nodes = False 
            read_creases = False 
        if read_nodes:
            a = line.split(None, 2)       
            x = float(a[0])
            y = float(a[1])
            node_list.append((x, y))
        if read_creases:
            a = line.split(None, 2)       
            a0 = int(a[0])
            a1 = int(a[1])
            if len(a) > 2:
                crease_types.append(a[2].strip())
            else:
                crease_types.append('')
            crease_list.append((a0, a1))
        if re.search('begin nodes', line):
            read_nodes = True
        if re.search('begin creases', line):
            read_creases = True

    return (np.array(node_list), np.array(crease_list), crease_types)


def plot_creasepattern(node_list, crease_list, crease_types=None):
    if crease_types == None:
        crease_types = ['' for i in range(crease_list.shape[0])]
    mpl.figure()
    ax = mpl.subplot(1,1,1)
    mpl.plot(node_list[:,0], node_list[:,1], '.b')
    mpl.xlim((-0.05, 1.05))
    mpl.ylim((-0.05, 1.05))
    offset = 0.01
    for i in range(node_list.shape[0]):
        mpl.text(node_list[i,0]+offset, node_list[i,1]+offset, '%d' % i)
        
    for i, t in enumerate(crease_types): 
        # range(crease_list.shape[0]):
        x = node_list[crease_list[i,:],0]
        y = node_list[crease_list[i,:],1]
        #print t.upper()
        if t.upper() == 'M':
            mpl.plot(x, y, 'k')
        elif t.upper() == 'V':
            mpl.plot(x, y, '--k')
        else:
            mpl.plot(x, y, 'b')

    ax.set_aspect('equal')
    mpl.show()


def get_neighbors(node_list, crease_list):
    """
    neighbor_angles[n][0] gives the angle in degrees between the nodes
    neighbors[n][0] and neighbors[n][1].
    """
    neighbors = [[] for i in range(node_list.shape[0])]
    neighbor_angles = [[] for i in range(node_list.shape[0])]
    for i in range(crease_list.shape[0]):    
        node0 = crease_list[i,0]
        node1 = crease_list[i,1]
        neighbors[node0].append(node1)
        neighbors[node1].append(node0)

    for i in range(node_list.shape[0]):    
        # Remove duplicate neighbors
        node_neighbors = np.array(list(set(neighbors[i])), dtype='int32')
        # Determine angles to each neighbor
        vectors = node_list[node_neighbors,:]
        vectors = vectors - np.tile(node_list[i,:], (len(node_neighbors),1))
        angles = np.arctan2(vectors[:,1], vectors[:,0]) * 180 / np.pi
        # Sort the neighbors by angle
        indices = np.argsort(angles)
        angles = angles[indices]
        node_neighbors = node_neighbors[indices]
        # Find angles between neighbors
        angle_diffs = np.roll(angles, -1) - angles
        #print i
        #print np.roll(angles, -1)
        #print angles
        angle_diffs = np.mod(angle_diffs + 720, 360)
        neighbors[i] = node_neighbors
        neighbor_angles[i] = angle_diffs

    return neighbors, neighbor_angles


def find_opposite_side(A, b, c):
    """
    Solve a spherical triangle for side a opposite angle A.  Sides b and c are
    also given.  Return value will be between 0 and 180 degrees, inclusive.
    Input and output are in degrees.
    """
    eps = 1e-13  # angles smaller than this in degrees are considered zero
    if b < eps: return c
    if c < eps: return b
    d2r = np.pi / 180   # Convert degrees to radians
    cos_a = np.cos(b * d2r) * np.cos(c * d2r) + \
        np.sin(b * d2r) * np.sin(c * d2r) * np.cos(A * d2r)
    a = np.arccos(cos_a)
    # Convert back to degrees
    a = np.mod(a * 180 / np.pi + 360, 360)
    return a 


#def make_test_triangle(a_deg, b_deg, c_deg):
def solve_triangle_angles(a_deg, b_deg, c_deg):
    """
    Return angles opposites sidea a, b, and c, in a spherical triangle.
    Do internal tests for consistency.
    """
    # Convert to radians
    a = a_deg * np.pi / 180
    b = b_deg * np.pi / 180
    c = c_deg * np.pi / 180

    A = None

    eps = 1e-13
    assert(a >= 0)
    assert(b >= 0)
    assert(c >= 0)
    assert(a <= b + c)
    assert(b <= c + a)
    assert(c <= a + b)
    if a < eps and b < eps and c < eps:
        A, B, C = (60, 60, 60)
    elif a < eps:
        A, B, C = (0, 90, 90)
    elif b < eps:
        A, B, C = (90, 0, 90)
    elif c < eps:
        A, B, C = (90, 90, 0)
    
    if A == None:
        cosA = (np.cos(a) - np.cos(b) * np.cos(c)) / (np.sin(b) * np.sin(c))
        cosB = (np.cos(b) - np.cos(c) * np.cos(a)) / (np.sin(c) * np.sin(a))
        cosC = (np.cos(c) - np.cos(a) * np.cos(b)) / (np.sin(a) * np.sin(b))
        A = np.arccos(cosA) 
        B = np.arccos(cosB)
        C = np.arccos(cosC)

        # Check that these are all equal...
        ratio1 = np.sin(A) / np.sin(a)
        ratio2 = np.sin(B) / np.sin(b)
        ratio3 = np.sin(C) / np.sin(c)

        assert(np.fabs(ratio1 - ratio2) < eps)
        assert(np.fabs(ratio2 - ratio3) < eps)
        assert(np.fabs(ratio3 - ratio1) < eps)

        # Convert back to degrees
        A = A * 180 / np.pi
        B = B * 180 / np.pi
        C = C * 180 / np.pi

    return A, B, C


class TestSphericalTriangle(unittest.TestCase):
    def setUp(self):
        self.eps = 1e-13 

    def test1(self):
        a = find_opposite_side(10, 90, 90)
        self.assertTrue(np.fabs(a - 10) < self.eps)

        a = find_opposite_side(90, 90, 90)
        self.assertTrue(np.fabs(a - 90) < self.eps)

        a = find_opposite_side(180, 90, 90)
        self.assertTrue(np.fabs(a - 180) < self.eps)

        a = find_opposite_side(0, 90, 90)
        self.assertTrue(np.fabs(a - 0) < self.eps)

        # This doesn't work:
        #a = find_opposite_side(270, 90, 90)
        #self.assertTrue(np.fabs(a - 270) < self.eps)

    def test2(self):
        a = find_opposite_side(45, 0, 20)
        self.assertTrue(np.fabs(a - 20) < self.eps)

        a = find_opposite_side(45, 20, 0)
        self.assertTrue(np.fabs(a - 20) < self.eps)

        a = find_opposite_side(45, 0, 0)
        self.assertTrue(np.fabs(a - 0) < self.eps)

        a = find_opposite_side(0, 0, 0)
        self.assertTrue(np.fabs(a - 0) < self.eps)

        a = find_opposite_side(90, 0, 0)
        self.assertTrue(np.fabs(a - 0) < self.eps)

        a = find_opposite_side(0, 0, 20)
        self.assertTrue(np.fabs(a - 20) < self.eps)

        a = find_opposite_side(0, 20, 0)
        self.assertTrue(np.fabs(a - 20) < self.eps)

        a = find_opposite_side(90, 0, 20)
        self.assertTrue(np.fabs(a - 20) < self.eps)

        a = find_opposite_side(90, 20, 0)
        self.assertTrue(np.fabs(a - 20) < self.eps)

    def test3(self):
        a = find_opposite_side(90, 180, 180)
        self.assertTrue(np.fabs(a - 0) < self.eps)

        a = find_opposite_side(0, 180, 180)
        self.assertTrue(np.fabs(a - 0) < self.eps)

        a = find_opposite_side(180, 180, 180)
        self.assertTrue(np.fabs(a - 0) < self.eps)

    def test4(self):
        a = 30
        b = 40
        c = 50
        A, B, C = solve_triangle_angles(a, b, c)

        a2 = find_opposite_side(A, b, c)
        b2 = find_opposite_side(B, c, a)
        c2 = find_opposite_side(C, a, b)
        self.assertTrue(np.fabs(a - a2) < self.eps)
        self.assertTrue(np.fabs(b - b2) < self.eps)
        self.assertTrue(np.fabs(c - c2) < self.eps)

    def test5(self):
        a, b, c = 0, 10, 10
        A, B, C = solve_triangle_angles(a, b, c)
        self.assertTrue(np.amax(np.fabs(np.array([A, B, C]) - np.array([0, 90, 90]))) < self.eps)

        a, b, c = 10, 0, 10
        A, B, C = solve_triangle_angles(a, b, c)
        self.assertTrue(np.amax(np.fabs(np.array([A, B, C]) - np.array([90, 0, 90]))) < self.eps)

        a, b, c = 10, 10, 0
        A, B, C = solve_triangle_angles(a, b, c)
        self.assertTrue(np.amax(np.fabs(np.array([A, B, C]) - np.array([90, 90, 0]))) < self.eps)

        a, b, c = 0, 0, 0
        A, B, C = solve_triangle_angles(a, b, c)
        self.assertTrue(np.amax(np.fabs(np.array([A, B, C]) - np.array([60, 60, 60]))) < self.eps)

        a, b, c = 90, 90, 90
        A, B, C = solve_triangle_angles(a, b, c)
        self.assertTrue(np.amax(np.fabs(np.array([A, B, C]) - np.array([90, 90, 90]))) < self.eps)


    

def solve_node(neighbor_angles, crease_angles):
    """ 
    neighbor_angles and crease_angles are python lists of the same length,
    given in degrees.  neighbor_angles must sum to 360 degrees (only because we
    start with flat paper).  Three of the crease_angles should be None; these
    will be solved.

    As seen from above the paper (on the +Z axis, looking in the -Z direction),
    these are listed counter-clockwise.  neighbor_angles[0] is the arc length of
    the spherical polygon edge between the creases corresponding to
    crease_angles[0] and crease_angles[1].  So in order, counter-clockwise,
    alternating between arc lengths (wedges of paper) and creases, we have:

    crease_angles[0]    (crease goes to neighbors[i][0], by the way)
    neighbor_angles[0]  (constant angle of paper between crease 0 and crease 1)
    crease_angles[1]
    neighbor_angles[1]
    ...
    crease_angles[n-1]
    neighbor_angles[n-1]

    where neighbor_angles[n-1] is the angle between the creases corresponding to
    crease_angle[n-1] and crease_angle[0].

    Returns -1 if there are more than 3 unknowns (underconstrained problem)
    Returns -2 if there are 2 or fewer unknowns with inconsistent values
      (an overconstrained problem)
    Returns -3 if there are 3 unknowns but spherical triangle is unsolvable due
      to arc lengths
    Returns -4 if any neighbor_angle is > 180 degrees, which prevents folding
    Returns -5 if any neighbor_angle is < 0, which should never occur
    Returns a tuple of arrays of crease_angles with the two solutions, otherwise

    If multiple errors occur, only the first one encountered determines the
    return value.

    When a needed edge length is exactly zero, the solution with crease angles
    of 0, 90, and 90 is assumed (and requires the other two edge lengths to be
    equal).  However, if all three edge lengths are zero, crease angles of 60,
    60, and 60 are used.  In these cases, only one solution is returned, since
    the other is not effectively different.
    """

    non_numbers = [not(isinstance(x, numbers.Number)) for x in crease_angles]
    if sum(non_numbers) > 3:
        return -1

    assert(len(neighbor_angles) > 2)

    for i in range(neighbor_angles):
        if neighbor_angles[i] > 180.0:
            return -4
        if neighbor_angles[i] < 0:
            return -5

    # Solve the spherical triangle case.
    eps = 1e-13  # angles below this are considered zero radians
    if len(neighbor_angles) == 3:
        # Convert to radians, for the benefit of numpy trig functions

        # B = crease_angles[0] * np.pi / 180   # angle opposite side b
        a = neighbor_angles[0] * np.pi / 180
        # C = crease_angles[1] * np.pi / 180   # angle opposite side c
        b = neighbor_angles[1] * np.pi / 180
        # A = crease_angles[2] * np.pi / 180   # angle opposite side a
        c = neighbor_angles[2] * np.pi / 180  

        # Handle special cases
        if a > b + c: return -3
        if b > c + a: return -3
        if c > a + b: return -3
        if a < eps and b < eps and c < eps: return ([60, 60, 60],)
        if a < eps: return ([90, 90, 0],)
        if b < eps: return ([0, 90, 90],)
        if c < eps: return ([90, 0, 90],)

        # Solve spherical triangle
        cosA = (np.cos(a) - np.cos(b) * np.cos(c)) / (np.sin(b) * np.sin(c))
        cosB = (np.cos(b) - np.cos(c) * np.cos(a)) / (np.sin(c) * np.sin(a))
        cosC = (np.cos(c) - np.cos(a) * np.cos(b)) / (np.sin(a) * np.sin(b))
        crease_angles = [np.arccos(cosB), np.arccos(cosC), np.arccos(cosA)]
        # Convert back to degrees
        crease_angles = [np.mod(x * 180 / np.pi + 360, 360) for x in crease_angles]
        # Find alternate solution
        opposites = [360 - x for x in crease_angles]

        if sum(non_numbers) == 3:
            return (crease_angles, opposites)
        else:
            # Check to see if this matches input crease angles?
            return (crease_angles, opposites)
    else:
        # Implement recursion here.
        neighbor_angles2 = copy.copy(neighbor_angles)
        crease_angles2 = copy.copy(crease_angles)

        while not(isinstance(crease_angles2[i], numbers.Number)):
            i = i + 1

        angle = crease_angles2[i]
        del crease_angles2[i]

        # This still works if i == 0
        new_side = find_opposite_side(angle, neighbor_angles2[i-1],
            neighbor_angles[i])

        # Get all the angles
        A, B, C = solve_triangle_angles(new_side, neighbor_angles2[i-1],
            neighbor_angles[i])
        assert(np.fabs(angle - A) < eps)

        neighbor_angles2[i-1] = new_side
        del neighbor_angles2[i]

        # Now we can recurse.
        answers = solve_node(neighbor_angles2, crease_angles2)

        crease_angles = answers[0]
        crease_angles.insert(i, A)
        crease_angles[i-1] = crease_angles[i-1] + C
        if i+1 < len(crease_angles):
            crease_angles[i+1] = crease_angles[i+1] + B
        else:
            crease_angles[0] = crease_angles[0] + B

        if len(answers) > 1:
            opposites = answers[1]
            opposites.insert(i, A)
            opposites[i-1] = opposites[i-1] + C
            if i+1 < len(opposites):
                opposites[i+1] = opposites[i+1] + B
            else:
                opposites[0] = opposites[0] + B
       
        if len(answers) == 1:
            return (crease_angles,)
        else:
            return (crease_angles, opposites)


def foo():
    node_list, crease_list, crease_types = load_creasepattern('test.creasepattern')
    #print node_list
    #print crease_list

    neighbors, neighbor_angles = get_neighbors(node_list, crease_list) 
    #for i in range(len(neighbors)):
    #    print i
    #    print neighbors[i]
    #    print neighbor_angles[i]

    i = 4


    plot_creasepattern(node_list, crease_list, crease_types)



if __name__ == "__main__":
    #foo()
    unittest.main()




