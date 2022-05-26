import numpy as np
from ..instruction import Instruction
from .pulse import Pulse
from .pulse_shape import PulseShape

class Functional(Pulse):
    def __init__(
        self,
        func,
        params,
        duration,
    ):
        super().__init__()
        self.pulse_shape = FunctionalShape()
        self.params = {
            "func" : func,
            "params" : params,
            "duration" : duration,
        }

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]
        
class FunctionalShape(PulseShape):
    def __init__(self):
        super().__init__()
        
    def set_params(self, pulse):
        self.func = pulse.tmp_params["func"]
        self.params = pulse.tmp_params["params"]
        self.duration = pulse.duration
        
    def model_func(self, time):
        waveform = self.func(self.params, self.duration, time)
        return waveform   
    
def rise(params, duration, time):
    amplitude = params
    phase = 0.5*np.pi - np.pi/duration*time
    waveform = 0.5*amplitude*(1 + np.cos(phase))
    return waveform

def down(params, duration, time):
    amplitude = params
    phase = 0.5*np.pi + np.pi/duration*time
    waveform = 0.5*amplitude*(1 + np.cos(phase))
    return waveform

def twist(params, duration, time):
    amplitude = params
    phase = 0.5*np.pi + np.pi/duration*time
    waveform = amplitude*np.exp(1j*phase)
    return waveform

def twist_minus(params, duration, time):
    amplitude = params
    phase = - 0.5*np.pi - np.pi/duration*time
    waveform = amplitude*np.exp(1j*phase)
    return waveform

def step_twist(params, duration, time):
    amplitude = params
    ftime = time[time < 0]
    btime = time[time >= 0]
    fphase = 2*np.pi/duration**2*(ftime + duration/2)**2
    bphase = np.pi - 2*np.pi/duration**2*(btime - duration/2)**2
    phase = np.hstack([fphase, bphase])
    waveform = amplitude*np.exp(1j*phase)
    return waveform

def step_twist_minus(params, duration, time):
    amplitude = params
    ftime = time[time < 0]
    btime = time[time >= 0]
    fphase = - 2*np.pi/duration**2*(ftime + duration/2)**2
    bphase = - (np.pi - 2*np.pi/duration**2*(btime - duration/2)**2)
    phase = np.hstack([fphase, bphase])
    waveform = amplitude*np.exp(1j*phase)
    return waveform

def cos_twist(params, duration, time):
    amplitude = params
    phase = np.pi/duration*(time+0.5*duration) + 0.5*np.sin(2*np.pi/duration*time)
    waveform = amplitude*np.exp(+1j*phase)
    return waveform

def cos_twist_minus(params, duration, time):
    amplitude = params
    phase = np.pi/duration*(time+0.5*duration) + 0.5*np.sin(2*np.pi/duration*time)
    waveform = amplitude*np.exp(-1j*phase)
    return waveform

def raised_cos_flattop_minus(params, duration, time):
    amplitude, edge = params
    top = duration - 2*edge
    detuning = np.pi/(top + edge)

    ftime = time[time < -0.5*top] + 0.5*top
    ctime = time[abs(time) <= 0.5*top] + 0.5*top
    btime = time[time > +0.5*top] - 0.5*top

    ftheta = np.pi/edge*ftime
    btheta = np.pi/edge*btime

    fphase = 0.5*edge/(top+edge)*(ftheta + np.pi + np.sin(ftheta))
    cphase = 0.5*edge/(top+edge)*np.pi + ctime * detuning
    bphase = top * detuning + 0.5*edge/(top+edge)*(btheta + np.pi + np.sin(btheta))

    phase = np.hstack([fphase, cphase, bphase])
    waveform = amplitude * np.exp(-1j*phase)
    return waveform