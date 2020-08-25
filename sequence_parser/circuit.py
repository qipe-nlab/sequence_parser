import numpy as np
from .sequence import Sequence
from .instruction.instruction_parser import compose
from .instruction.command import VirtualZ
from .util.decompose import matrix_to_su2, matrix_to_su4

class ControlDict:
    def __init__(self):
        self.gate_table = {}
        self.port_table = {}

    def _add(self, gate_name, key, setting):
        gate = Sequence()
        gate.load_setting(setting)
        self.gate_table[(gate_name, key)] = gate

    def _add_sync(self, master, slaves):
        self.port_table[master] = slaves

    def get(self, gate_name, key):
        gate = self.gate_table[(gate_name, key)]
        return gate

    def get_sync(self, port):
        slaves = self.port_table[port]
        return slaves

    def find_sync(self, port):
        slaves = []
        for cross_port, (_, target_port) in self.port_table.items():
            if target_port.name is port.name:
                slaves.append(cross_port)
        return slaves

class CircuitBase(Sequence):
    def __init__(self):
        super().__init__()

    def _apply(self, control_dict):
        self.control_dict = control_dict

    def rz(self, phi, port):
        """Execute a rz gate with given angle
        Args:
            phi (float) : rotation angle [0, 2pi]
            port (Port): target port object
        """
        self.add(VirtualZ(phi), port)
        for slave in self.control_dict.find_sync(port):
            self.add(VirtualZ(phi), slave)

    def rx90(self, port):
        """Execute a rx90 gate
        Args:
            port (Port): target port object
        """
        rx90 = self.control_dict.get("rx90", port.name)
        self.call(rx90)

    def rzx45(self, port):
        """Execute a rzx45 gate
        Args:
            port (Port): target port object
        """
        rzx45 = self.control_dict.get("rzx45", port.name)
        self.call(rzx45)

    def measurement(self, port):
        """Execute measurement
        Args:
            port (Port): target port object
        """
        meas = self.control_dict.get("meas", port.name)
        self.call(meas)

class Circuit(CircuitBase):
    def __init__(self):
        super().__init__()

    def ry90(self, port):
        """Execute a ry90 gate
        Args:
            port (Port): target port object
        """
        self.rz(-0.5*np.pi, port)
        self.rx90(port)
        self.rz(+0.5*np.pi, port)

    def irx90(self, port):
        """Execute a inversed rx90 gate
        Args:
            port (Port): target port object
        """
        self.rz(np.pi, port)
        self.rx90(port)
        self.rz(np.pi, port)

    def iry90(self, port):
        """Execute a inversed ry90 gate
        Args:
            port (Port): target port object
        """
        self.rz(+0.5*np.pi, port)
        self.rx90(port)
        self.rz(-0.5*np.pi, port)

    def irzx45(self, port):
        """Execute a inversed rzx45 gate
        Args:
            port (Port): cross port object
        """
        control, target = self.control_dict.get_sync(port)
        self.rz(np.pi, target)
        self.rzx45(port)
        self.rz(np.pi, target)

    def rzx90(self, port):
        """Execute a rzx90 gate with TPCX gate seauence
        Args:
            port (Port): cross port object
        """
        control, target = self.control_dict.get_sync(port)
        self.trigger([control, target, port])
        self.rzx45(port)
        self.trigger([control, target, port])
        self.rx90(control)
        self.rx90(control)
        self.trigger([control, target, port])
        self.irzx45(port)
        self.trigger([control, target, port])
        self.rx90(control)
        self.rx90(control)

    def cnot(self, port):
        """Execute a cnot gate
        Args:
            port (Port): cross port object
        """
        control, target = self.control_dict.get_sync(port)
        self.rz(-0.5*np.pi, control)
        self.rzx90(port)
        self.irx90(target)

    def prep_init(self, pauli, index, port):
        """Prepare the eigenstate of Pauli operator on the indicated qubit
        Args:
            pauli (str): indicate the Pauli operator with "I" or "X" or "Y" or "Z"
            index (str): indicate the eigenstate with "0" or "1"
            port (Port): target port object
        """
        if pauli in ["I","Z"]:
            if index == "0":
                pass
            else:
                self.rx90(port)
                self.rx90(port)
        elif pauli == "X":
            if index == "0":
                self.ry90(port)
            else:
                self.iry90(port)
        elif pauli == "Y":
            if index == "0":
                self.irx90(port)
            else:
                self.rx90(port)

    def meas_axis(self, pauli, port):
        """Change the measurement axis on the indicated qubit
        Args:
            pauli (str): indicate the Pauli operator with "I" or "X" or "Y" or "Z"
            port (Port): target port object
        """
        if pauli in ["I","Z"]:
            pass
        elif pauli == "X":
            self.iry90(port)
        elif pauli == "Y":
            self.rx90(port)

    def su2(self, matrix, port):
        """Execute the arbitrary single-qubit gate with virtual-Z decomposition (u3)
        Args:
            matrix (np.ndarray): matrix expression of the single-qubit gate
            port (Port): target port object
        """
        phases = matrix_to_su2(matrix)
        self.rz(phases[2], port)
        self.rx90(port)
        self.rz(phases[1], port)
        self.rx90(port)
        self.rz(phases[0], port)

    def su4(self, matrix, port):
        """Execute the arbitrary two-qubit gate with Cartan's KAK decomposition
        Args:
            matrix (np.ndarray): matrix expression of the single-qubit gate
            port (Port): cross port object
        """
        control, target = self.control_dict.get_sync(port)
        gates = matrix_to_su4(matrix)
        self.su2(gates[0][0], control)
        self.su2(gates[0][1], target)
        self.cnot(port)
        self.su2(gates[1][0], control)
        self.su2(gates[1][1], target)
        self.cnot(port)
        self.su2(gates[2][0], control)
        self.su2(gates[2][1], target)
        self.cnot(port)
        self.su2(gates[3][0], control)
        self.su2(gates[3][1], target)