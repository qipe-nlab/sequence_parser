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

class StepShape(PulseShape):
    def __init__(self):
        super().__init__()
        
    def set_params(self, pulse):
        self.amplitude = pulse.tmp_params["amplitude"]
        self.edge = pulse.tmp_params["edge"]
        self.duration = pulse.duration
        
    def model_func(self, time):
        ftime = time[np.where(time <= -0.5*self.edge)]
        btime = time[np.where(time >= +0.5*self.edge)]
        fwaveform = np.zeros(ftime.size)
        bwaveform = self.amplitude*np.ones(btime.size)
        mwaveform = np.linspace(0, self.amplitude, time.size - ftime.size - btime.size, dtype=np.complex128)
        waveform = np.hstack([fwaveform, mwaveform, bwaveform])
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

class HyperbolicSecantShape(PulseShape):
    def __init__(self):
        super().__init__()
        
    def set_params(self, pulse):
        self.amplitude = pulse.tmp_params["amplitude"]
        self.zero_end = pulse.tmp_params["zero_end"]
        self.fwhm = pulse.tmp_params["fwhm"]
        self.duration = pulse.duration
        
    def model_func(self, time):
        waveform = self.amplitude/np.cosh(2*np.log(2+3**0.5)/self.fwhm*time)
        if self.zero_end:
            edge = self.amplitude/np.cosh(2*np.log(2+3**0.5)/self.fwhm*0.5*self.duration)
            waveform = self.amplitude*(waveform - edge)/(self.amplitude - edge)
        if self.amplitude == 0:
            waveform = 0*time
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

class CRABShape(PulseShape):
    def __init__(self):
        super().__init__()
        
    def set_params(self, pulse):
        self.envelope_shape = copy.deepcopy(pulse.insts[0].pulse_shape)
        self.coefficients = pulse.coefficients
        self.polynominals = pulse.polynominals
        
    def model_func(self, time):
        envelope = self.envelope_shape.model_func(time)
        distortion = 0j
        for coeff, func in zip(self.coefficients, self.polynominals):
            distortion += coeff*func(time/max(abs(time)))
        waveform = distortion * envelope
        return waveform

class DeriviativeShape(PulseShape):
    def __init__(self):
        super().__init__()

    def set_params(self, pulse):
        self.pulseshape = copy.deepcopy(pulse.insts[0].pulse_shape)

    def model_func(self, time):
        waveform = self.pulseshape.model_func(time)
        return np.gradient(waveform)/np.gradient(time)

class ProductShape(PulseShape):
    def __init__(self):
        super().__init__()
        
    def set_params(self, pulse):
        self.pulseshape_a = copy.deepcopy(pulse.insts[0].pulse_shape)
        self.pulseshape_p = copy.deepcopy(pulse.insts[1].pulse_shape)
        
    def model_func(self, time):
        waveform_a = self.pulseshape_a.model_func(time)
        waveform_p = self.pulseshape_p.model_func(time)
        waveform = waveform_a * np.exp(1j*np.pi*waveform_p)
        return waveform