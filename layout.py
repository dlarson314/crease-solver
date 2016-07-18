import re
import numbers

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
        crease_angles = [np.acos(cosB), np.acos(cosC), np.acos(cosA)]
        # Convert back to degrees
        crease_angles = [np.mod(x * 180 / np.pi + 360, 360) for x in crease_angles]
        # Find alternate solution
        opposites = [360 - x for x in crease_angles]

        if sum(non_numbers) == 3:
            return (crease_angles, opposites)
        else:
            # Check to see if this matches input crease angles?
            return (crease_angles, opposites)


    return crease_angles


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
    foo()




