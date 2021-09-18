import itertools
import numpy as np
import matplotlib.pyplot as plt
from .sequence import Sequence
from .instruction.instruction_parser import compose
from .instruction.command import VirtualZ, Delay
from .instruction.acquire import Acquire
from .instruction.align import _AlignManager
from .util.decompose import matrix_to_su2, matrix_to_su4
from sequence_parser.instruction import acquire

plt.rcParams['ytick.minor.visible'] = False
plt.rcParams['xtick.top']           = True
plt.rcParams['ytick.right']         = True
plt.rcParams['ytick.minor.visible'] = False
plt.rcParams['xtick.direction']     = 'in'
plt.rcParams['ytick.direction']     = 'in'
plt.rcParams['font.family']         = 'arial'
plt.rcParams["mathtext.fontset"]    = 'stixsans'
plt.rcParams['xtick.major.width']   = 0.5
plt.rcParams['ytick.major.width']   = 0.5
plt.rcParams['font.size']           = 16
plt.rcParams['axes.linewidth']      = 1.0

class CircuitBase(Sequence):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._apply_port_table(backend.port_table)
        self._apply_gate_table(backend.gate_table)
            
    def _apply_port_table(self, port_table):
        self.q = {}
        self.r = {}
        self.a = {}
        self.c = {}
        self.i = {}
        self.port_table = port_table
        for idx, port in self.port_table.nodes.items():
            self.q[idx] = self._verify_port(port.q)
            self.r[idx] = self._verify_port(port.r)
            self.a[idx] = self._verify_port(port.a)
        for idx, port in self.port_table.edges.items():
            self.c[idx] = self._verify_port(port)
        for idx, port in self.port_table.impas.items():
            self.i[idx] = self._verify_port(port)
            
    def _apply_gate_table(self, gate_table):
        self.gate_table = gate_table
        
    def qadd(self, instruction, target):
        """Add Instruction to QubitPort.q
        Args:
            instruction (Instruction): Pulse, Command, or Trigger
            target (int or tuple): index of target port, or index of (control, target) for cross port
        """
        if isinstance(target, int):
            port = self.port_table.nodes[target].q
        elif isinstance(target, tuple):
            port = self.port_table.edges[target]

        instruction = self._verify_instruction(instruction)
        port = self._verify_port(port)
        self.instruction_list.append((instruction, port))
        
    def radd(self, instruction, target):
        """Add Instruction to QubitPort.r
        Args:
            instruction (Instruction): Pulse, Command, or Trigger
            target (int or list): index of target port
        """
        instruction = self._verify_instruction(instruction)
        port = self._verify_port(self.port_table.nodes[target].r)
        self.instruction_list.append((instruction, port))

    def aadd(self, instruction, target):
        """Add Instruction to QubitPort.a
        Args:
            instruction (Instruction): Acquire
            target (int or list): index of target port
        """
        if isinstance(instruction, Acquire):
            raise
        instruction = self._verify_instruction(instruction)
        port = self._verify_port(self.port_table.nodes[target].a)
        self.instruction_list.append((instruction, port))

    def qtrigger(self, qubits, align="left"):
        """Add Trigger into the instruction_list
        Args:
            qubit_port_list (list): list of the index of the target qubit ports to be syncronized
            align (str): indicate align mode in the next trigger-edge ("left", "middle", and "right")
        """
        control_port_list = [self.port_table.nodes[qubit].q for qubit in qubits]
        self.trigger(control_port_list, align)

    def rtrigger(self, qubits, align="left"):
        """Add Trigger into the instruction_list
        Args:
            qubits (list): list of the index of the target qubit ports to be syncronized
            align (str): indicate align mode in the next trigger-edge ("left", "middle", and "right")
        """
        muxes = []
        for qubit in qubits:
            muxes += self.port_table.nodes[qubit].mux
        muxes = set(muxes)

        control_port_list = [self.port_table.nodes[qubit].q for qubit in qubits]
        readout_port_list = [self.port_table.nodes[qubit].r for qubit in qubits]
        acquire_port_list = [self.port_table.nodes[qubit].a for qubit in qubits]
        impa_port_list = [self.port_table.impas[mux] for mux in muxes]
        self.trigger(control_port_list + readout_port_list + acquire_port_list + impa_port_list, align)
        
    def gate(self, key, index):
        """Execute a gate
        Args:
            key (str): name of gate
            index (int or list): target
        """
        gate = self.gate_table.get_gate(key, index)
        self.call(gate)
        
    def qwait(self, time, target):
        """Execute a wait gate with given angle
        Args:
            time (float) : wait time [ns]
            target (int): index of the target qubit port
        """
        self.add(Delay(time), self.port_table.nodes[target].q)

    def rz(self, phi, target):
        """Execute a rz gate with given angle
        Args:
            phi (float) : rotation angle [0, 2pi]
            target (int): index of the target qubit port
        """
        self.add(VirtualZ(phi), self.port_table.nodes[target].q)
        for cross in self.port_table.syncs[target]:
            self.add(VirtualZ(phi), cross)

    def rx90(self, target):
        """Execute a rx90 gate
        Args:
            target (int): index of the target qubit port
        """
        self.gate("rx90", target)
        
    def rx180(self, target):
        """Execute a rx180 gate
        Args:
            target (int): index of the target qubit port
        """
        self.gate("rx180", target)

    def rzx45(self, control, target):
        """Execute a rzx45 gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        self.gate("rzx45", (control, target))
        
    def rzx90(self, control, target):
        """Execute a rzx90 gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        self.gate("rzx90", (control, target))

    def measurement(self, target):
        """Execute measurement
        Args:
            target (int): index of the target qubit port
        """
        self.gate("meas", target)

    def pump(self, target):
        """Execute measurement
        Args:
            target (int): index of the target impa port
        """
        self.gate("pump", target)

    def draw(self, time_range=None, cancell_sideband=True, reflect_skew=False):
        """draw waveform saved in the Ports
        Args:
            time_range (tupple): time_range for plot written as (start, end)
            cancell_sideband (bool): bool index to identify whether cancell or not the waveform charping for plot
        """
        
        if reflect_skew is False:
            skew_list = []
            all_ports = list(self.q.values()) + list(self.r.values()) + list(self.a.values()) + list(self.i.values()) + list(self.c.values())
            for port in all_ports:
                skew_list.append(port.skew)
                port.skew = 0
        
        if not self.flag["compiled"]:
            self.compile()

        if self.port_table is None:
            plot_port_list = self.port_list
        else:
            plot_port_list = []
            plot_port_list += [self._verify_port(node.q) for node in self.port_table.nodes.values()]
            plot_port_list += [self._verify_port(node)   for node in self.port_table.edges.values()]
            for (impa, nodes) in self.port_table.muxes.values():
                for node in nodes:
                    rport = self._verify_port(node.r)
                    aport = self._verify_port(node.a)
                    rport.measurement_windows = aport.measurement_windows
                    plot_port_list.append(rport)
                plot_port_list.append(self._verify_port(impa))
        
        if time_range is None:
            plot_time_range = (0, self.max_waveform_lenght)
        else:
            plot_time_range = time_range

        plt.figure(figsize=(20,1.5*len(plot_port_list)))
        for i, port in enumerate(plot_port_list):
            plt.subplot(len(plot_port_list), 1, i+1)
            plt.axhline(0, color="black", linestyle="-")
            for measurement_window in port.measurement_windows:
                plt.axvspan(measurement_window[0], measurement_window[1], color="green", alpha=0.3)
            if cancell_sideband:
                plot_waveform = np.exp(1j*(2*np.pi*port.SIDEBAND_FREQ*port.time))*port.waveform
            else:
                plot_waveform = port.waveform
            plt.step(port.time, plot_waveform.real)
            plt.step(port.time, plot_waveform.imag)
            plt.fill_between(port.time, plot_waveform.real, step="pre", alpha=0.4)
            plt.fill_between(port.time, plot_waveform.imag, step="pre", alpha=0.4)
            for trigger_index, _ in port.trigger_node_list:
                position = self.trigger_position_list[trigger_index]
                plt.axvline(position, color="red", linestyle="--")
                if plot_time_range[0] <= position <= plot_time_range[1]:
                    plt.text(x=position, y=-1, s=trigger_index, color="red", fontsize=12)
            plt.text(x=plot_time_range[0], y=-0, s=port.name,fontsize=18)
            plt.ylim(-1,1)
            plt.xlim(plot_time_range[0], plot_time_range[1])
            plt.grid()
            plt.ylabel("Amplitude")
            plt.tick_params(labelbottom=False)
        plt.tight_layout()
        plt.tick_params(labelbottom=True)
        plt.xlabel("Time (ns)")
        plt.show()
        
        if reflect_skew is False:
            for port, skew in zip(all_ports, skew_list):
                port.skew = skew
        
    def get_waveform_information(self):
        """get waveform information for I/O with measurement_tools
        """
        
        if not self.flag["compiled"]:
            self.compile()
        
        waveform_information = {}
        for idx, port in self.port_table.nodes.items():
            
            qport = self._verify_port(port.q)
            rport = self._verify_port(port.r)
            aport = self._verify_port(port.a)
            
            qdir = {
                "daq_length" : qport.waveform.size*qport.DAC_STEP,
                "measurement_windows" : qport.measurement_windows,
                "waveform" : qport.waveform.real,
                "waveform_updated" : False,
            }
            rdir = {
                "daq_length" : rport.waveform.size*rport.DAC_STEP,
                "measurement_windows" : aport.measurement_windows,
                "waveform" : rport.waveform.real,
                "waveform_updated" : False,
            }
            
            waveform_information[f"Q{idx}"] = {
                "qubit"   : qdir,
                "readout" : rdir,
            }
            
        for edge, port in self.port_table.edges.items():
            cport = self._verify_port(port)

            cdir = {
                "daq_length" : cport.waveform.size*cport.DAC_STEP,
                "measurement_windows" : cport.measurement_windows,
                "waveform" : cport.waveform.real,
                "waveform_updated" : False,
            }

            waveform_information[f"Q{edge[1]}"]["cr"] = cdir
            
        for idx, port in self.port_table.impas.items():
            iport = self._verify_port(port)
            
            idir = {
                "daq_length" : iport.waveform.size*iport.DAC_STEP,
                "measurement_windows" : iport.measurement_windows,
                "waveform" : iport.waveform.real,
                "waveform_updated" : False,
            }
            
            waveform_information[f"I{idx}"] = {
                "jpa"    : idir,
            }
            
        self.reset_compile()
            
        return waveform_information

class Circuit(CircuitBase):
    def __init__(self, backend):
        super().__init__(backend)

    def irx90(self, target):
        """Execute a inversed rx90 gate
        Args:
            target (int): index of the target qubit port
        """
        self.rz(np.pi, target)
        self.rx90(target)
        self.rz(-np.pi, target)

    def ry90(self, target):
        """Execute a ry90 gate
        Args:
            target (int): index of the target qubit port
        """
        self.rz(-0.5*np.pi, target)
        self.rx90(target)
        self.rz(+0.5*np.pi, target)
        
    def iry90(self, target):
        """Execute a inversed ry90 gate
        Args:
            target (int): index of the target qubit port
        """
        self.rz(+0.5*np.pi, target)
        self.rx90(target)
        self.rz(-0.5*np.pi, target)
        
    def I(self, target):
        """Execute a I gate
        Args:
            target (int): index of the target qubit port
        """
        pass
    
    def X(self, target):
        """Execute a X gate
        Args:
            target (int): index of the target qubit port
        """
        self.rx90(target)
        self.rx90(target)

    def Y(self, target):
        """Execute a Y gate
        Args:
            target (int): index of the target qubit port
        """
        self.rz(-0.5*np.pi, target)
        self.X(target)
        self.rz(+0.5*np.pi, target)
        
    def Z(self, target):
        """Execute a Z gate
        Args:
            target (int): index of the target qubit port
        """
        self.rz(np.pi, target)
        
    def iX(self, target):
        """Execute a Inversed X gate
        Args:
            target (int): index of the target qubit port
        """
        self.Z(target)
        self.X(target)
        self.Z(target)
        
    def iY(self, target):
        """Execute a Inversed Y gate
        Args:
            target (int): index of the target qubit port
        """
        self.Z(target)
        self.Y(target)
        self.Z(target)
        
    def Pauli(self, label, target):
        """Execute a Pauli gate
        Args:
            label (str) : I or X or Y or Z
            target (int): index of the target qubit port
        """
        
        if label == "I":
            self.I(target)
        elif label == "X":
            self.X(target)
        elif label == "Y":
            self.Y(target)
        elif label == "Z":
            self.Z(target)
        else:
            raise
    
    def irzx45(self, control, target):
        """Execute a inversed irzx45 gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        self.Z(target)
        self.rzx45(control, target)
        self.Z(target)

    def rzx90(self, control, target):
        """Execute a inversed rzx90 gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        self.rzx45(control, target)
        self.X(control)
        self.irzx45(control, target)
        self.iX(control)

    def cnot(self, control, target):
        """Execute a inversed cnot gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        self.rz(-0.5*np.pi, control)
        self.rzx90(control, target)
        self.irx90(target)
        
    def icnot(self, control, target):
        """Execute a inversed cnot gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        H = 0.5**(0.5)*np.array([[1,1],[1,-1]])
        irx90 = 0.5**(0.5)*np.array([[1,1j],[1j,1]])
        
        self.rz(-0.5*np.pi, target)
        self.su2(H, control)
        self.su2(H, target)
        self.rzx90(control, target)
        self.su2(irx90@H, control)
        self.su2(H, target)

    def prep_init(self, pauli, index, target):
        """Prepare the eigenstate of Pauli operator on the indicated qubit
        Args:
            pauli (str): indicate the Pauli operator with "I" or "X" or "Y" or "Z"
            index (str): indicate the eigenstate with "0" or "1"
            target (int): index of the target qubit port
        """
        if pauli in ["I","Z"]:
            if index == "0":
                pass
            else:
                self.rx90(target)
                self.rx90(target)
        elif pauli == "X":
            if index == "0":
                self.ry90(target)
            else:
                self.iry90(target)
        elif pauli == "Y":
            if index == "0":
                self.irx90(target)
            else:
                self.rx90(target)

    def meas_axis(self, pauli, target):
        """Change the measurement axis on the indicated qubit
        Args:
            pauli (str): indicate the Pauli operator with "I" or "X" or "Y" or "Z"
            target (int): index of the target qubit port
        """
        if pauli in ["I","Z"]:
            pass
        elif pauli == "X":
            self.iry90(target)
        elif pauli == "Y":
            self.rx90(target)

    def su2(self, matrix, target):
        """Execute the arbitrary single-qubit gate with virtual-Z decomposition (u3)
        Args:
            matrix (np.ndarray): matrix expression of the single-qubit gate
            target (int): index of the target qubit port
        """
        phases = matrix_to_su2(matrix)
        self.rz(phases[2], target)
        self.rx90(target)
        self.rz(phases[1], target)
        self.rx90(target)
        self.rz(phases[0], target)

    def su4(self, matrix, control, target):
        """Execute the arbitrary two-qubit gate with Cartan's KAK decomposition
        Args:
            matrix (np.ndarray): matrix expression of the two-qubit gate
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        gates = matrix_to_su4(matrix)
        self.su2(gates[0][0], control)
        self.su2(gates[0][1], target)
        self.cnot(control, target)
        self.su2(gates[1][0], control)
        self.su2(gates[1][1], target)
        self.cnot(control, target)
        self.su2(gates[2][0], control)
        self.su2(gates[2][1], target)
        self.cnot(control, target)
        self.su2(gates[3][0], control)
        self.su2(gates[3][1], target)

    def measurements(self, target):
        """Execute measurements for many qubits
        Args:
            target (list): list of the index of the target qubit port
        """
        muxes = []
        for i in target:
            muxes += self.port_table.nodes[i].mux
        muxes = set(muxes)

        self.rtrigger(target)
        for i in target:
            self.measurement(i)
        for i in muxes:
            self.pump(i)
        self.rtrigger(target)

    def measurement_all(self):
        """Execute measurements for all qubits
        """
        target = self.port_table.nodes.keys()
        self.measurements(target)
        
class MitigatedCircuit(Circuit):
    def __init__(self, backend, repeat):
        super().__init__(backend)
        self.repeat = repeat
        
    def rx90(self, target):
        """Execute a rx90 gate
        Args:
            target (int): index of the target qubit port
        """
        for _ in range(self.repeat):
            super().rx90(target)
            self.rz(np.pi, target)
            super().rx90(target)
            self.rz(np.pi, target)
        super().rx90(target)

    def rzx45(self, control, target):
        """Execute a rzx45 gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        for _ in range(self.repeat):
            super().rzx45(control, target)
            self.rz(np.pi, target)
            super().rzx45(control, target)
            self.rz(np.pi, target)
        super().rzx45(control, target)
        
class MitigatedCircuit2(Circuit):
    def __init__(self, backend, index):
        super().__init__(backend)
        self.index = index
        
    def rx90(self, target):
        """Execute a rx90 gate
        Args:
            target (int): index of the target qubit port
        """
        rx90 = self.gate_table.get_gate("rx90", target)
        if rx90.flag["compiled"] is False:
            rx90.compile()
        duration = rx90.max_waveform_lenght
        
        self.qwait(0.5*self.index*duration, target)
        super().rx90(target)
        self.qwait(0.5*self.index*duration, target)

    def rzx45(self, control, target):
        """Execute a rzx45 gate
        Args:
            control (int): index of the control qubit port
            target (int): index of the target qubit port
        """
        rzx45 = self.gate_table.get_gate("rzx45", (control, target))
        if rzx45.flag["compiled"] is False:
            rzx45.compile()
        duration = rzx45.max_waveform_lenght
        
        self.qtrigger([control, target])
        self.qwait(0.5*self.index*duration, control)
        self.qwait(0.5*self.index*duration, target)
        super().rzx45(control, target)
        self.qwait(0.5*self.index*duration, control)
        self.qwait(0.5*self.index*duration, target)
        self.qtrigger([control, target])