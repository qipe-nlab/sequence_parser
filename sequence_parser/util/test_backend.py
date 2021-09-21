import numpy as np
from ..sequence import Sequence
from ..port import Port
from ..backend import PortTable, GateTable, Backend
from ..instruction import *

nodes = [1,2,3]
edges = [(1,2), (2,3)]
muxs = {1:(1,2,3)}

pt = PortTable()
pt._add_nodes(nodes)
pt._add_edges(edges)

gt = GateTable()
for node, port in pt.nodes.items():
    rx90 = Sequence()
    with rx90.align(port.q, mode="left"):
        rx90.add(Gaussian(amplitude=0.5, fwhm=3, duration=10), port.q)
        rx90.add(Deriviative(Gaussian(amplitude=0.3j, fwhm=3, duration=10)), port.q)
    gt._add_gate("rx90", node, rx90)
    
for edge, port in pt.edges.items():
    rzx45 = Sequence()
    rzx45.add(FlatTop(RaisedCos(amplitude=0.1, duration=10), top_duration=50), pt.nodes[edge[1]].q)
    rzx45.add(FlatTop(RaisedCos(amplitude=0.8*np.exp(0.125j*np.pi), duration=10), top_duration=50), port)
    gt._add_gate("rzx45", edge, rzx45)
    
for node, port in pt.nodes.items():
    meas = Sequence()
    with meas.align(port.r, mode="left"):
        meas.add(FlatTop(RaisedCos(amplitude=0.2, duration=10), top_duration=100), port.r)
        with meas.align(port.r, mode="sequential"):
            meas.add(Delay(10), port.r)
            meas.add(Acquire(duration=80), port.r)
    gt._add_gate("meas", node, meas)
        
backend = Backend()
backend.add_port_table(pt)
backend.add_gate_table(gt)