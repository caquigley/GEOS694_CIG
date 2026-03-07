import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from obspy.geodetics import gps2dist_azimuth
from matplotlib.transforms import blended_transform_factory
from array_functions import cos_model
from scipy.optimize import curve_fit


#plot_type = 'close' #'close', 'far'
#plot_type = 'far' #'close', 'far'

#station_sub = station_info[station_info['station'].isin(stations)]
#sta_lats = station_sub['lat'].to_numpy()
#sta_lons = station_sub['lon'].to_numpy()
#stations = station_sub['station'].to_numpy()


def record_section(st, stations, sta_lats, sta_lons, mag, channel, plot_type):

    fig, ax = plt.subplots(figsize = (10,8))

    trans = blended_transform_factory(ax.transAxes, ax.transData)

    distance = []
    for i in range(len(st)):
        tr = st[i]
        station = stations[i]
        dist,baz,az = gps2dist_azimuth(sta_lats[i], sta_lons[i], eq_lat, eq_lon)
        ypos = dist/1000
        distance.append(ypos)
        time_range = np.max(tr.times()) - np.min(tr.times())
        ax.plot(tr.times()-time_range/2,ypos+((tr.data/(4*max(tr.data)))), color = 'black', alpha = 0.8)
        ax.text(1.01, ypos, station, transform=trans, color = 'black', fontweight = 'bold',fontsize = 10, ha="left", va="center")
    
    plt.axvline(x=0, color = 'red', linestyle = '--')
    distance = np.array(distance)
    ax.text(0.05, max(distance)+0.25, 'Event: '+event+'; M'+str(mag)+'; '+channel, transform = trans, fontsize = 15, fontweight = 'bold', color = 'firebrick')
    ax.set_xlabel('Time since estimated arival time (s)')
    ax.set_ylabel('Distance from earthquake (km)')
    if plot_type =='far':
        ax.set_xlim(-time_range/2,time_range/2)
    else:
        ax.set_xlim(-6+time_range/2,6+time_range/2)
    ax.grid(alpha = 0.3)
    plt.show()

def trigger_timing(st, start):
    fig, ax = plt.subplots(figsize=(8, 4))
      

    for i in range(len(st)):
        tr = st[i]
        normalized = tr.data/np.max(abs(tr.data))
        ax.plot(tr.times()-start, normalized, color="black", alpha = 0.1)
    
    
    ax.set_xlabel('Time relative to pick')
    ax.set_ylabel('Normalized Counts')
    ax.grid(alpha=0.3)
    #ax.set_xlim(-4, 8)

    ax.axvline(x=0, color='red', linestyle='--')

    plt.show()


#########################################################
#niazi = True

#baz_error_model = []


def baz_error_spatial(baz, baz_error, baz_error_model, color_data, color_data_label, niazi = True, save = False, path = None):

    fig, ax = plt.subplots(figsize = (7,4))
    
    trans = blended_transform_factory(ax.transData, ax.transAxes)

    if len(baz_error_model) > 0:
        ax.scatter(baz, baz_error, color = 'gray', edgecolors = 'black', s = 100, label = 'measured')
        ax.scatter(baz, baz_error_model, color = 'red', edgecolors = 'black', s = 100, label = 'modeled')
    else:

        if len(color_data) > 0:
            sc = ax.scatter(baz, baz_error, c = color_data, cmap = 'plasma_r', edgecolors = 'black', s = 100)
            fig.colorbar(sc, label = color_data_label)
        else:
            ax.scatter(baz, baz_error, color = 'gray', alpha = 1, edgecolors = 'black', s = 100, label = 'observed')

    

    if niazi == True:
        
        p0 = [1.0, 10.0, 180.0]   # a, b, phi guesses

        Z_data = baz
        y_data = baz_error
        params, cov = curve_fit(cos_model, Z_data, y_data, p0=p0)
        a_fit, b_fit, phi_fit = params
        #Plot niazi fit
        Z_fit = np.linspace(0, 360, 500)
        y_fit = cos_model(Z_fit, *params)
        ax.plot(Z_fit, y_fit, color = 'red', linewidth = 2.5, label = 'Niazi fit', alpha= 0.5)

    ax.text(45,0.9, "NE", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')
    ax.text(135,0.9, "SE", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')
    ax.text(225,0.9, "SW", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')
    ax.text(315,0.9, "NW", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')

    ax.axvline(x=90, color = 'black', linestyle = '--')
    ax.axvline(x=180, color = 'black', linestyle = '--')
    ax.axvline(x=270, color = 'black', linestyle = '--')
    ax.axhline(y=0, color = 'red', linestyle = '--', alpha = 0.3)

    ax.grid(alpha = 0.3)
    ax.set_xlabel('catalog backazimuth (degrees)')
    ax.set_ylabel('backazimuth error (degrees)')
    ax.set_xlim(0,360)
    #ax.set_ylim(-np.max(abs(baz_error)),np.max(abs(baz_error)))
    ax.set_ylim(-80,80)

    ax.invert_xaxis()
    plt.legend(loc = 'upper left', bbox_to_anchor=(0, 0.25))
    
    if save == True:
            fig.savefig(path, transparent=True, dpi=720)
    #plt.savefig('./slow_error_'+array+'snell_nonfixed_3s', transparent=True, dpi = 720)
    plt.show()

#########################################################
niazi = True

slow_error_model = []


def slow_error_spatial(baz, slow_error, slow_error_model, color_data, color_data_label, niazi = True, save = False, path = None):

    fig, ax = plt.subplots(figsize = (7,4))
    
    trans = blended_transform_factory(ax.transData, ax.transAxes)


    if len(slow_error_model) > 0:
        ax.scatter(baz, slow_error, color = 'gray', edgecolors = 'black', s = 100, label = 'measured')
        ax.scatter(baz, slow_error_model, color = 'skyblue', edgecolors = 'black', s = 100, label = 'modeled')
    else:
        if len(color_data) > 0:
            sc = ax.scatter(baz, slow_error, c = color_data, cmap = 'cividis_r', edgecolors = 'black', s = 100)
            fig.colorbar(sc, label = color_data_label)
        else:
            ax.scatter(baz, slow_error, color = 'gray', alpha = 1, edgecolors = 'black', s = 100, label = array+' observed')

    
    if niazi == True:
        
        p0 = [1.0, 10.0, 180.0]   # a, b, phi guesses

        Z_data = baz
        y_data = slow_error
        params, cov = curve_fit(cos_model, Z_data, y_data, p0=p0)
        a_fit, b_fit, phi_fit = params
        #Plot niazi fit
        Z_fit = np.linspace(0, 360, 500)
        y_fit = cos_model(Z_fit, *params)
        ax.plot(Z_fit, y_fit, color = 'red', linewidth = 2.5, label = 'Niazi fit', alpha= 0.5)

    ax.text(45,0.9, "NE", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')
    ax.text(135,0.9, "SE", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')
    ax.text(225,0.9, "SW", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')
    ax.text(315,0.9, "NW", transform = trans, color = 'black', fontweight = 'bold',fontsize = 15, ha='center')

    ax.axvline(x=90, color = 'black', linestyle = '--')
    ax.axvline(x=180, color = 'black', linestyle = '--')
    ax.axvline(x=270, color = 'black', linestyle = '--')
    ax.axhline(y=0, color = 'red', linestyle = '--', alpha = 0.3)

    ax.grid(alpha = 0.3)
    ax.set_xlabel('catalog backazimuth (degrees)')
    ax.set_ylabel('slowness error (s/km)')
    ax.set_xlim(0,360)
    #ax.set_ylim(-np.max(abs(slow_error))-0.05,np.max(abs(slow_error))+0.05)
    ax.set_ylim(-0.2, 0.2)

    ax.invert_xaxis()
    plt.legend(loc = 'upper left', bbox_to_anchor=(0, 0.25))
    
    if save == True:
        fig.savefig(path, transparent=True, dpi=720)
    #plt.savefig('./slow_error_'+array+'snell_nonfixed_3s', transparent=True, dpi = 720)
    plt.show()

def vida_plot(distmat, slowmat, depmat):
    fig, ax = plt.subplots(figsize=(8,6))
    levels = np.linspace(0, 200, 200)
    sc = ax.contourf(distmat, I, depmat, levels=levels, cmap='inferno_r', vmin = 0, vmax = 200) #jet_r, 90
    ax.set_xlabel('epicentral distance (kilometers)')
    ax.set_ylabel('horizontal slowness (s/km)')
    ax.set_ylim(0,0.20)
    fig.colorbar(sc, label = 'Depth (km)')
    #plt.savefig('/Users/cadequigley/Downloads/Research/paper_figures/japan1d_depth_estimate.png', transparent=True, dpi = 600)
    plt.show()


slow_cone = 0.05 #width of slowness cone of interest, determines the color levels

def dist_depth_slow(distmat, slowmat, depmat, slow_cone ):
    fig, ax = plt.subplots(figsize=(8,6))
    level = 0.2/(slow_cone/2)
    levels = np.linspace(0, 0.2, level)
    sc = ax.contourf(distmat, depmat, I, levels=levels, cmap='inferno', vmin = 0, vmax = 0.2) #jet_r, 90
    ax.set_xlabel('epicentral distance (kilometers)')
    ax.set_ylabel('depth (km)')
    ax.set_ylim(0,250)
    ax.set_xlim(0,250)

    fig.colorbar(sc, label = 'horizontal slowness (s/km)')
    ax.invert_yaxis()
    plt.show()


def histogram(values, lower_quantile, upper_quantile, variable_name, save = False, path = None):
    fig, ax = plt.subplots(figsize=(6, 4,))

    if variable_name =='slowness_error':
        xlim1 = -0.2
        xlim2 = 0.2
        hist_params = {
            'color': 'skyblue',
            'bins': 30, #0.01 s/km per bin
            'range': (-0.15, 0.15),
            'edgecolor': 'black'
            }
        label = 'slowness error (s/km)'
    elif variable_name =='backazimuth_error':
        xlim1 = -180
        xlim2 = 180
        
        hist_params = {
            'color': 'firebrick',
            'bins': 80, #5 degrees per bin
            'range': (-200, 200),
            'edgecolor': 'black'
            }
        label = 'backazimuth error (degrees)'
    elif variable_name == 'distance_error':
        xlim1 = -10
        xlim2 = 800
        hist_params = {
            'color': 'purple',
            'bins': 80, #10 km per bin
            'range': (0, 800),
            'edgecolor': 'black'
            }
        label = 'distance error (km)'
    


    ax.axvspan(xlim1,np.quantile(values, lower_quantile), color = 'gray',alpha = 0.1)

    ax.axvspan(np.quantile(values, upper_quantile),xlim2, color = 'gray',alpha = 0.1)
    ax.axvspan(np.quantile(values, lower_quantile), np.quantile(values, upper_quantile), color = 'blue',alpha = 0.1)

    ax.hist(values, **hist_params)

    ax.set_xlabel(label, fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.grid(axis='y', alpha=0.8)


    ax.axvline(x=np.quantile(values, upper_quantile), ymin = 0, ymax = 1, color = 'black', linestyle = '--')
    ax.axvline(x=np.quantile(values, lower_quantile), ymin = 0, ymax = 1, color = 'black', linestyle = '--')
    range1 = (np.abs(np.quantile(values, lower_quantile))+np.abs(np.quantile(values, upper_quantile)))
    print('Quantile range:', range1)
#c = temp['slowness_error']
#range2 = (np.abs(np.quantile(c, 0.05))+np.abs(np.quantile(c, 0.95)))

    ax.set_xlim(xlim1, xlim2)
    if save == True:
        fig.savefig(path, transparent=True, dpi=720)

    plt.show()
    #print('Quantile range before correction:', range2)
    #print('Quantile range after correction:', range1)
    #print('Percent improvement:', ((range2-range1)/range2)*100)
    #slow_improve = ((range2-range1)/range2)*100


