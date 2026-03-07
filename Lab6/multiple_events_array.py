import pandas as pd
import numpy as np
from scipy import stats
import obspy
from obspy import read_events
from obspy import Stream
from obspy import Trace
from obspy.core import UTCDateTime
from scipy import stats
from obspy.clients.fdsn import Client
from obspy.geodetics import gps2dist_azimuth
from obspy.core.util import AttribDict
from obspy.imaging.cm import obspy_sequential
from obspy.signal.invsim import corn_freq_2_paz
from obspy.signal.array_analysis import array_processing
from obspy.signal.trigger import recursive_sta_lta, trigger_onset, classic_sta_lta
from obspy.core import UTCDateTime
from obspy.clients.fdsn.header import FDSNNoDataException
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

import lts_array

#Functions needed fro code----------------------------
from array_functions import (data_from_inventory, get_geometry, pull_earthquakes,
                             check_num_stations, stations_available_generator,
                             array_time_window, moveout_time, grab_preprocess,
                             least_trimmed_squares, triggers, fk_obspy)
from array_figures import baz_error_spatial, slow_error_spatial


'''
Conducts array analysis for a set array and number of events in the vicinity
of the array. This can be used to determine how well an array is performing,
and how errors are occuring spatially.
    
Parameters:
    use_full_deployment: whether to use full time window deployment was out (True or False)
    start_d1_list: list of start times for each station
    end_d1_list: list of end times for each station
    starttime: specified starttime, will use if use_full_deployment = True
    endtime: speficied endtime, will use if use_full_deployment = True

Returns: 
    df: dataframe containing earthquake information, array output parameters,
    plots: baz error, slowness error
        
        
    '''

#from array_functions import rotate_data

###############################
#----------INPUTS---------------
###############################

#station/array inputs----------
net = '9C' #9C, 4E, 5E, UW, XG
sta = '2A*' #'2A*', '3A*', 'POM*', S1**, UIL*, LC*, IL*
loc = '*' #0
chan = 'SHZ' #SHZ, DHZ, HHZ
client = 'IRIS' #IRIS, GEOFON, path, #if 'path', create new variable path =
starttime = '2015-10-01' #'2015-10-01' , '2011-05-11' '2025-09-07'
endtime = '2015-10-12'#'2015-10-02' , '2013-05-01', '2025-11-13'
min_stations = 8 # if you only want times with all stations, list the number of stations
remove_stations =  []#['3A10', '3A15'] #['POM06', 'POM07', 'POM18'] #['3A10', '3A15'] # ['POM06', 'POM07', 'POM18']
keep_stations = [] #****NOT WORKING YET****
array_name = '2A' #2A, 3A, POM, KD, HM, S1, UIL
use_full_deployment = False #if True, searches for full deployment length in inventory and finds all events
path_to_inventory = None #if inventory object is stored locally
save = False #save the dataframe to CSV or not

#Earthquake inputs----------
min_mag = '3.0' #minimum magnitude
max_rad = '600' #maximum radius from arrays
velocity_model = 'iasp91' #iasp91, pavdut, scak, ak135

#Array processing---------------
processing = 'fk' #ls, fk, lts
FREQ_MIN = 0.5
FREQ_MAX = 18.0
WINDOW_LENGTH = 2.5 #seconds

# Window overlap decimal [0.0, 1.0)
WINDOW_OVERLAP = (WINDOW_LENGTH-0.25)/WINDOW_LENGTH #0.25s between each window

window_start = -1 #1 second before trigger

# Inputs for sta/lta-------

timing = 'trigger' #'power', 'trigger', NEED TO FIX POWER
min_triggers = min_stations // 3 #minimum station triggers to associate
ptolerance = 5 #seconds, +/- around p-arrival
multiple_triggers = 'peak' #'closest', 'peak', which trigger to choose if multiple

#Inputs for FK array processing---------

sll_x=-1.0 # X min, X max, Y min, Y max, Slow Step
slm_x=1.0 # X max
sll_y=-1.0 # Y min
slm_y=1.0 # Y max
sl_s=0.03 # Slow Step

# restrict output
semb_thres=-1e9
vel_thres=-1e9
timestamp='mlabday'
prewhiten = 0


###############################
#----------PROCESSING-----------
###############################

#Pull inventory-----------------------
#------------------------------------------------
if client == 'path':
    inv = read_inventory(path_to_inventory) #need to add something at some point about
else:
    #client = Client(client, user="caquigley@alaska.edu", password="U9sWxXLREK4FsdUX", debug = True)
    client = Client(client)


    inv = client.get_stations(network=net, station=sta, channel=chan,
                                location=loc, starttime=UTCDateTime(starttime),
                                endtime=UTCDateTime(endtime), level='response') #level = 'channel'
#Pull station information out of inventory
(lat_list, lon_list, elev_list, station_d1_list,
 start_d1_list, end_d1_list, num_channels_d1_list) = data_from_inventory(inv, 
                                                                         remove_stations, 
                                                                         keep_stations)

check = check_num_stations(min_stations, station_d1_list)

data = {
        'station': station_d1_list,
        'lat': lat_list,
        'lon': lon_list,
        'elevation': elev_list}

#Save stations for later
station_info = pd.DataFrame(data) 


#Pull earthquakes-----------------------
#------------------------------------------------

# Get center of array--------
output = get_geometry(lat_list, lon_list, elev_list, return_center = True)
origin_lat = str(output[-1][1])
origin_lon = str(output[-1][0])
# Get expected moveout time--------
moveout = moveout_time(output)

#Pull earthquakes during deployment
start, end = array_time_window(use_full_deployment, start_d1_list, end_d1_list,
                               starttime, endtime)
df = pull_earthquakes(origin_lat, origin_lon, max_rad, start, end, min_mag, 
                      array_name, velocity_model)
print('Number of earthquakes >'+min_mag+' within '+max_rad+' km:', len(df))


#Create station availability lists-----------------------
#------------------------------------------------
earthquake_time = df['time_utc'].to_numpy()
earthquake_names = df['event_id'].to_numpy()

stations_lists, stations_available = stations_available_generator(earthquake_time, station_d1_list, start_d1_list, end_d1_list)

### Drop events that don't have enough stations present--------------
bad_idx = [i for i, v in enumerate(stations_available) if v < min_stations]
keep_idx = [i for i, v in enumerate(stations_available) if v >= min_stations]

stations_available = [stations_available[i] for i in keep_idx]
stations_lists = [stations_lists[i] for i in keep_idx]
df = df.drop(index=bad_idx)

print('Station lists for each earthquake created. New earthquake number:', len(df))

###Loop over all events---------------------------------

event_ids = df['event_id'].to_numpy()
eq_depths = df['depth'].to_numpy()
eq_lats = df['latitude'].to_numpy()
eq_lons = df['longitude'].to_numpy()
eq_time = df['time_utc'].to_numpy()
expected_parrival = df['p_arrival'].to_numpy()
eq_baz = df['backazimuth'].to_numpy()
eq_slow = df['slowness'].to_numpy()
eq_distance = df['distance'].to_numpy()
array_data_list = []
for event in range(len(df)):
    try:
        print("Starting", event_ids[event])
        stations = stations_lists[event] #pull out stations available for each event
        eq_slow_real = eq_slow[event]
        eq_baz_real = eq_baz[event]
        event_id = event_ids[event]

        #Pull out one minute on either side of expected arrival time
        START = UTCDateTime(eq_time[event])+expected_parrival[event]-60 
        END = START +120

        ###Grab and preprocess data----------------------------
        (st, stations, sta_lats, 
         sta_lons, sta_elev) = grab_preprocess(stations, station_info, inv, 
                                               net, loc, chan, min_stations, 
                                               START, END, FREQ_MIN, FREQ_MAX,
                                               client)
        
        st1 = st.copy() #Pulling this out for FK

        ###Finding triggers---------------------------------
        if timing == 'trigger': #use sta/lta triggers
            (st, trigger, peak, length, 
             trigger_type, trigger_time, 
             START_new, END_new)= triggers(st, moveout, min_triggers, 
                                                   ptolerance, START, 
                                                   window_start, 
                                                   WINDOW_LENGTH, 
                                                   multiple_triggers)
    
                

        ###Array processing---------------------------------
        ##Least squares--------------------
        if processing == 'lts' or processing == 'ls':

            array_data = least_trimmed_squares(processing, st, sta_lats, sta_lons, 
                                       WINDOW_LENGTH, WINDOW_OVERLAP,
                                       trigger_time, trigger_type, peak,
                                       length, origin_lat, origin_lon, 
                                       event_id, eq_baz_real, eq_slow_real)
            
        ##Frequency wavenumber--------------------
        else: 
            array_data = fk_obspy(st1, stations, sta_lats, sta_lons, sta_elev, START, START_new, END_new,
                                  WINDOW_LENGTH, WINDOW_OVERLAP, FREQ_MIN, FREQ_MAX,
                                  sll_x, slm_x, sll_y, slm_y, sl_s, semb_thres, vel_thres, timestamp, prewhiten,
                                  eq_baz_real, eq_slow_real, event_id, trigger, trigger_type, peak, length, origin_lat, origin_lon)


    ################################################################      
    
        array_data_list.append(array_data)

        print('Events completed:', str(event+1)+'/'+str(len(df)))

    except ValueError as e:
        print(f"Skipping event {event_ids[event]}: {e}")
        continue

    except Exception as e:
        print(f"Unexpected error for event {event_ids[event]}: {e}")
        continue

#Putting data into single dataframe----------------------
array_data_comb1 = pd.concat(array_data_list, ignore_index=True)

#Combining with earthquake data-----------------------
array_data_comb = pd.merge(array_data_comb1, df, on='event_id', how='inner')

if save == True:
    array_data_comb.to_csv(array_name+'_'+max_rad+'km_m3_fk_wawa.csv')

#Plot some figures
df = array_data_comb
color_data = df['distance']
color_label = 'earthquake distance (km)'
model_data = []
baz_error_spatial(df['backazimuth'], df['baz_error'], model_data, color_data, color_label, niazi = True,
                  save = False, path = '/Users/cadequigley/Downloads/Research/gigls_2026/POM_baz_error_spatial.png')

slow_error_spatial(df['backazimuth'], df['slow_error'], model_data, color_data, color_label, niazi = True, 
                   save = False, path = '/Users/cadequigley/Downloads/Research/gigls_2026/POM_slow_error_spatial.png')

