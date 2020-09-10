import numpy as np
import matplotlib.pyplot as plt
from .sequence import Sequence
from .port import Port
from .instruction.instruction_parser import compose
from .instruction.command import VirtualZ
from .util.decompose import matrix_to_su2, matrix_to_su4

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

class QubitPort:
    def __init__(self, node):
        self.node = node
        self.control = Port(f"q{node}.q")
        self.readout = Port(f"q{node}.r")
        
        # alias
        self.q = self.control
        self.r = self.readout
        
        self.lshift = {}
        self.rshift = {}
        self.mux = []
    
    def _add_lshift(self, other, port):
        self.lshift[other] = port
        
    def _add_rshift(self, other, port):
        self.rshift[other] = port
        
    def _add_mux(self, other):
        self.mux.append(other)
        
    def __repr__(self):
        return f"q{self.node}"
        
    def __lshift__(self, other):
        return self.lshift[other]

    def __rshift__(self, other):
        return self.rshift[other]

class PortTable:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.syncs = {}
        
    def _add_nodes(self, nodes):
        for node in nodes:
            exec(f"global q{node} ; q{node} = QubitPort({node}) ;self.nodes[{node}] = q{node}")
        
    def _add_edges(self, edges):
        for edge in edges:
            edge_port = Port(name=f"c{edge[0]}_{edge[1]}")
            self.edges[edge] = edge_port
            self.nodes[edge[0]]._add_rshift(self.nodes[edge[1]], edge_port)
            self.nodes[edge[1]]._add_lshift(self.nodes[edge[0]], edge_port)
            
        for node in self.nodes.keys():
            tmp_sync = []
            for (control, target), edge_port in self.edges.items():
                if node == target:
                    tmp_sync.append(edge_port)
            self.syncs[node] = tmp_sync

class GateTable:
    def __init__(self):
        self.gate_table = {}
        
    def __repr__(self):
        print_str = ""
        for (gate_name, key), gate in self.gate_table.items():
            print_str += f"* [Gate Name : {gate_name}, Key : {key}] \n"
            print_str += f"{gate}"
            print_str += "\n\n"
        return print_str

    def _add_gate(self, gate_name, key, gate):
        self.gate_table[(gate_name, key)] = gate
        
    def get_gate(self, gate_name, key):
        gate = self.gate_table[(gate_name, key)]
        return gate
    
    def dump_setting(self):
        setting = {}
        for (gate_name, key), gate in self.gate_table.items():
            setting[(gate_name, key)] = gate.dump_setting()
        return setting
        
    def load_setting(self, setting):
        self.gate_table = {}
        for (gate_name, key), tmp_setting in setting.items():
            gate = Sequence()
            gate.load_setting(tmp_setting)
            self.gate_table[(gate_name, key)] = gate

class CircuitBase(Sequence):
    def __init__(self):
        super().__init__()
        self.port_table = None
        self.gate_table = None

    def _apply_port_table(self, port_table):
        self.port_table = port_table
        
    def _apply_gate_table(self, gate_table):
        self.gate_table = gate_table
        
    def qtrigger(self, qubits, align="left"):
        """Add Trigger into the instruction_list
        Args:
            qubit_port_list (list): list of the target qubit ports to be syncronized
            align (str): indicate align mode in the next trigger-edge ("left", "middle", and "right")
        """
        self.trigger([qubit.r for qubit in qubits] + [qubit.q for qubit in qubits], align)

    def rz(self, phi, target):
        """Execute a rz gate with given angle
        Args:
            phi (float) : rotation angle [0, 2pi]
            target (QubitPort): target qubit port
        """
        self.add(VirtualZ(phi), target.q)
        for cross in self.port_table.syncs[target.node]:
            self.add(VirtualZ(phi), cross)

    def rx90(self, target):
        """Execute a rx90 gate
        Args:
            target (QubitPort): target qubit port
        """
        rx90 = self.gate_table.get_gate("rx90", target.node)
        self.call(rx90)

    def rzx45(self, control, target):
        """Execute a rzx45 gate
        Args:
            control (QubitPort): control qubit port
            target (QubitPort): target qubit port
        """
        rzx45 = self.gate_table.get_gate("rzx45", (control.node, target.node))
        self.call(rzx45)

    def measurement(self, target):
        """Execute measurement
        Args:
            target (QubitPort): target qubit port
        """
        meas = self.gate_table.get_gate("meas", target.node)
        self.call(meas)

    def draw(self, time_range=None, cancell_sideband=True):
        """draw waveform saved in the Ports
        Args:
            time_range (tupple): time_range for plot written as (start, end)
            cancell_sideband (bool): bool index to identify whether cancell or not the waveform charping for plot
        """
        if not self.flag["compiled"]:
            self.compile()

        if self.port_table is None:
            plot_port_list = self.port_list
        else:
            plot_port_list = []
            plot_port_list += [self._verify_port(node.r) for node in self.port_table.nodes.values()]
            plot_port_list += [self._verify_port(node.q) for node in self.port_table.nodes.values()]
            plot_port_list += [self._verify_port(node)   for node in self.port_table.edges.values()]
        
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

class Circuit(CircuitBase):
    def __init__(self):
        super().__init__()

    def irx90(self, target):
        """Execute a inversed rx90 gate
        Args:
            target (QubitPort): target qubit port object
        """
        self.rz(np.pi, target)
        self.rx90(target)
        self.rz(np.pi, target)

    def ry90(self, target):
        """Execute a ry90 gate
        Args:
            target (QubitPort): target qubit port object
        """
        self.rz(-0.5*np.pi, target)
        self.rx90(target)
        self.rz(+0.5*np.pi, target)
        
    def iry90(self, target):
        """Execute a inversed ry90 gate
        Args:
            target (QubitPort): target qubit port object
        """
        self.rz(+0.5*np.pi, target)
        self.rx90(target)
        self.rz(-0.5*np.pi, target)
        
    def irzx45(self, control, target):
        """Execute a inversed irzx45 gate
        Args:
            control (QubitPort): control qubit port object
            target (QubitPort): target qubit port object
        """
        self.rz(np.pi, target)
        self.rzx45(control, target)
        self.rz(np.pi, target)

    def rzx90(self, control, target):
        """Execute a inversed rzx90 gate
        Args:
            control (QubitPort): control qubit port object
            target (QubitPort): target qubit port object
        """
        self.trigger([control.q, target.q, control>>target])
        self.rzx45(control, target)
        self.trigger([control.q, target.q, control>>target])
        self.rx90(control)
        self.rx90(control)
        self.trigger([control.q, target.q, control>>target])
        self.irzx45(control, target)
        self.trigger([control.q, target.q, control>>target])
        self.rx90(control)
        self.rx90(control)

    def cnot(self, control, target):
        """Execute a inversed cnot gate
        Args:
            control (QubitPort): control qubit port object
            target (QubitPort): target qubit port object
        """
        self.rz(-0.5*np.pi, control)
        self.rzx90(control, target)
        self.irx90(target)

    def prep_init(self, pauli, index, target):
        """Prepare the eigenstate of Pauli operator on the indicated qubit
        Args:
            pauli (str): indicate the Pauli operator with "I" or "X" or "Y" or "Z"
            index (str): indicate the eigenstate with "0" or "1"
            target (QubitPort): target qubit port object
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
            target (QubitPort): target qubit port object
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
            target (QubitPort): target qubit port object
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
            matrix (np.ndarray): matrix expression of the single-qubit gate
            control (QubitPort): control qubit port object
            target (QubitPort): target qubit port object
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