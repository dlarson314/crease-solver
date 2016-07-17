import re

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
    neighbors = {}
    for i in range(crease_list.shape[0]):    
        node0 = crease_list[i,0]
        node1 = crease_list[i,1]
        if node0 in neighbors:
            neighbors[node0].add(node1)
        else:
            neighbors[node0] = set([node1])
        if node1 in neighbors:
            neighbors[node1].add(node0)
        else:
            neighbors[node1] = set([node0])
    
    nodes = neighbors.keys()
    for n in nodes:
        node_neighbors = np.array(list(neighbors[n]), dtype='int32')
        vectors = node_list[node_neighbors,:]
        vectors = vectors - np.tile(node_list[n,:], (len(node_neighbors),1))
        angles = np.arctan2(vectors[:,1], vectors[:,0])
        indices = np.argsort(angles)
        node_neighbors = node_neighbors[indices]
        neighbors[n] = node_neighbors

    return neighbors


def foo():
    node_list, crease_list, crease_types = load_creasepattern('test.creasepattern')
    #print node_list
    #print crease_list

    neighbors = get_neighbors(node_list, crease_list) 
    print neighbors

    plot_creasepattern(node_list, crease_list, crease_types)




    


if __name__ == "__main__":
    foo()




