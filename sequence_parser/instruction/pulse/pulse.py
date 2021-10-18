import numpy as np
from ..instruction import Instruction
from .pulse_shape import SquareShape, GaussianShape, RaisedCosShape, DeriviativeShape, FlatTopShape


class Pulse(Instruction):
    def __init__(self):
        super().__init__()
        self.pulse_shape = None
        self.position = None
        self.phase = None
        self.detuning = None
        self.duration = None

    def _get_duration(self):
        raise NotImplementedError()

    def _fix_duration(self):
        for inst in self.insts.values():
            inst._fix_duration()
        self._get_duration()

    def _fix_pulseshape(self):
        for inst in self.insts.values():
            inst._fix_pulseshape()
        self.pulse_shape.set_params(self)

    def _execute(self, port):
        self._fix_duration()
        self.position = port.position
        self.phase = port.phase
        self.detuning = port.detuning
        port._time_step(self.duration)

    def _write(self, port):
        self._fix_pulseshape()
        relative_time = port.time - (self.position + self.duration / 2)
        support = (-self.duration / 2 <= relative_time) & (relative_time < self.duration / 2)
        envelope = self.pulse_shape.model_func(relative_time[support])
        if_freq = port.if_freq + self.detuning
        phase_factor = np.exp(-1j * (2*np.pi * if_freq * port.time[support] + self.phase))
        waveform = phase_factor * envelope
        port.waveform[support] += waveform

class Square(Pulse):
    def __init__(
        self,
        amplitude = 1,
        duration = 100,
    ):
        super().__init__()
        self.pulse_shape = SquareShape()
        self.params = {
            "amplitude" : amplitude,
            "duration" : duration
        }

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]

class Gaussian(Pulse):
    def __init__(
        self,
        amplitude = 1,
        fwhm = 30,
        duration = 100,
        zero_end = False,
    ):
        super().__init__()
        self.pulse_shape = GaussianShape()
        self.params = {
            "amplitude" : amplitude,
            "fwhm" : fwhm,
            "duration" : duration,
            "zero_end" : zero_end
        }

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]

class RaisedCos(Pulse):
    def __init__(
        self,
        amplitude = 1,
        duration = 100,
    ):
        super().__init__()
        self.pulse_shape = RaisedCosShape()
        self.params = {
            "amplitude" : amplitude,
            "duration" : duration
        }
        
    def _get_duration(self):
        self.duration = self.tmp_params["duration"]

class Deriviative(Pulse):
    def __init__(
        self,
        pulse,
    ):
        super().__init__()
        self.pulse_shape = DeriviativeShape()
        self.params = {}
        self.insts = {0 : pulse}

    def _get_duration(self):
        self.duration = self.insts[0].duration

class FlatTop(Pulse):
    def __init__(
        self,
        pulse,
        top_duration = 200,
    ):
        super().__init__()
        self.pulse_shape = FlatTopShape()
        self.params = {"top_duration" : top_duration}
        self.insts = {0 : pulse}

    def _get_duration(self):
        self.duration = self.tmp_params["top_duration"] + self.insts[0].duration