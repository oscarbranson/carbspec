import numpy as np

# from Galban et al, 2007
def thermal_noise(Abs, k1):
    return k1 * (1 + 10**(-2 * Abs))**0.5

def rel_thermal_noise(Abs, k1):
    return 0.434 * k1 * (1 + 10**(2 * Abs))**0.5 / Abs

def photon_noise(Abs, k2):
    return k2 * (10**-Abs + 10**(-2 * Abs))**0.5

def rel_photon_noise(Abs, k2):
    return 0.434 * k2 * (1 + 10**(Abs))**0.5 / Abs

def cell_position_noise(Abs, k3):
    return k3 * 10**-Abs

def rel_cell_position_noise(Abs, k3):
    return 0.434 * k3 / Abs

def combine_errors(Abs, *it):
    noise = np.zeros(Abs.size)
    for i in it:
        noise += (i / Abs)**2
    
    return Abs * noise**0.5

def combine_rel_errors(*it):
    errors = np.array(it)**2
    return errors.sum(0)**0.5

def rel_photometric_error(Abs, sT):
    return (0.434 / Abs) * (sT / 10 ** -Abs)

def calc_rel_photometric_error(Abs, k1=0, k2=0, k3=0):
    shot = thermal_noise(Abs, k1)
    photon = photon_noise(Abs, k2)
    cell = cell_position_noise(Abs, k3)
    
    # return combine_rel_errors(shot, photon, cell)
    noise = combine_errors(Abs, shot, photon, cell)
    
    return rel_photometric_error(Abs, noise)

def calc_rel_photometric_error_const(Abs, k1=0, k2=0, k3=0, c=0):
    shot = thermal_noise(Abs, k1)
    photon = photon_noise(Abs, k2)
    cell = cell_position_noise(Abs, k3)
    
    # return combine_rel_errors(shot, photon, cell)
    noise = combine_errors(Abs, shot, photon, cell)
    
    return rel_photometric_error(Abs, noise) + c


def calc_photometric_error(Abs, k1=0, k2=0, k3=0):
    return Abs * calc_rel_photometric_error(Abs, k1=k1, k2=k2, k3=k3)

def ANU_spec_RSD(Abs, mode='static'):
    if mode == 'static':
        return calc_rel_photometric_error_const(Abs, 4.81640855e-04,  1.15596397e-07, -6.01500894e-08,  6.43798590e-03)
    elif mode == 'replace':
        return calc_rel_photometric_error_const(Abs, 2.42725297e-03, -1.71163800e-06,  1.28754221e-02,  1.23247589e-03)

def ANU_spec_sigma(Abs, mode='static'):
    return ANU_spec_RSD(Abs, mode=mode) * Abs