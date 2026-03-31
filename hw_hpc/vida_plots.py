import numpy as np
import matplotlib.pyplot as plt
from obspy.taup import TauPyModel

from obspy.geodetics import kilometers2degrees


###Inputs------------------------

velocity_model = 'iasp91'
max_depth = 300 #kilometers
max_dist = 250 #kilometers
grid_size = 60 #number of values for grid
uppermost_vel = 5.8 # uppermost velocity of velocity model, need to find way to pull directly
slow_cone = 0.05 #width of slowness cone, determines color levels. A smaller value will give smoother colors





###Functions--------------------

def taup_slow_dist_depth(velocity_model, max_depth, max_dist, grid_size, uppermost_vel):

    '''
    Calculates the slowness/distance/depth relation for a number of possible 
    earthquakes sources. Utilizes TauP 1D velocity model calculator.
    
    Parameters:
        velocity_model (str): velocity model for TauP ('ak135', 'iasp91')
        max_depth (int): max depth of earthquake sources
        max_dist (int): max distance of earthquake sources
        grid_size (int): number of grid points to create
        uppermost_vel (float): velocity of uppermost layer in velocity model in km/s
        
    Returns:
        depmat: meshgrid of depths
        distmat: meshgrid of distances
        slowmat: meshgrid of slowness
    '''

    model = TauPyModel(model=velocity_model)

    depth_min = 0 #kilometers
    depth_max = max_depth #kilometers, 100
    num_dep = grid_size
    num_dist = num_dep
    dist_min = 0 # kilometers
    dist_max = max_dist #kilometers

    depth_vec = np.linspace(depth_min,depth_max,num_dep)

    dist_vec = np.linspace(dist_min,dist_max,num_dist)

    distmat, depmat = np.meshgrid(dist_vec, depth_vec)

    slowmat = np.zeros((num_dep, num_dist))

    for i in range(num_dep):
        distances = distmat[i]
        depths = depmat[i]
        for j in range(num_dep):
            dist = kilometers2degrees(distances[j])
            arrivals = model.get_travel_times(source_depth_in_km=depths[j],
                                      distance_in_degree=dist) 
                            
            arr = arrivals[0]
            angle = arr.incident_angle
            vh = uppermost_vel/(np.sin(np.deg2rad(angle)))
            slow = 1/vh
            slowmat[i,j] = slow

    return depmat, distmat, slowmat


def vida_plot(distmat, slowmat, depmat):
    """
    Plot resembling the distance/depth/slowness relation from ViDA
    
    Parameters:
        depmat: meshgrid of depths
        distmat: meshgrid of distances
        slowmat: meshgrid of slowness
        
    Returns:
        plot of dist/depth/slowness
    """
    fig, ax = plt.subplots(figsize=(8,6))
    levels = np.linspace(0, 200, 200)
    sc = ax.contourf(distmat, slowmat, depmat, levels=levels, cmap='inferno_r', vmin = 0, vmax = 200) #jet_r, 90
    ax.set_xlabel('epicentral distance (kilometers)')
    ax.set_ylabel('horizontal slowness (s/km)')
    ax.set_ylim(0,0.20)
    fig.colorbar(sc, label = 'Depth (km)')
    #plt.savefig('/Users/cadequigley/Downloads/Research/paper_figures/japan1d_depth_estimate.png', transparent=True, dpi = 600)
    plt.show()



def dist_depth_slow_plot(distmat, slowmat, depmat, slow_cone):
    """
    Plot for distance/depth with slowness as color
    
    Parameters:
        depmat: meshgrid of depths
        distmat: meshgrid of distances
        slowmat: meshgrid of slowness
        slow_cone: width of slowness cone, use for making color segments more clear.
        
    Returns:
        plot of dist/depth/slowness
    """
    fig, ax = plt.subplots(figsize=(8,6))
    level = int(0.2/(slow_cone/2))
    levels = np.linspace(0, 0.2, level)
    sc = ax.contourf(distmat, depmat, slowmat, levels=levels, cmap='inferno', vmin = 0, vmax = 0.2) #jet_r, 90
    ax.set_xlabel('epicentral distance (kilometers)')
    ax.set_ylabel('depth (km)')
    ax.set_ylim(0,250)
    ax.set_xlim(0,250)

    fig.colorbar(sc, label = 'horizontal slowness (s/km)')
    ax.invert_yaxis()
    plt.show()


###Running--------------------
depmat, distmat, slowmat = taup_slow_dist_depth(velocity_model, max_depth,
                                                 max_dist, grid_size, 
                                                 uppermost_vel)

print('Calculation completed, starting plots')

vida_plot(distmat, slowmat, depmat)

dist_depth_slow_plot(distmat, slowmat, depmat, slow_cone)
