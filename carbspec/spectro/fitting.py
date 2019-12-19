import numpy as np
from scipy.optimize import least_squares

def Jacobian(x, wv, aspl, bspl, daspl, dbspl, sigma, **kwargs):
    """
    Calculate the jacobian for the minimisation function.

    Parameters
    ==========
    x : tuple
        A tuple containing the model parameters as (a, b, m, c, B0)
    wv : array-like
        The wavelength of the data
    aspl, bspl : UnivariateSpline
        Spline objects that produce the acid (aspl) or base (aspl)
        molal absorption given a wavelength.
    daspl, sbspl : UnivariateSpline
        Spline objects that return the first derivative of aspl and
        bspl at a given wavelength.
    
    Returns
    =======
    Jacobian of fitting function as a matrix of shape (n,m) : array-like
    """
    a, b, m, c, B0 = x
    
    J = np.ones((len(wv), 5))
    
    J[:,0] = aspl(wv * m + c)
    J[:,1] = bspl(wv * m + c)
    J[:,2] = wv * a * daspl(wv * m + c) + wv * b * dbspl(wv * m + c)
    J[:,3] = a * daspl(wv * m + c) + b * dbspl(wv * m + c)
    
    return J / sigma.reshape(-1,1)  # this pre-scales the jacobian so that it's appropriate for scaled residuals

def specmix(x, wv, aspl, bspl, **kwargs):
    """
    Return the mixture of aspl and bspl sepcified by the parameters in x.

    Parameters
    ==========
    x : tuple
        A tuple containing the model parameters as (a, b, m, c, B0)
    wv : array-like
        The wavelength of the data
    aspl, bspl : UnivariateSpline
        Spline objects that produce the acid (aspl) or base (aspl)
        molal absorption given a wavelength.
    """
    a, b, m, c, B0 = x
    return a * aspl(m * wv + c) + b * bspl(m * wv + c) + B0

def obj_fn(x, wv, Abs, sigma, aspl, bspl, **kwargs):
    """
    Objective function for least squares optimisation
    """
    return (specmix(x, wv, aspl, bspl) - Abs) / sigma
    # divide by sigma makes this equivalent to multiplying by 1 / sigma**2 once the sumsq of residuals is calculated.

def jac_2_cov(fit):
    """
    Calculate the covariance matrix from the jacobian contained within a least_squares result.
    
    Parameters
    """
    s_sq = 2 * fit.cost / (fit.fun.size - fit.x.size)  # RSS / DOF; fit.cost is half the sum of squares (see curve_fit source)
    # covariance matrix is inverse of hessian (H = J.dot(J.T)) scaled to MSE.
    return np.linalg.inv(fit.jac.T.dot(fit.jac)) * s_sq 

def fit_spectrum(wv, Abs, aspl, bspl, sigma=np.array(1), pstart=[0.1, 0.1, 1, 0, 0]):
    """
    Fit a spectrum with a combination of end-member spectra.

    Parameters
    ==========
    wv : array-like
        The wavelength of the absorption spectrum
    Abs : array-like
        The absorption spectrum
    aspl, bspl : UnivariateSpline
        Spline objects that produce the acid (aspl) or base (aspl)
        molal absorption given a wavelength.
    sigma : arra-like
        The standard deviation of the data.

    Returns
    =======
    p, cov  : the optimal values for (a, b, m, c, B0) and their covariance matrix
    """
    fit = least_squares(obj_fn, pstart, Jacobian, 
                        kwargs=dict(wv=wv, Abs=Abs, sigma=sigma, aspl=aspl, bspl=bspl, daspl=aspl.derivative(), dbspl=bspl.derivative()), 
                        bounds=((0, 0, 0.95, -20, -0.2), (np.inf, np.inf, 1.05, 20, 0.2)), method='trf')
    return fit.x, jac_2_cov(fit)
