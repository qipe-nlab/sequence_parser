import numpy as np
from scipy.linalg import expm
from cirq.linalg import kak_decomposition
from qupy.operator import H, S, X, Z

def matrix_to_su2(matrix):
    """Decompose the arbitrary single-qubit gate with the rx90 and rz gates
    Args:
        u (np.ndarray): matrix expression of the single-qubit gate
    Returns:
        list: rotation angles of the rz gates
    """
    u = np.array(matrix,dtype=np.complex128)
    u = u/np.sqrt(np.linalg.det(u))
    angle1 = np.angle(u[1,1])
    angle2 = np.angle(u[1,0])
    t2 = angle1+angle2
    t3 = angle1-angle2
    cv = u[1,1]/np.exp(1.j*angle1)
    sv = u[1,0]/np.exp(1.j*angle2)
    cv_safety = max(min(cv,1.),-1.)
    t1 = np.arccos(np.real(cv_safety))*2
    if(sv<0):
        t1 = -t1
    return t2 + 3*np.pi , t1+np.pi, t3

def matrix_to_su4(matrix):
    """Decompose the arbitrary two-qubit gate with the rzx45 and rx90 and rz gates
    Args:
        u (np.ndarray): matrix expression of the two-qubit gate
    Returns:
        list: matrix expression of the single-qubit gates interleaved rzx45 in the KAK decomposition
    """
    u = np.array(matrix,dtype=np.complex128)
    u = u/np.sqrt(np.linalg.det(u))
    kak_decomp = kak_decomposition(u)
    bef = kak_decomp.single_qubit_operations_before
    aft = kak_decomp.single_qubit_operations_after
    param = kak_decomp.interaction_coefficients
    # global_phase = kak_decomp.global_phase
    l1 = [bef[0], bef[1]]
    l2 = [H@expm(1.j*param[0]*X), expm(1.j*param[2]*Z)]
    l3 = [H@S, expm(-1.j * param[1]*Z)]
    l4 = [aft[0]@expm(1.j*np.pi/4*X), aft[1]@expm(-1.j*np.pi/4*X)]
    return l1,l2,l3,l4