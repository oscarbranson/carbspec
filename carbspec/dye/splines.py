import json
import numpy as np
import pkg_resources as pkgrs
from scipy.interpolate import UnivariateSpline

def spline_handler(dye):
    """
    Returns splines for specified dye.

    Parameters
    ----------
    dye : str or dict
        Either the name of the dye in question, or a dict of dye splines.
    
    Returns
    -------
    splines for the acid and base end-members : aspl, bspl
    """
    if isinstance(dye, str):
        dye = load_splines(dye)

    return dye['acid'], dye['base']

def load_spline_tcks(file=None):
    if file is None:
        file = pkgrs.resource_filename('carbspec','resources/splines.json')
    with open(file, 'r') as f:
        splns = json.load(f)
    return splns

def save_spline(spln, dye, form, file=None, append=True, overwrite=False):
    """
    Save a spline describing an acid or base end-member for later use.

    Parameters
    ----------
    spln : scipy.interpolate.UnivariateSpline
        A UnivariateSpline object that has been fitted to the molal
        absorption of the acid or base form of a dye.
    dye : str
        The name of the dye.
    form : str
        The form of the dye that has been measured. Should be 
        'acid' or 'base'
    file : str
        The location of the file to save them in.
        If not given, defaults to the spline file in the 'resources' subdirectory
        of the package.
    append : bool
        If True, the new splines are added to the existing file.
    overwrite : bool
        Whether or not to overwrite an entry for a dye, if it is already
        in the database.
    """
    if file is None:
        file = pkgrs.resource_filename('carbspec','resources/splines.json')

    if append:
        try:
            splns = load_spline_tcks(file)
        except json.JSONDecodeError:
            splns = {}
            pass
    else:
        splns = {}
    
    tck = spln._eval_args
    
    if dye not in splns:
        splns[dye] = {}

    if form in splns[dye] and not overwrite:
        raise ValueError("The {:} form of {:} is already in the spline database. Either change the dye name, or set overwrite=True.".format(form, dye))
    
    splns[dye][form] = [list(tck[0]), list(tck[1]), tck[2]]
    
    with open(file, 'w') as f:
        json.dump(splns, f, sort_keys=True, indent=4)

def tck_2_array(tck):
    return tuple([np.asanyarray(a) for a in tck[:-1]] + [tck[-1]])

def load_splines(dye='BPB', file=None):
    """
    Load saved splines for 
    """
    splines = load_spline_tcks(file)[dye]

    return {k: UnivariateSpline._from_tck(tck_2_array(tck)) for k, tck in splines.items()}

def list_available(file=None):
    """
    List available dye splines.
    """
    splns = load_spline_tcks(file)

    out = ["Available Splines:",
           "------------------"]
    
    for k, v in splns.items():
        out.append('{:}:'.format(k))
        for k2 in v.keys():
            out.append('  - {:}'.format(k2))

    out.append("------------------")

    print('\n'.join(out))