import numpy as np
from ..sequence import Sequence
from ..port import Port
from ..backend import PortTable, GateTable, Backend
from ..instruction import *

def default_backend(muxes, edges, qubit_notes, impa_notes, cross_notes, visualize=True):
    
    pt = PortTable()
    pt._add_muxes(muxes)
    pt._add_edges(edges)

    gt = GateTable()
    for node in pt.nodes.values():
        qubit_name = f"Q{node.node}"
        qubit_note = qubit_notes[qubit_name]
        arx90 = qubit_note.half_pi_pulse_power
        brx90 = qubit_note.half_pi_pulse_length_precise["ns"]
        grx90 = qubit_note.half_pi_pulse_drag_coeff

#         rx90 = Sequence()
#         rx90.add(Delay(duration=-brx90), node.q)
#         with rx90.align(node.q, mode="left"):
#             rx90.add(Gaussian(amplitude=arx90, fwhm=brx90, duration=4*brx90), node.q)
#             rx90.add(Deriviative(Gaussian(amplitude=1j*arx90*grx90, fwhm=brx90, duration=4*brx90)), node.q)
#         rx90.add(Delay(duration=-brx90), node.q)

        rx90 = Sequence()
        with rx90.align(node.q, mode="left"):
            rx90.add(Gaussian(amplitude=arx90, fwhm=brx90, duration=2*brx90, zero_end=True), node.q)
            rx90.add(Deriviative(Gaussian(amplitude=1j*arx90*grx90, fwhm=brx90, duration=2*brx90, zero_end=True)), node.q)
        gt._add_gate("rx90", node.node, rx90)
        
        rx180 = Sequence()
        rx180.add(Delay(duration=-brx90), node.q)
        with rx180.align(node.q, mode="left"):
            rx180.add(Gaussian(amplitude=2*arx90, fwhm=brx90, duration=4*brx90), node.q)
            rx180.add(Deriviative(Gaussian(amplitude=2j*arx90*grx90, fwhm=brx90, duration=4*brx90)), node.q)
        rx180.add(Delay(duration=-brx90), node.q)
        gt._add_gate("rx180", node.node, rx180)
        
        if visualize:
            print(f"rx90 : {node.node}")
            rx90.draw()

    for idx, (impa, nodes) in pt.muxes.items():
        impa_name = f"I{idx}"
        impa_note = impa_notes[impa_name]
        pump_amp = impa_note.pump_amplitude
        pump_freq = impa_note.pump_frequency["GHz"]
        
        imeas_dur_list = []
        imeas_list = []
        for node in nodes:
            qubit_name = f"Q{node.node}"
            qubit_note = qubit_notes[qubit_name]
            dmeas = qubit_note.cavity_readout_trigger_delay["ns"]
            top_dur = qubit_note.single_length["ns"]
            ac_dur = np.where(np.sum(qubit_note.single_window, axis=0) != 0)[0][-1]*8
            imeas = Sequence()
            imeas.add(Delay(duration=-10), node.r)
            with imeas.align(node.r, mode="left"):
                imeas.add(FlatTop(Gaussian(amplitude=1.0, fwhm=10, duration=40), top_duration=top_dur-10), node.r)
                with imeas.align(node.r, mode="sequential"):
                    imeas.add(Delay(dmeas), node.r)
                    imeas.add(Acquire(duration=ac_dur), node.r)
            imeas.add(Delay(duration=-10), node.r)
            gt._add_gate("imeas", node.node, imeas)
            imeas_list.append(imeas)
            imeas_dur_list.append(dmeas + ac_dur - 10)

        pump = Sequence()
        pump.add(Delay(duration=-10), impa)
        pump.add(SetDetuning(pump_freq), impa)
        pump.add(FlatTop(Gaussian(amplitude=pump_amp, fwhm=10, duration=40), top_duration=55000), impa)
        pump.add(Delay(duration=-10), impa)
        gt._add_gate("pump", idx, pump)

        meas = Sequence()
        meas.trigger([impa]+[node.r for node in nodes]+[node.q for node in nodes])
        for imeas in imeas_list:
            meas.call(imeas)
        meas.call(pump)
        meas.trigger([impa]+[node.r for node in nodes]+[node.q for node in nodes])
        gt._add_gate("meas", idx, meas)
        
        if visualize:
            print(f"meas : {idx}")
            meas.draw()

    for key, edge in pt.edges.items():
        cross_name = f"C({key[0]},{key[1]})"
        if cross_name in cross_notes.keys():
            cross_note = cross_notes[cross_name]
            
            skew = cross_note.skew
            edge.skew = skew
            
            cra = cross_note.rzx45_cra
            cta = cross_note.rzx45_cta
            crt = cross_note.rzx45_crt
            cre = cross_note.rzx45_cre
            crz = cross_note.rzx45_crz

            qc = pt.nodes[key[0]]
            qt = pt.nodes[key[1]]

            rzx45 = Sequence()
            rzx45.trigger([qc.q,qt.q,qc.r,qt.r,qc>>qt])
            rzx45.add(FlatTop(RaisedCos(amplitude=+cra, duration=cre), top_duration=crt), qc>>qt)
            rzx45.add(FlatTop(RaisedCos(amplitude=+cta, duration=cre), top_duration=crt), qt.q)
            rzx45.trigger([qc.q,qt.q,qc.r,qt.r,qc>>qt])
            rzx45.add(VirtualZ(crz), qc.q)
            gt._add_gate("rzx45", key, rzx45)

            if visualize:
                print(f"rzx45 : {idx}")
                rzx45.draw()
                
            cra = cross_note.rzx90_cra
            cta = cross_note.rzx90_cta
            crt = cross_note.rzx90_crt
            cre = cross_note.rzx90_cre
            crz = cross_note.rzx90_crz
            rta = cross_note.rzx90_rta
            
            rzx90 = Sequence()
            rzx90.trigger([qc.q,qt.q,qc.r,qt.r,qc>>qt])
            rzx90.add(FlatTop(RaisedCos(amplitude=+cra, duration=cre), top_duration=crt), qc>>qt)
            with rzx90.align(qt.q, mode="left"):
                rzx90.add(FlatTop(RaisedCos(amplitude=+cta, duration=cre), top_duration=crt), qt.q)
                with rzx90.align(qt.q, mode="sequential"):
                    rzx90.add(RaisedCos(amplitude=+rta, duration=0.5*(crt+cre)), qt.q)
                    rzx90.add(RaisedCos(amplitude=-rta, duration=0.5*(crt+cre)), qt.q)
            rzx90.trigger([qc.q,qt.q,qc.r,qt.r,qc>>qt])
            rzx90.add(VirtualZ(crz), qc.q)
            gt._add_gate("rzx90", key, rzx90)

            if visualize:
                print(f"rzx90 : {idx}")
                rzx90.draw()
        
    backend = Backend()
    backend.add_port_table(pt)
    backend.add_gate_table(gt)
    
    return backend