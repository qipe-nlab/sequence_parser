# sequence_parser
Sequence Parser is a library supporting time-domain experiments.
Users can execute the Instructions defined as a class one after another and use Triggers to specify the synchronization relationship between ports.
Users also can partially customize the rules about time orders for instructions using the "with" grammar in python.
Sequence Parser will streamline your experiments by dramatically increasing the reusability of pulse sequences.

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
r1 = Port(name="r1")
r2 = Port(name="r2")
c12 = Port(name="c12")

cd = ControlDict()
cd._add_sync(c12, (q1, q2))

for port in [q1, q2]:
    rx90 = Sequence()
    with rx90.align(port, mode="left"):
        rx90.add(Gaussian(amplitude=0.5), port)
        rx90.add(Deriviative(Gaussian(amplitude=5j)), port)
    rx90_setting = rx90.dump_setting()
    cd._add("rx90", port.name, rx90_setting)
    
for port in [c12]:
    rzx45 = Sequence()
    rzx45.add(FlatTop(RaisedCos(amplitude=0.8, duration=10), top_duration=300), port)
    rzx45_setting = rzx45.dump_setting()
    cd._add("rzx45", port.name, rzx45_setting)

for port in [r1, r2]:
    meas = Sequence()
    with meas.align(port, mode="left"):
        meas.add(FlatTop(RaisedCos(amplitude=0.5, duration=10), top_duration=400), port)
        with meas.align(port, mode="sequencial"):
            meas.add(Delay(100), port)
            meas.add(Acquire(duration=300), port)
    meas_setting = meas.dump_setting()
    cd._add("meas", port.name, meas_setting)
```

3. Declare Variables
```python
v1 = Variable(name="instruction", value_array=[Gaussian(), RaisedCos()], unit="")
v2 = Variable(name="phase", value_array=[0, 0.5*np.pi], unit="rad")
v3 = Variable(name="amplitude", value_array=[0, 0.5, 1.0], unit="")
var = Variables()
var.add([v1, v2]) # zip sweep for v1 and v2
var.add(v3)
var.compile()
```

4. Run Circuit
```python
cir = Circuit()
cir._apply(cd)
cir.rx90(q1)
cir.trigger([q1, q2, c12, r1, r2])
cir.rz(0.5*np.pi, q2)
cir.rzx90(c12)
cir.trigger([q1, q2, c12, r1, r2])
cir.rx90(q2)
cir.add(Container(inst=v1), q2)
cir.trigger([q1, q2, c12, r1, r2])
cir.measurement(r1)
cir.measurement(r2)
```

3. Update Variable and Compile Sequence
```python
for update_command in var.update_command_list:
    cir.update_variables(update_command)
    cir.compile()
```

3. Plot waveforms
```python
cir.plot_waveform()
```
![Pulse sequence](/figures/pulse_sequence.png)

4. I/O with the Measurement tools
```python
# get waveform information
waveform_information = cir.get_waveform_information()

# dump and load sequence setting
setting = cir.dump_setting()
new_cir = Circuit()
new_cir.load_setting(setting)
```

## To Do
- Add variable Sequence
