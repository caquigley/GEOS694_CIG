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
from array_functions import data_from_inventory
from array_functions import get_geometry
from array_functions import pull_earthquakes
from array_functions import check_num_stations
from array_functions import stations_available_generator
from array_functions import array_time_window
from array_functions import moveout_time
from array_functions import grab_preprocess
from array_functions import least_squares
from array_functions import triggers

#from array_functions import rotate_data

###############################
#----------INPUTS---------------
###############################

#station/array inputs----------
net = '9C' #9C, 4E, 5E, UW, XG
sta = '3A**' #'2A*', '3A*', 'POM*', S1**, UIL*, LC*, IL*
loc = '*' #0
chan = 'SHZ' #SHZ, DHZ, HHZ
client = 'IRIS' #IRIS, GEOFON, path, #if 'path', create new variable path =
starttime = '2015-10-01' #'2015-10-01' , '2011-05-11' '2025-09-07'
endtime = '2015-10-15'#'2015-10-02' , '2013-05-01', '2025-11-13'
min_stations = 10 # if you only want times with all stations, list the number of stations
remove_stations =  ['3A10', '3A15'] #['POM06', 'POM07', 'POM18'] #['3A10', '3A15'] # ['POM06', 'POM07', 'POM18']
keep_stations = [] #****NOT WORKING YET****
array_name = '3A' #2A, 3A, POM, KD, HM, S1, UIL
use_full_deployment = False
path_to_inventory = None
save = False

#Earthquake inputs----------
min_mag = '3.0' #minimum magnitude
max_rad = '400' #maximum radius from arrays
velocity_model = 'iasp91' #iasp91, pavdut, scak, ak135

#Array processing---------------
processing = 'lts' #ls, fk, lts
FREQ_MIN = 0.5
FREQ_MAX = 18.0
WINDOW_LENGTH = 2.5 #seconds

# Window overlap decimal [0.0, 1.0)
WINDOW_OVERLAP = (WINDOW_LENGTH-0.25)/WINDOW_LENGTH #0.25s between each window

window_start = -1 #1 second before trigger

# Inputs for sta/lta-------

timing = 'trigger' #'power', 'trigger'
min_triggers = 3 #minimum station triggers to associate
ptolerance = 5 #seconds, +/- around p-arrival
multiple_triggers = 'peak' #'closest', 'peak'

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

        ###Finding triggers---------------------------------
        if timing == 'trigger': #use sta/lta triggers
            (st, trigger, peak, length, 
             trigger_type, trigger_time)= triggers(st, moveout, min_triggers, 
                                                   ptolerance, START, 
                                                   window_start, 
                                                   WINDOW_LENGTH, 
                                                   multiple_triggers)
            print(trigger_type)
                

        ###Array processing---------------------------------
        ##Least squares--------------------
        if processing == 'lts' or processing == 'ls':

            array_data = least_squares(processing, st, sta_lats, sta_lons, 
                                       WINDOW_LENGTH, WINDOW_OVERLAP,
                                       trigger_time, trigger_type, peak,
                                       length, origin_lat, origin_lon, 
                                       event_id, eq_baz_real, eq_slow_real)
            

        ##Frequency wavenumber--------------------
        else: #fk analysis
            ####IM IGNORING THE FK STUFF NOW AND JUST FOCUSING ON LTS

            print('Starting FK')
            #Add necessary data to streams----------------
            for l in range(len(stations)):  # Uses all stations in pd dataframe stations
                st1[l].stats.coordinates = AttribDict({
                    'latitude': sta_lats[l],
                    'elevation': sta_elev[l],
                    'longitude': sta_lons[l]})
    
            kwargs = dict(
                # slowness grid: X min, X max, Y min, Y max, Slow Step
                sll_x=sll_x, slm_x=slm_x, sll_y=sll_y, slm_y=slm_y, sl_s=sl_s,
                # sliding window properties
                win_len=WINDOW_LENGTH, win_frac=WINDOW_OVERLAP,
                # frequency properties
                frqlow=FREQ_MIN, frqhigh=FREQ_MAX, prewhiten=prewhiten,
                # restrict output
                semb_thres=semb_thres, vel_thres=vel_thres, timestamp=timestamp,
                stime=START+0.2, etime=END-0.2 #had to add and subtract to avoid timing errors
                )
            out = array_processing(st1, **kwargs)
    
            #OUTPUT FROM FK PROCESSING-----------------------------------------------------
            array_out = pd.DataFrame(out, columns = ['time','relpow','abspow','baz_obspy','array_slow'])
        

            t = array_out['time'].to_numpy()
            baz_obspy = array_out['baz_obspy'].to_numpy()
        
            bazs = []
            time_error = []
            for j in range(len(t)):
                matplotlib_time = t[j]
                x = mdates.num2date(matplotlib_time) 
                x = UTCDateTime(x)
                #diff = (x-UTCDateTime(time_station))+(win_len/2)
                diff = str(x+(WINDOW_LENGTH/2)) #time centered on point
                time_error.append(diff)
                baz = baz_obspy[j]
                if baz <= 0:
                    baz_correct = baz+360 #converts to all positive backazimuth
                else:
                    baz_correct = baz
                bazs.append(baz_correct)
        
            time_error = np.array(time_error)
            fk_bazs = np.array(bazs)

            fk_baz_error = baz_error(eq_baz[event], fk_bazs)

            trace_vel_error = (1/eq_slow[event])- 1/array_out['array_slow'].to_numpy() #real - array

            slowness_error = (eq_slow[event]) - array_out['array_slow'].to_numpy()

            array_out['baz_error'] = fk_baz_error
            array_out['centered_time'] = time_error
            array_out['array_baz'] = fk_bazs
            array_out['slow_error'] = slowness_error

            #Pull out greatest power------------
            idx = np.argmax(array_out['relpow'].to_numpy())
        
            array_data = array_out.loc[[idx]]
            array_data['event_id'] = event_ids[event]
            array_data['trigger_type'] = trigger_type
            array_data['trigger_time'] = str(START+trigger)





    ################################################################      
    
        array_data_list.append(array_data)

        print('Events completed:', str(event)+'/'+str(len(df)))

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
    array_data_comb.to_csv(array_name+'_400km_m3_.csv')


