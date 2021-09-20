from sequence_parser.variable import Variable
from typing import Optional, TypeVar, Union

import numpy as np
from sequence_parser.port import Port

from ..instruction import Instruction
from .pulse_shape import (DeriviativeShape, FlatTopShape, GaussianShape,
                          PulseShape, RaisedCosShape, SquareShape)


T = TypeVar('T')
MaybeVariable = Union[T, Variable[T]]


class Pulse(Instruction):
    pulse_shape: PulseShape
    position: float  # ns
    phase: float  # rad
    if_freq: float  # GHz
    duration: float  # ns

    def __init__(self, pulse_shape: PulseShape, if_freq: Optional[MaybeVariable[float]]):
        """if if_freq is None, it is set to port.SIDEBAND_FREQ + port.detuning during execution"""
        super().__init__()
        self.pulse_shape = pulse_shape
        self.params.update(if_freq=if_freq)

    def _get_duration(self):
        raise NotImplementedError

    def _fix_duration(self):
        for inst in self.insts.values():
            inst._fix_duration()
        self._get_duration()

    def _fix_pulseshape(self):
        for inst in self.insts.values():
            inst._fix_pulseshape()
        self.pulse_shape.set_params(self)

    def _execute(self, port: Port):
        self._fix_duration()
        self.position = port.position
        self.phase = port.phase
        if self.tmp_params['if_freq'] is None:
            self.if_freq = port.SIDEBAND_FREQ + port.detuning
        else:
            self.if_freq = self.tmp_params['if_freq']
        port._time_step(self.duration)

    def _write(self, port: Port):
        self._fix_pulseshape()
        relative_time = port.time - (self.position + 0.5*self.duration)
        support = abs(relative_time) < 0.5*self.duration
        envelope = self.pulse_shape.model_func(relative_time[support])
        phase_factor = np.exp(-1j*(2*np.pi*self.if_freq*port.time[support] + self.phase))
        waveform = phase_factor*envelope
        port.waveform[support] += waveform


class Square(Pulse):
    def __init__(
        self,
        amplitude: MaybeVariable[float] = 1,
        duration: MaybeVariable[float] = 100,
        if_freq: Optional[MaybeVariable[float]] = None,
    ):
        super().__init__(SquareShape(), if_freq)
        self.params.update(
            amplitude=amplitude,
            duration=duration,
        )

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]


class Gaussian(Pulse):
    def __init__(
        self,
        amplitude: MaybeVariable[float] = 1,
        fwhm: MaybeVariable[float] = 30,
        duration: MaybeVariable[float] = 100,
        zero_end: MaybeVariable[bool] = False,
        if_freq: Optional[MaybeVariable[float]] = None,
    ):
        super().__init__(GaussianShape(), if_freq)
        self.params.update(
            amplitude=amplitude,
            fwhm=fwhm,
            duration=duration,
            zero_end=zero_end,
        )

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]


class RaisedCos(Pulse):
    def __init__(
        self,
        amplitude: MaybeVariable[float] = 1,
        duration: MaybeVariable[float] = 100,
        if_freq: Optional[MaybeVariable[float]] = None,
    ):
        super().__init__(RaisedCosShape(), if_freq)
        self.params.update(
            amplitude=amplitude,
            duration=duration,
        )

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]


class Deriviative(Pulse):
    def __init__(
        self,
        pulse: Pulse,
    ):
        super().__init__(DeriviativeShape(), pulse.params['if_freq'])
        self.insts.update({0 : pulse})

    def _get_duration(self):
        self.duration = self.insts[0].duration


class FlatTop(Pulse):
    def __init__(
        self,
        pulse: Pulse,
        top_duration: MaybeVariable[float] = 200,
    ):
        super().__init__(FlatTopShape(), pulse.params['if_freq'])
        self.params.update(
            top_duration=top_duration,
        )
        self.insts.update({0 : pulse})

    def _get_duration(self):
        self.duration = self.tmp_params["top_duration"] + self.insts[0].duration
