""" various function useful to analyze the outlet glacier model
"""
import numpy as np

def massbalance_diag(glacier1d):
    """ diagnose surface mass balance, submelt and velocity divergence 
    to analyze the glacier equilibrium
    """
    # cumulative surface mass balance in m^3/s over whole catchment basin
    dx = glacier1d.x[1]-glacier1d.x[0]
    W = glacier1d['W']
    H = glacier1d['H']
    A = H*W # section area
    smb_cum = glacier1d['smb'].cumsum()*W*dx
    smb_cum.units = 'meters^3 / second'

    glacier1d_diag = glacier1d.copy() # shallow copy
    glacier1d_diag['cumulative_smb'] = smb_cum

    # various velocity based diagnostic for surface and basal velocities
    # compute ice flux for various velocities
    for v, nm in [('U', 'ice_flux_surf_obs'), ('balvelmag','ice_flux_bal_mod3D')]:
        # flux through cross-section
        F = A*glacier1d[v]
        F.units = 'meters^3 / second'
        glacier1d_diag[nm] = F

    # balance velocity
    A[np.abs(H)<10] = np.nan # thickness less than 10m is an invalid glacier
    balance_velocity = smb_cum / A
    balance_velocity[np.isnan(balance_velocity)] = 0

    glacier1d_diag['balance_velocity_obs'] = balance_velocity
    glacier1d_diag['balance_velocity_mod3D'] = glacier1d_diag['balvelmag']

    # # velocity divergence 
    # div
    
    return glacier1d_diag
