# sequence_parser
Sequence Parser is a library supporting time-domain experiments.


Users can execute the Instructions defined as a class one after another and use Triggers to specify the synchronization relationship between ports.


Users also can partially customize the rules about time orders for instructions using the "with" grammar in python.


Sequence Parser will streamline experiments by increasing the reusability of pulse sequences.

## Usage

1. Import Modules
```python
import numpy as np
from sequence_parser.variable import Variable, Variables
from sequence_parser.sequence import Sequence
from sequence_parser.port import Port
from sequence_parser.circuit import Circuit, ControlDict
from sequence_parser.instruction import *
```

2. Load Preset Gates (these are processed when creating calibration_note in measurement_tools)
```python
q1 = Port(name="q1")
q2 = Port(name="q2")
q3 = Port(name="q3")
q4 = Port(name="q4")
q5 = Port(name="q5")

r1 = Port(name="r1")
r2 = Port(name="r2")
r3 = Port(name="r3")
r4 = Port(name="r4")
r5 = Port(name="r5")

c21 = Port(name="c21")
c31 = Port(name="c31")
c41 = Port(name="c41")
c51 = Port(name="c51")

cd = ControlDict()
cd._add_sync(c21, (q2, q1))
cd._add_sync(c31, (q3, q1))
cd._add_sync(c41, (q4, q1))
cd._add_sync(c51, (q5, q1))

for port in [q1,q2,q3,q4,q5]:
    rx90 = Sequence()
    with rx90.align(port, mode="left"):
        rx90.add(Gaussian(amplitude=0.5), port)
        rx90.add(Deriviative(Gaussian(amplitude=2j)), port)
    rx90_setting = rx90.dump_setting()
    cd._add("rx90", port.name, rx90_setting)
    
for port in [(q1,c21),(q1,c31),(q1,c41),(q1,c51)]:
    rzx45 = Sequence()
    rzx45.add(FlatTop(RaisedCos(amplitude=0.1, duration=10), top_duration=300), port[0])
    rzx45.add(FlatTop(RaisedCos(amplitude=0.8*np.exp(0.125j*np.pi), duration=10), top_duration=300), port[1])
    rzx45_setting = rzx45.dump_setting()
    cd._add("rzx45", port[1].name, rzx45_setting)

for port in [r1,r2,r3,r4,r5]:
    meas = Sequence()
    with meas.align(port, mode="left"):
        meas.add(FlatTop(RaisedCos(amplitude=0.5, duration=10), top_duration=500), port)
        with meas.align(port, mode="sequencial"):
            meas.add(Delay(100), port)
            meas.add(Acquire(duration=300), port)
    meas_setting = meas.dump_setting()
    cd._add("meas", port.name, meas_setting)
```

3. Run Circuit
```python
cir = Circuit()
cir._apply(cd)
for _ in range(3):
    cir.trigger([r1, q1,q2,q3,q4,q5], align="middle")
    cir.measurement(r1)
    cir.trigger([r1, q1,q2,q3,q4,q5])
    cir.cnot(c21)
    cir.cnot(c31)
    cir.cnot(c41)
    cir.cnot(c51)
cir.trigger([r1, q1,q2,q3,q4,q5], align="middle")
cir.measurement(r1)
```

4. Plot waveforms
```python
cir.draw()
```
![Pulse sequence](/figures/circuit.png)

5. Declare and Update Variable
```python
v1 = Variable(name="instruction", value_array=[Gaussian(), RaisedCos()], unit="")
v2 = Variable(name="phase", value_array=[0, 0.5*np.pi], unit="rad")
v3 = Variable(name="amplitude", value_array=[0, 0.5, 1.0], unit="")
var = Variables()
var.add([v1, v2]) # zip sweep for v1 and v2
var.add(v3)
var.compile()

cir = Circuit()
cir.add(VirtualZ(phi=v2), q1)
cir.add(Gaussian(amplitude=v1), q1)
cir.add(FlatTop(Gaussian(amplitude=v3), top_duration=1000), q2)
for update_command in var.update_command_list:
    cir.update_variables(update_command)
    cir.compile()
```

6. Run Circuit with the Measurement tools
```python
# get waveform information
waveforms = cir.get_waveform_information()

import measurement_tool as mt
from measurement_tool.sequence.sequence_external import ExternalSequence
session = mt.Session(
    labrad_hostname = "host_name",
    labrad_password = "password",
    labrad_username = "username",
    cooling_down_id = "example",
    experiment_username = "username",
    package_name = "example",
)
control.sequencer = control.seq = ExternalSequence(session)
control = mt.QubitMeasurement(session)
control.sequencer.set_waveforms(waveforms)
dataset = control.take_data("test")
```

7. Dump and Load Circuit (setting can be saved in the Registry)
```python
setting = cir.dump_setting()
new_cir = Circuit()
new_cir.load_setting(setting)
```

## To Do List
- Add feature to bind the control port and the readout port of the same qubit, such as "cd._define_qubit(q0,r0)"
- Add feature to get the summention of the several ports to represent the multiplexed readout port, such as "cd._define_mux(cavity=[r0,r1,r2,r3], pump=[p0])"
- Add feature to sweep variable Sequence, such as "cir.vcall"
- Add feature to save the variable on the registry, such as "var.dump_setting()"
