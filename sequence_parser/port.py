import copy
import numpy as np
from .instruction.trigger import Trigger
from .instruction.acquire import Acquire
from .instruction.pulse.pulse import Pulse
from .instruction.command import Delay
from .instruction.functional import Container

class Port:
    """Port management class for timedomain measurement"""

    def __init__(self, name, if_freq=0.25):
        """initial setting of the Port
        Args:
            name (str): port name
            if_freq (float): IF frequency in GHz
        """
        self.name = name
        self.if_freq = if_freq # GHz
        self.DAC_STEP = 1.0 # ns
        self.skew = 0.0 # ns
        self.skew_delay = 0.0 # ns
        self._reset()

    def __repr__(self):
        return str(self.name)

    def __str__(self):
        return str(self.name)

    def _reset(self):
        """Initialize all elements
        """
        self.instruction_list = []
        self.syncronized_instruction_list = None
        self.waveform = None
        self.measurement_windows = []
        self._execute_reset()

    def _execute_reset(self):
        """Initialize several elements overwritten by the execute function
        """
        self.position = 0
        self.phase = 0
        self.detuning = 0
        self.align_modes = [("sequential", [])]

    def _add(self, instruction):
        """Add Instruction into the instruction_list
        Args:
            instruction (Instruction): Pulse, Command, or Trigger
        """
        if isinstance(instruction, Container):
            instruction = instruction.inst
        self.instruction_list.append(instruction)

    def _time_step(self, duration):
        """Progress position of the Port
        Args:
            duration (float): progress time

        """
        if self.align_modes[-1][0] == "sequential":
            self.align_modes[-1][1].append(duration)
            self.position += duration
        if self.align_modes[-1][0] == "left":
            self.align_modes[-1][1].append(duration)

    def _get_trigger_edge_list(self):
        """Evaluate the minimum duration between neighboring Triggers

        Returns:
            trigger_edge_list (list): list of the minimum duration between neighboring Triggers
        """
        self._execute_reset()
        self.trigger_node_list = []
        for instruction in self.instruction_list:
            instruction._execute(self)
            if isinstance(instruction, Trigger):
                self.trigger_node_list.append((instruction.trigger_index, self.position))

        self.trigger_edge_list = []
        for i in range(len(self.trigger_node_list)-1):
            trigger_index_1, trigger_position_1 = self.trigger_node_list[i]
            trigger_index_2, trigger_position_2 = self.trigger_node_list[i+1]
            self.trigger_edge_list.append((trigger_index_1, trigger_index_2, trigger_position_2 - trigger_position_1))
        return copy.deepcopy(self.trigger_edge_list)

    def _sync_trigger_position(self, trigger_position):
        """Syncronize the positions of the Triggers with the trigger_position
        Args:
            trigger_position (list): list of the positions of the Triggers after syncronization with other ports
        """
        edge_delay = {}
        for fnode, bnode, weight in self.trigger_edge_list:
            delay = (trigger_position[bnode] - trigger_position[fnode]) - weight
            edge_delay[bnode] = delay

        self.syncronized_instruction_list = []
        trigger_edge_list = []
        for instruction in self.instruction_list:
            if isinstance(instruction, Trigger):
                if instruction.trigger_index == 0:
                    last_align = "left"
                else:
                    delay = edge_delay[instruction.trigger_index]
                    if last_align == "left":
                        bdelay = Delay(delay)
                        bdelay._fix_variable()
                        trigger_edge_list = trigger_edge_list + [bdelay]
                    elif last_align == "middle":
                        fdelay = Delay(0.5*delay)
                        fdelay._fix_variable()
                        bdelay = Delay(0.5*delay)
                        bdelay._fix_variable()
                        trigger_edge_list = [fdelay] + trigger_edge_list + [bdelay]
                    elif last_align == "right":
                        fdelay = Delay(delay)
                        fdelay._fix_variable()
                        trigger_edge_list = [fdelay] + trigger_edge_list
                    else:
                        raise KeyError(f"align : {last_align} (trigger {instruction.trigger_index}) is not implemented. please use [left, middle, right].")
                    self.syncronized_instruction_list += trigger_edge_list + [instruction]
                    last_align = instruction.align
                    trigger_edge_list = []
            trigger_edge_list.append(instruction)
            
    def _sync_skew(self, delay):
        """Syncronize the skew from other ports
        Args:
            delay (float) : wait time (ns) to syncronize skew with other ports
        """
        self.skew_delay = delay
        initial_delay = Delay(delay)
        initial_delay._fix_variable()
        self.syncronized_instruction_list.insert(0, initial_delay)

    def _execute_instructions(self):
        """Execute all instructions
        """
        self._execute_reset()
        for instruction in self.syncronized_instruction_list:
            instruction._execute(self)

    def _write_waveform(self, waveform_length):
        """Write waveform by the Pulse instructions
        Args:
            waveform_length (float): total waveform time length
        """
        self.time = np.arange(0, waveform_length, self.DAC_STEP)
        self.waveform = np.zeros(self.time.size, dtype=np.complex128)
        
        for instruction in self.syncronized_instruction_list:
            if isinstance(instruction, Pulse):
                instruction._write(self, out=self.waveform)
            if isinstance(instruction, Acquire):
                instruction._acquire(self)
            else:
                pass
            
        if np.max(np.abs(self.waveform)) > 1.001:
            print(f'sequence amplitude should be below 1 (Port : {self.name}).')
