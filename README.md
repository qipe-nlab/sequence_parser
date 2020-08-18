# sequence_parser
Parser for pulse sequence declared as  the Classes

## Usage

1. Declares the Instructions used for the Sequence
```python
import numpy as np
from sequence_parser.variable import Variable, Variables
from sequence_parser.sequence import Sequence
from sequence_parser.port import Port
from sequence_parser.instruction import *

# Variables
amp1 = Variable(name="amplitude1", value_array=np.linspace(0,1,2), unit="")
amp2 = Variable(name="amplitude2", value_array=np.linspace(0,1,2), unit="")
amp3 = Variable(name="amplitude3", value_array=np.linspace(0,1,2), unit="")
var = Variables()
var.add([amp1,amp2])
var.add(amp3)
var.compile()

# Ports
port1 = Port(name="port1")
port2 = Port(name="port2")
port3 = Port(name="port3")
port4 = Port(name="port4")

# Pulses
truncated_gaussian = Gaussian(zero_end=True)
square = Square(amplitude=amp1)
raisedcosflattop = FlatTop(RaisedCos(amplitude=amp2), top_duration=200)
drag = Union([Gaussian(amplitude=amp3), Deriviative(Gaussian(amplitude=1j))])

# Commands
vz = VirtualZ(0.5*np.pi)
shift_freq = ShiftFrequency(0.03) # GHz
fix_freq = ShiftFrequency(0)
delay = Delay(100)

# Demodulation windows
acquire1 = Acquire(duration=300)
acquire2 = Acquire(duration=350)
```

2. Declares Sequence and adds Instructions into the Sequence
```python
# Declare sub sequence
sub = Sequence()
sub.add(delay, port3)
sub.add(drag, port3)
sub.add(delay, port3)
sub.add(drag, port3)

# Declare main sequence
seq = Sequence()
seq.trigger([port1, port2], align="right")
seq.add(acquire1, port1)
seq.add(acquire2, port3)
seq.trigger([port1, port2, port3, port4])
seq.add(truncated_gaussian, port1)
seq.add(raisedcosflattop, port2)
seq.trigger([port1, port2, port4])
seq.add(truncated_gaussian, port1)
seq.add(shift_freq, port2)
seq.add(drag, port2)
seq.add(fix_freq, port2)
seq.add(vz, port3)

# user can call the sub sequence in the other sequence
seq.call(sub)

seq.add(truncated_gaussian, port4)
seq.add(vz, port4)
seq.add(raisedcosflattop, port4)
seq.add(vz, port4)
seq.trigger([port1, port3, port4])
seq.add(square, port2)
seq.add(shift_freq, port3)
seq.add(truncated_gaussian, port2)
seq.add(raisedcosflattop, port3)
seq.add(fix_freq, port3)
seq.trigger([port1, port2, port3, port4])
seq.add(acquire1, port2)
seq.add(acquire2, port4)
```

3. Compile Sequence and get waveform
```python
# compile sequence and plot waveform while sweeping the variables
for update_command in var.update_command_list:
    seq.update_variables(update_command)
    seq.compile()
    seq.plot_waveform()
```

![Pulse sequence](/figures/pulse_sequence.png)

4. I/O with the Measurement tools
```python
# get waveform information
waveform_info = seq.get_waveform_information()

# dump and load sequence setting
setting = seq.dump_setting()
new_seq = Sequence()
new_seq.load_setting(setting)
```

## To Do
- Add reference phase-locking system between different ports (ex. cross resonance port and target qubit port)
- Add experiment injection feature to insert recalibration of the IQ projector
- Add preset gates e.g. RX90, RZX45
