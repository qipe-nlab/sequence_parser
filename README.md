# sequence_parser
Sequence Parser is a library supporting time-domain experiments.


Users can execute the Instructions defined as a class one after another and use Triggers to specify the synchronization relationship between ports.


Users also can partially customize the rules about time orders for instructions using the "with" grammar in python.


Sequence Parser will streamline experiments by increasing the reusability of pulse sequences.

## Usage

1. Import Modules
```python
import numpy as np
from sequence_parser.sequence import Sequence
from sequence_parser.port import Port
from sequence_parser.circuit import Circuit
from sequence_parser.backend import PortTable, GateTable, Backend
from sequence_parser.instruction import *
```

2. Most simple example
```python
seq = Sequence()
seq.add(Gaussian(amplitude=1, fwhm=50, duration=200), Port("Q0"))
seq.add(RaisedCos(amplitude=1, duration=200), Port("Q1"))
seq.trigger([Port("Q0"), Port("Q1")])
seq.add(Square(amplitude=1, duration=100), Port("Q2"))
```
instruction list included in seq can be visible with 
```python
print(seq)
```
then, you'll get as follows,
```
                                               Sequence Instruction List                                                
------------------------------------------------------------------------------------------------------------------------
  ID   |  Instruction Name                                                       |  Target Port                             
------------------------------------------------------------------------------------------------------------------------
  0    |  Gaussian                                                               |  Q0                                      
------------------------------------------------------------------------------------------------------------------------
  1    |  RaisedCos                                                              |  Q1                                      
------------------------------------------------------------------------------------------------------------------------
  2    |  Trigger                                                                |  [Q0, Q1]                                
------------------------------------------------------------------------------------------------------------------------
  3    |  Square                                                                 |  Q2                                      
```

3. Declare Preset Gates
```python
pt = PortTable()
pt._add_muxes([(0, [0,1,2,3])])
pt._add_edges([(0,1), (0,2), (1,3), (2,3)])

gt = GateTable()
for node in pt.nodes.values():
    rx90 = Sequence()
    with rx90.align(node.q, mode="left"):
        rx90.add(Gaussian(1, 10, 20, zero_end=True), node.q)
        rx90.add(Deriviative(Gaussian(0.3j, 10, 20, zero_end=True)), node.q)
    gt._add_gate("rx90", node.node, rx90)
    
    node.a.skew = -300
    meas = Sequence()
    meas.trigger([node.q, node.r, node.a])
    meas.add(FlatTop(Gaussian(1, 10, 40), top_duration=100), node.r)
    meas.add(Acquire(200), node.a)
    gt._add_gate("meas", node.node, meas)
    
for key, (impa, nodes) in pt.muxes.items():
    impa.skew = -50
    pump = Sequence()
    pump.add(FlatTop(Gaussian(1, 10, 40), top_duration=80), impa)
    gt._add_gate("pump", key, pump)
    
for key, edge in pt.edges.items():
    qc = pt.nodes[key[0]]
    qt = pt.nodes[key[1]]

    edge.skew = 30
    rzx45 = Sequence()
    rzx45.trigger([qc.q,qt.q,qc>>qt])
    rzx45.add(FlatTop(RaisedCos(amplitude=+1, duration=20), top_duration=100), qc>>qt)
    rzx45.add(FlatTop(RaisedCos(amplitude=+1, duration=20), top_duration=100), qt.q)
    rzx45.trigger([qc.q,qt.q,qc>>qt])
    gt._add_gate("rzx45", key, rzx45)
    
backend = Backend()
backend.add_port_table(pt)
backend.add_gate_table(gt)
```

4. Run Circuit
```python
cir = Circuit(backend)
cir.icnot(0,1)
cir.cnot(2,3)
cir.icnot(0,2)
cir.cnot(1,3)
cir.measurements([0,3])
cir.icnot(0,1)
cir.cnot(2,3)
cir.icnot(0,2)
cir.cnot(1,3)
cir.measurements([0,3])
```

5. Plot waveforms
```python
cir.draw(reflect_skew=False)
```
![Pulse sequence](/figures/circuit.png)

6. Declare and Update Variable
```python
from sequence_parser.variable import Variable, Variables

v1 = Variable(name="amplitude_0", value_array=[0, 1.0], unit="")
v2 = Variable(name="phase", value_array=[0, 0.5*np.pi], unit="rad")
v3 = Variable(name="amplitude_1", value_array=[0, 0.5, 1.0], unit="")

var = Variables()
var.add([v1, v2]) # zip sweep for v1 and v2
var.add(v3)
var.compile()

seq = Sequence()
seq.add(VirtualZ(phase=v2), Port("Q1"))
seq.add(Gaussian(amplitude=v1, fwhm=10, duration=30), Port("Q1"))
seq.add(FlatTop(Gaussian(amplitude=v3), top_duration=100), Port("Q2"))
for update_command in var.update_command_list:
    seq.update_variables(update_command)
    seq.compile()
```

7. Run Circuit with the Measurement tools
```python
import measurement_tool as mt
session = mt.Session(
    labrad_hostname = "host_name",
    labrad_password = "password",
    labrad_username = "username",
    cooling_down_id = "example",
    experiment_username = "username",
    package_name = "example",
)

from measurement_tool.datataking.time_domain_qubit_measurement_sequencer import TimeDomainQubitMeasurementSequencer
qm = TimeDomainQubitMeasurementSequencer(session)
circuits = [cir1, cir2, cir3, ...]
dataset = qm.take_data(circuits)
```

8. Dump and Load Circuit (setting can be saved in the Registry)
```python
setting = cir.dump_setting()
new_cir = Circuit()
new_cir.load_setting(setting)
```

## To Do List
- Add feature to get the summention of the several ports
- Add feature to execute "charp" as a instruction
