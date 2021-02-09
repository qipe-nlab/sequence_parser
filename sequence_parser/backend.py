from .port import Port
from .sequence import Sequence

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
        self.muxes = {}
        self.syncs = {}
        self.impas = {}
        
    def _add_nodes(self, nodes):
        for node in nodes:
            self.nodes[node] = QubitPort(node)
        
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
            
    def _add_muxes(self, muxes):
        for mux in muxes:
            impa_port = Port(name=f"i{mux[0]}")
            self.impas[mux[0]] = impa_port
            
            qubit_port_list = []
            for node in mux[1]:
                qubit_port = QubitPort(node)
                qubit_port._add_mux(mux[0])
                self.nodes[node] = qubit_port
                qubit_port_list.append(qubit_port)
            self.muxes[mux[0]] = (impa_port, qubit_port_list)
            
    def dump_setting(self):
        setting = {
            "nodes" : self.nodes.keys(),
            "edges" : self.edges.keys(),
        }
        return setting
        
    def load_setting(self, setting):
        self._add_nodes(setting["nodes"])
        self._add_edges(setting["edges"])

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

class Backend:
    def __init__(self):
        self.instrument = None
        self.calib_note = None
        self.port_table = None
        self.gate_table = None
    
    def add_calib_note(self, calib_note):
        self.calib_note = calib_note
        
    def add_instrument(self, instrument):
        self.instrument = instrument
    
    def add_port_table(self, port_table):
        self.port_table = port_table
    
    def add_gate_table(self, gate_table):
        self.gate_table = gate_table
    
#     def dump_setting(self):
#         setting = {
#             "calib_note" : self.calib_note.dump_setting(),
#             "instrument" : self.instrument.dump_setting(),
#             "port_table" : self.port_table.dump_setting(),
#             "gate_table" : self.gate_table.dump_setting(),
#         }
#         return setting
        
#     def load_setting(self, setting):
#         import measurement_tool as mt
        
#         self.calib_note = Calibration_note()
#         calib_note.load_setting(setting["calib_note"])
        
#         self.instrument = 
        
#         self.port_table = PortTable()
#         port_table.load_setting(setting["port_table"])
        
#         self.gate_table = GateTable()
#         gate_table.load_setting(setting["gate_table"])