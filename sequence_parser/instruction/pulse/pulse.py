import numpy as np
from ..instruction import Instruction
from .pulse_shape import SquareShape, GaussianShape, RaisedCosShape, DeriviativeShape, FlatTopShape, UnionShape, AdjointShape

def charp(time, envelope, frequency, phase):
    phase_factor = np.exp(1j*(2*np.pi*frequency*time + phase))
    waveform = phase_factor * envelope
    return waveform

class Pulse(Instruction):
    def __init__(self):
        super().__init__()
        self.type = "Pulse"
        self.pulse_shape = None
        self.position = None
        self.phase = None
        self.detuning = None

    def _execute(self, port):
        self.position = port.position
        self.phase = port.phase
        self.detuning = port.detuning
        port.position += self.duration

    def _write(self, port):
        pulse_region = abs(port.time - (self.position + 0.5*self.duration)) < 0.5*self.duration
        charp_time = port.time[pulse_region]
        charp_envelope = self.pulse_shape.model_func(port.time[pulse_region]  - (self.position + 0.5*self.duration))
        charp_frequency = port.SIDEBAND_FREQ + self.detuning
        charp_phase = self.phase
        waveform = charp(charp_time, charp_envelope, charp_frequency, charp_phase)
        port.waveform[pulse_region] += waveform

class Square(Pulse):
    def __init__(
        self,
        amplitude = 1,
        duration = 100,
    ):
        super().__init__()
        self.name = "Square"
        self.duration = duration
        self.pulse_shape = SquareShape(
            amplitude = amplitude,
            duration = duration,
        )
        self.input_params = {
            "amplitude" : amplitude,
            "duration" : duration
        }

class Gaussian(Pulse):
    def __init__(
        self,
        amplitude = 1,
        fwhm = 30,
        duration = 100,
        zero_end = False,
    ):
        super().__init__()
        self.name = "Gaussian"
        self.duration = duration
        self.pulse_shape = GaussianShape(
            amplitude = amplitude,
            fwhm = fwhm,
            duration = duration,
            zero_end = zero_end,
        )
        self.input_params = {
            "amplitude" : amplitude,
            "fwhm" : fwhm,
            "duration" : duration,
            "zero_end" : False
        }

class RaisedCos(Pulse):
    def __init__(
        self,
        amplitude = 1,
        duration = 100,
    ):
        super().__init__()
        self.name = "RaisedCos"
        self.duration = duration
        self.pulse_shape = RaisedCosShape(
            amplitude = amplitude,
            duration = duration
        )
        self.input_params = {
            "amplitude" : amplitude,
            "duration" : duration
        }

# OverRideClass

class Deriviative(Pulse):
    def __init__(
        self,
        pulse,
    ):
        super().__init__()
        self.name = "Deriviative"
        self.pulse = pulse
        self.duration = pulse.duration
        self.pulse_shape = DeriviativeShape(
            pulseshape = self.pulse.pulse_shape
        )
        self.input_params = {
            "pulse" : pulse
        }

class FlatTop(Pulse):
    def __init__(
        self,
        pulse,
        top_duration = 200,
        edge_duration = 100,
    ):
        super().__init__()
        self.name = "FlatTop"
        self.pulse = pulse
        self.duration = top_duration + edge_duration
        self.pulse_shape = FlatTopShape(
            pulseshape = self.pulse.pulse_shape,
            top_duration = top_duration,
            edge_duration = edge_duration
        )
        self.input_params = {
            "pulse" : {pulse.name : pulse.input_params},
            "top_duration" : top_duration,
            "edge_duration" : edge_duration,
        }

# UnionClass

class Adjoint(Pulse):
    def __init__(
        self,
        pulse_list
    ):
        super().__init__()
        self.name = "Adjoint"
        self.pulse_list = pulse_list
        self.duration = sum([pulse.duration for pulse in pulse_list])
        self.pulse_shape = AdjointShape(
            pulseshape_list = [pulse.pulse_shape for pulse in pulse_list]
        )
        self.input_params = {
            "pulse_list" : [{pulse.name : pulse.input_params} for pulse in pulse_list]
        }

class Union(Pulse):
    def __init__(
        self,
        pulse_list
    ):
        super().__init__()
        self.name = "Union"
        self.pulse_list = pulse_list
        self.duration = max([pulse.duration for pulse in pulse_list])
        self.pulse_shape = UnionShape(
            pulseshape_list = [pulse.pulse_shape for pulse in pulse_list]
        )
        self.input_params = {
            "pulse_list" : [{pulse.name : pulse.input_params} for pulse in pulse_list]
        }