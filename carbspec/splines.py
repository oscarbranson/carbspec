import json
import pkg_resources as pkgrs
from scipy.interpolate import UnivariateSpline

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

def load_dye_splines(dye='BPB', file=None):
    """
    Load saved splines for 
    """

    splines = load_spline_tcks(file)[dye]

    return {k: UnivariateSpline._from_tck(v) for k, v in splines.items()}

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