import copy
import numpy as np

class PulseShape:
    def __init__(self):
        pass

    def set_params(self):
        raise NotImplementedError()

    def model_func(self, time):
        raise NotImplementedError()

class SquareShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.amplitude = pulse.tmp_params["amplitude"]
        self.duration = pulse.duration

    def model_func(self, time):
        waveform = self.amplitude*np.ones(time.size)
        return waveform

class GaussianShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.amplitude = pulse.tmp_params["amplitude"]
        self.fwhm = pulse.tmp_params["fwhm"]
        self.zero_end = pulse.tmp_params["zero_end"]
        self.duration = pulse.duration

    def model_func(self, time):
        waveform = self.amplitude*np.exp(-4*np.log(2)*(time/self.fwhm)**2)
        if self.zero_end:
            edge = self.amplitude*np.exp(-4*np.log(2)*(0.5*self.duration/self.fwhm)**2)
            waveform = self.amplitude*(waveform - edge)/(self.amplitude - edge)
        return waveform

class RaisedCosShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.amplitude = pulse.tmp_params["amplitude"]
        self.duration = pulse.duration

    def model_func(self, time):
        phase = np.pi*time/(0.5*self.duration)
        waveform = 0.5*self.amplitude*(1 + np.cos(phase))
        return waveform

class FlatTopShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.pulseshape = copy.deepcopy(pulse.insts[0].pulse_shape)
        self.top_duration = pulse.tmp_params["top_duration"]

    def model_func(self, time):
        ftime = time[np.where(time <= -0.5*self.top_duration)] + 0.5*self.top_duration
        btime = time[np.where(time >= +0.5*self.top_duration)] - 0.5*self.top_duration
        fwaveform = self.pulseshape.model_func(ftime)
        bwaveform = self.pulseshape.model_func(btime)
        mwaveform = self.pulseshape.amplitude*np.ones(time.size - ftime.size - btime.size)
        waveform = np.hstack([fwaveform, mwaveform, bwaveform])
        return waveform

class DeriviativeShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.pulseshape = copy.deepcopy(pulse.insts[0].pulse_shape)

    def model_func(self, time):
        waveform = self.pulseshape.model_func(time)
        return np.gradient(waveform)/np.gradient(time)

class UnionShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.pulseshape_list = copy.deepcopy([pulse.pulse_shape for pulse in pulse.insts.values()])

    def model_func(self, time):
        waveform = 0j
        for pulseshape in self.pulseshape_list:
            waveform += pulseshape.model_func(time)
        return waveform

class AdjointShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.pulseshape_list = copy.deepcopy([pulse.pulse_shape for pulse in pulse.insts.values()])
        self.duration = pulse.duration

    def model_func(self, time):
        cursor = -0.5*self.duration
        waveform_list = []
        for pulseshape in self.pulseshape_list:
            tmp_time = time[np.where((time - cursor >= 0) & (time - cursor <= pulseshape.duration))]
            waveform_list.append(pulseshape.model_func(tmp_time - cursor - 0.5*pulseshape.duration))
            cursor += pulseshape.duration
        waveform = np.hstack(waveform_list)
        return waveform