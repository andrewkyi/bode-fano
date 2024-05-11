from circuit_reader import *

# definition of constants
phi0 = cnst.h/(2*cnst.e)

class CalculatedValues:
    def __init__(self, label, values, measurable_type):
        self.label = label  # label for values e.g., leff
        self.values = values  # a list of values
        self.measurable_type = measurable_type  # specify type of measurement for plotter
        self.axis_label = None  # probably same as measurable type, but customizable?
    
    # if label is from circuit_data, automatically find label

# probably do a use_calc_val data format transformation

# general circuit/jj functions
def calc_lc_rfreq(l, c):
    # frequency, not omega!
    return 1/(2*np.pi*np.sqrt(l*c))

def calc_lc_q(r, l, c, mode="series"):
    if mode=="series" or mode=="s":
        qfactor = 1/r*np.sqrt(l/c)
    elif mode=="parallel" or mode=="p":
        qfactor = r*np.sqrt(c/l)
    else:
        qfactor = 0
    return qfactor

def calc_k(l1, l2, m):
    return m/np.sqrt(l1*l2)

def calc_lj(ic, phi):
    return phi0/(2*np.pi*ic)/np.cos(phi)

def calc_lj_ibias(ic, ibias):  # incomplete
    ibias = ibias % (2*ic)
    phi = np.arcsin(ibias/ic)
    return phi0/(2*np.pi*ic)/np.cos(phi)

def calc_fj(ic):
    return ic/(4*np.pi*e)

# rifkin circuit specific functions
def calc_leff(lt, omega, r, l, cur_l, k=1, ls=0, stabilize_tank=True):
    m2 = k**2*lt*l
    if r == 0 and stabilize_tank:
        leff = lt - m2/(l + cur_l + ls)
    elif not stabilize_tank:
        leff = lt + ls - m2/(l + cur_l)
    else:
        z_0r = omega**2*cur_l**2*r/(r**2 + omega**2*cur_l**2)
        z_0i = omega*cur_l*r**2/(r**2 + omega**2*cur_l**2) + omega*ls
        leff = lt - omega*m2*(z_0i+omega*l)/(z_0r**2 + (z_0i+omega*l)**2)
    # leff = lt - (r**2*m2*(l+cur_l) + omega**2*m2*cur_l**2*l)/(r**2*(cur_l+l)**2+omega**2*cur_l**2*l**2)
    return leff

def calc_reff(rt, lt, omega, r, l, cur_l, k=1, ls=0):
    m2 = k**2*lt*l
    if r == 0:
        try: reff = rt * np.ones(len(cur_l))
        except TypeError: reff = rt
    else:
        z_0r = omega**2*cur_l**2*r/(r**2 + omega**2*cur_l**2)
        z_0i = omega*cur_l*r**2/(r**2 + omega**2*cur_l**2) + ls
        reff = rt + omega**2*m2*z_0r/(z_0r**2 + (z_0i+omega*l)**2)
    # reff = rt + (r*omega**2*m2*cur_l**2)/(r**2*(cur_l+l)**2+omega**2*cur_l**2*l**2)
    return reff
    
def calc_coupled_z(rt, lt, omega, r, l, cur_l, k=1, ls=0, stabilize_tank=True):
    m2 = k**2*lt*l
    m = np.sqrt(m2)
    z_0r = omega**2*cur_l**2*r/(r**2 + omega**2*cur_l**2)
    if stabilize_tank: z_0i = omega*cur_l*r**2/(r**2 + omega**2*cur_l**2)
    else: z_0i = omega*cur_l*r**2/(r**2 + omega**2*cur_l**2) + ls
    # z_0 = z_0r + 1j*z_0i  # complex(z_0r, z_0i)
    z_coupled = 1 / (1/(1j*omega*m) + 1/(z_0r + 1j*(omega*(l-m) + omega*ls + z_0i)))
    # print((z_coupled + 1j*omega*(lt - m)).imag/omega)
    return z_coupled
    
def calc_zeff(reff, leff, ct, omega, mode="series"):
    zl = omega*leff
    zc = 1/(ct*omega)
    if mode == "series":
        real = reff
        imag = zl - zc
    else:  # if parallel
        denom = reff**2 + (zl - zc)**2
        real = reff*zl**2 / denom
        imag = zl*(reff**2 + zc*(zc + zl)) / denom
    z_mag = np.sqrt(real**2 + imag**2)
    return (real, imag, z_mag)

def calc_cur_l(reff, rt, leff, lt, m, omega, l, ls, no_r=False, stabilize_tank=True):
    # only supports ls>0 cases if no_r
    rdiff = reff - rt
    ldiff = leff - lt
    if no_r and not stabilize_tank: cur_l = - m**2 / ldiff - ls - l
    else:
        num = (rdiff)**2*l**2 + omega**2*(m**2+ldiff*l)**2
        denom = -omega**2*ldiff*(m**2 + ldiff*l) - rdiff**2*l
        cur_l = num/denom
    return cur_l
    
def calc_r(reff, rt, leff, lt, m, omega, l, ls, no_r=False):
    # only supports ls>0 cases for no_r
    rdiff = reff - rt
    ldiff = leff - lt
    num = (rdiff)**2*l**2 + omega**2*(m**2+ldiff*l)**2
    if no_r:
        r = rdiff
    else:
        num = (rdiff)**2*l**2 + omega**2*(m**2+ldiff*l)**2
        denom = rdiff*m**2
        r = num/denom
    return r
