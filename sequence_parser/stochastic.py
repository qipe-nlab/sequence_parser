import numpy as np

class StochasticSequence:
    def __init__(self, seq, prob):
        self.seq = seq
        self.prob = prob
        
    def _fix_sequence(self):
        return np.random.choice(self.seq, p=self.prob)