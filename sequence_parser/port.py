import copy
import numpy as np
from .instruction.trigger import Trigger
from .instruction.acquire import Acquire
from .instruction.pulse.pulse import Pulse
from .instruction.command import Delay
from .instruction.container import Container

class Port:
    """Port management class for timedomain measurement"""

    def __init__(self, name):
        """initial setting of the Port
        Args:
            name (str): port name
        """
        self.name = name
        self._reset()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def _reset(self):
        """Initialize all elements
        """
        self.instruction_list = []
        self.syncronized_instruction_list = None
        self.position = 0
        self.phase = 0
        self.detuning = 0
        self.DAC_STEP = 0.2 # ns
        self.SIDEBAND_FREQ = 0.25 # GHz
        self.waveform = None

    def _execute_reset(self):
        """Initialize several elements overwrited by the execute function
        """
        self.position = 0
        self.phase = 0
        self.detuning = 0

    def _add(self, instruction):
        """Add Instruction into the instruction_list
        Args:
            instruction (Instruction): Pulse, Command, or Trigger
        """
        self.instruction_list.append(instruction)

    def _get_trigger_edge_list(self):
        """Evaluate the minimum duration between neighbor Triggers

        Returns:
            trigger_edge_list (list): list of the minimum duration between the neighbor Triggers
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
        self.measurement_window_list = []
        for instruction in self.syncronized_instruction_list:
            if isinstance(instruction, Pulse) or (isinstance(instruction, Container) and isinstance(instruction.inst, Pulse)):
                instruction._write(self)
            if isinstance(instruction, Acquire) or (isinstance(instruction, Container) and isinstance(instruction.inst, Acquire)):
                self.measurement_window_list.append(instruction.measurement_window)
            else:
                pass