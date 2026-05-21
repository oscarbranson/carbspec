import os, shutil
from importlib.resources import as_file, files

def get_TA_weight_template(dir, overwrite=False):
    """Get the template for the TA weight file.

    Parameters
    ----------
    dir : str
        The directory in which to save the template.

    Returns
    -------
    None
    """
    template_path = files('carbspec').joinpath('cmd/resources/TA_weights.ods')

    savepath = os.path.join(dir, 'TA_weights.ods')
    
    if os.path.exists(savepath) and not overwrite:
        raise ValueError('TA_weights.ods already exists in this directory. Set overwrite=True to overwrite.')
    
    with as_file(template_path) as src_path:
        shutil.copy2(src_path, dir)