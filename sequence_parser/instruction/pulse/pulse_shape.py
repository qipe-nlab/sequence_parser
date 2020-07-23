import copy
import numpy as np

class PulseShape:
    def __init__(self):
        self.time = None
        self.waveform = None
        self.duration = None

    def model_func(self, time):
        raise

class SquareShape(PulseShape):
    def __init__(
        self,
        amplitude = 1,
        duration = 100,
    ):
        self.amplitude = amplitude
        self.duration = duration

    def model_func(self, time):
        waveform = self.amplitude*np.ones(time.size)
        return waveform

class GaussianShape(PulseShape):
    def __init__(
        self,
        amplitude = 1,
        fwhm = 30,
        duration = 100,
        zero_end = True,
    ):
        self.amplitude = amplitude
        self.fwhm = fwhm
        self.duration = duration
        self.zero_end = zero_end

    def model_func(self, time):
        waveform = self.amplitude*np.exp(-4*np.log(2)*(time/self.fwhm)**2)
        if self.zero_end:
            edge = self.amplitude*np.exp(-4*np.log(2)*(0.5*self.duration/self.fwhm)**2)
            waveform = self.amplitude*(waveform - edge)/(self.amplitude - edge)
        return waveform

class RaisedCosShape(PulseShape):
    def __init__(
        self,
        amplitude = 1,
        duration = 100,
    ):
        self.amplitude = amplitude
        self.duration = duration

    def model_func(self, time):
        phase = np.pi*time/(0.5*self.duration)
        waveform = 0.5*self.amplitude*(1 + np.cos(phase))
        return waveform

class FlatTopShape(PulseShape):
    def __init__(
        self,
        pulseshape,
        top_duration = 200,
        edge_duration = 100,
    ):
        self.pulseshape = copy.deepcopy(pulseshape)
        self.pulseshape.duration = edge_duration
        self.top_duration = top_duration
        self.edge_duration = edge_duration
        self.duration = top_duration + edge_duration

    def model_func(self, time):
        ftime = time[np.where(time <= -0.5*self.top_duration)] + 0.5*self.top_duration
        btime = time[np.where(time >= +0.5*self.top_duration)] - 0.5*self.top_duration
        fwaveform = self.pulseshape.model_func(ftime)
        bwaveform = self.pulseshape.model_func(btime)
        mwaveform = self.pulseshape.amplitude*np.ones(time.size - ftime.size - btime.size)
        waveform = np.hstack([fwaveform, mwaveform, bwaveform])
        return waveform

class DeriviativeShape(PulseShape):
    def __init__(
        self,
        pulseshape,
    ):
        self.pulseshape = pulseshape
        self.duration = pulseshape.duration

    def model_func(self, time):
        waveform = self.pulseshape.model_func(time)
        return np.gradient(waveform)/np.gradient(time)

class UnionShape(PulseShape):
    def __init__(
        self,
        pulseshape_list,
    ):
        self.pulseshape_list = pulseshape_list
        self.duration = max([pulseshape.duration for pulseshape in pulseshape_list])

    def model_func(self, time):
        waveform = 0j
        for pulseshape in self.pulseshape_list:
            waveform += pulseshape.model_func(time)
        return waveform

class AdjointShape(PulseShape):
    def __init__(
        self,
        pulseshape_list,
    ):
        self.pulseshape_list = pulseshape_list
        self.duration = sum([pulseshape.duration for pulseshape in pulseshape_list])

    def model_func(self, time):
        cursor = -0.5*self.duration
        waveform_list = []
        for pulseshape in self.pulseshape_list:
            tmp_time = time[np.where((time - cursor >= 0) & (time - cursor <= pulseshape.duration))]
            waveform_list.append(pulseshape.model_func(tmp_time - cursor - 0.5*pulseshape.duration))
            cursor += pulseshape.duration
        waveform = np.hstack(waveform_list)
        return waveform