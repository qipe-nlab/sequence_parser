import copy
from typing import Callable

import numpy as np

from .instruction.acquire import Acquire
from .instruction.pulse.pulse import Pulse
from .port import Port


class IQPort(Port):
    """A Port which compensates for the amplitude and delay imbalances of an IQ mixer"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i_factor = lambda freq: 1
        self.q_factor = lambda freq: 1
        self.i_delay = lambda freq: 0
        self.q_delay = lambda freq: 0

    def set_i_factor(self, i_factor: Callable[[float], float]):
        """multiply I waveform by `i_factor(if_freq)`"""
        self.i_factor = i_factor

    def set_q_factor(self, q_factor: Callable[[float], float]):
        """multiply Q waveform by `q_factor(if_freq)`"""
        self.q_factor = q_factor

    def set_i_delay(self, i_delay: Callable[[float], float]):
        """delay I waveform by `i_delay(if_freq)` ns"""
        self.i_delay = i_delay

    def set_q_delay(self, q_delay: Callable[[float], float]):
        """delay Q waveform by `q_delay(if_freq)` ns"""
        self.q_delay = q_delay

    def _write_waveform(self, waveform_length):
        """Write waveform by the Pulse instructions
        Args:
            waveform_length (float): total waveform time length
        """
        self.time = np.arange(0, waveform_length, self.DAC_STEP)
        i_waveform = np.zeros(self.time.size, dtype=np.complex128)
        q_waveform = np.zeros_like(i_waveform)
        for instruction in self.syncronized_instruction_list:
            if isinstance(instruction, Pulse):
                # get the compensation parameters at the IF frequency of the pulse
                if_freq = self.if_freq + self.detuning
                i_factor = self.i_factor(if_freq)
                q_factor = self.q_factor(if_freq)
                i_delay = self.i_delay(if_freq)
                q_delay = self.q_delay(if_freq)

                # compensate and write the I waveform
                i_pulse = copy.deepcopy(instruction)
                i_pulse.pulse_shape.amplitude *= i_factor
                i_pulse.position += i_delay
                i_pulse._write(self, out=i_waveform)

                # compensate and write the Q waveform
                q_pulse = copy.deepcopy(instruction)
                q_pulse.pulse_shape.amplitude *= q_factor
                q_pulse.position += q_delay
                q_pulse._write(self, out=q_waveform)

            elif isinstance(instruction, Acquire):
                instruction._acquire(self)

        self.waveform = i_waveform.real + 1j * q_waveform.imag
