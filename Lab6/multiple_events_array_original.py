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

from array_functions import calculate_slowness
from array_functions import data_from_inventory
from array_functions import get_geometry
from array_functions import pull_earthquakes
from array_functions import is_between
from array_functions import utc2datetime
from array_functions import check_num_stations
from array_functions import stations_available_generator
from array_functions import baz_error
from array_functions import combined_residuals
from array_functions import slab_inversion
from array_functions import triggers_associator
from array_functions import trigger_list
from array_functions import interstation_distances
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
endtime = '2015-10-02'#'2015-10-02' , '2013-05-01', '2025-11-13'
min_stations = 10 # if you only want times with all stations, list the number of stations
remove_stations =  ['3A10', '3A15'] #['POM06', 'POM07', 'POM18'] #['3A10', '3A15'] # ['POM06', 'POM07', 'POM18']
keep_stations = []
array_name = '3A' #2A, 3A, POM, KD, HM, S1, UIL

#earthquakes----------
min_mag = '3.0'
max_rad = '400'
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

#Inputs for interface inversion---------
initial_guess = [
    249.0,   # strike, based on trench strike
    10.0,   # dip, based on subduction zone dip
    8.04,    # oceanic velocity
    6.2     # continental velocity
    ]

#Value bounds---------------------
bounds = ( #strike, dip, oceanic_vel, continental_vel
    [0,   0,   8.03, 4], #lower bounds, 5.8, 4
    [360, 90,  8.04, 8] #upper bounds
        )

weight_baz = 1
weight_slow = 0


###############################
#----------PROCESSING-----------
###############################

#Pull inventory-----------------------
#------------------------------------------------
if client == 'path':
    path = '/Users/cadequigley/Downloads/Research/deployment_array_design/'
    inv = read_inventory(path + array+'_d1_station.xml') #need to add something at some point about
else:
    client = Client(client)

    inv = client.get_stations(network=net, station=sta, channel=chan,
                                location=loc, starttime=UTCDateTime(starttime),
                                endtime=UTCDateTime(endtime), level='response') #level = 'channel'

(lat_list, lon_list, elev_list, station_d1_list,
 start_d1_list, end_d1_list, num_channels_d1_list) = data_from_inventory(inv, remove_stations, keep_stations)

check = check_num_stations(min_stations, station_d1_list)

data = {
        'station': station_d1_list,
        'lat': lat_list,
        'lon': lon_list,
        'elevation': elev_list}

station_info = pd.DataFrame(data) #for pulling info later


#Pull earthquakes-----------------------
#------------------------------------------------

#### Get center of array--------

output = get_geometry(lat_list, lon_list, elev_list, return_center = True)
origin_lat = str(output[-1][1])
origin_lon = str(output[-1][0])

#### Calculate interstation distances/moveout time
xpos = list(output[:,0])
xpos = xpos[:-1]
ypos = list(output[:,1])
ypos = ypos[:-1]
distances_temp = interstation_distances(xpos, ypos)
moveout = (np.max(distances_temp)/3)+0.5 #t = d/v + error

### Pull in earthquakes--------------
start = str(np.min(start_d1_list)) #time when first station online
if str(type(end_d1_list[0])) == "<class 'NoneType'>": #deals with case where station/array is still active by taking time today
    end_temp = UTCDateTime.now()
    end = str(end_temp)
    temp = []
    for i in range(len(end_d1_list)):
        temp.append(end_temp)
    end_d1_list = temp
else:
    end = str(np.max(end_d1_list)) #time when last station offline

#start = starttime
#end = endtime

df = pull_earthquakes(origin_lat, origin_lon, max_rad, start, end, min_mag, array_name, velocity_model)
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
        station_sub = station_info[station_info['station'].isin(stations)] #pull out specific station info
    
        sta_lats = station_sub['lat'].to_numpy()
        sta_lons = station_sub['lon'].to_numpy()
        stations = station_sub['station'].to_numpy()
        sta_elev = station_sub['elevation'].to_numpy()


        START = UTCDateTime(eq_time[event])+expected_parrival[event]-60
        END = START +120

        st = Stream()
        failed_stations = []

        for sta in stations:
            try:
                st += client.get_waveforms(net, sta, loc, chan, START, END)
            except FDSNNoDataException:
                print(f"No data for station {sta}")
                failed_stations.append(sta)
            except Exception as e:
                print(f"Error for station {sta}: {e}")
                failed_stations.append(sta)

        # Remove failed stations cleanly
        if failed_stations:
            mask = ~np.isin(stations, failed_stations)
            stations = stations[mask]
            sta_lats = sta_lats[mask]
            sta_lons = sta_lons[mask]
            sta_elev = sta_elev[mask]
        
        #Get data on either side of event-------------------
        
        ### Need to add a new "try" statement here for channels that go out
        #failed_stations = []
        #st = client.get_waveforms(net, stations[0], loc, chan, START, END) #attach_response=True
        #for i in range(len(stations)-1):
            #try:
               # st += client.get_waveforms(net, stations[i+1], loc, chan, START, END)
            #except ValueError as e:
                #print(f"Pulling data error from IRIS, skipping "+stations[i+1])
                #failed_stations.append(stations[i+1])
                #continue
        #if len(failed_stations) > 0: 
            #for k in range(len(failed_stations)):
                #station = failed_stations[k]
                #idx = stations.index(station)
                #del sta_lats[idx]
                #del sta_lons[idx]
                #del stations[idx]
                #del sta_elev[idx]
        #if len(st) < min_stations:

        if len(st) < min_stations:
            raise ValueError("Not enough traces")
            
        st.merge(fill_value='latest')
        st.trim(START, END, pad='true', fill_value=0)
        st.sort()
        st.remove_sensitivity(inventory = inv)

        # Filter the data
        st.filter("bandpass", freqmin=FREQ_MIN, freqmax=FREQ_MAX, corners=2, zerophase=True)
        st.taper(max_percentage=0.05)
        #print('Done pulling data')

        ###Finding triggers---------------------------------
        if timing == 'trigger': #use sta/lta triggers

           #Create list of triggers using sta/lta for each trace
            trigger_lists = []
            trigger_peaks = []
            trigger_lengths = []
            for s in range(len(st)):
                times, peaks, lengths = trigger_list(st[s])
                trigger_lists.append(times)
                trigger_peaks.append(peaks)
                trigger_lengths.append(lengths)


            # Associate triggers together based on expected moveout--------------------
            
            #moveout = 2 #seconds, need to rewrite as a function of max inter-array distance/upper crust velocity
            

            times, peaks, lengths = triggers_associator(trigger_lists, trigger_peaks, trigger_lengths, moveout, min_triggers)
            
            times = np.array(times)
            peaks = np.array(peaks)
            lengths = np.array(lengths)
            # Create mask to find triggers around expected p-arrival---------
            mask = np.abs(times - 60) <= ptolerance
            trigger_filtered = times[mask]
            peaks_filtered = peaks[mask]
            lengths_filtered = lengths[mask]
            
            if len(trigger_filtered) == 0:
                trigger = 60 
                trigger_type = 'Taup'
                peak = 0
                length = 0
                #Trim stream to allow for max mdccm
                START_new = START + trigger + window_start- 0.001 - ptolerance
                END_new = START_new + 2*ptolerance
                st = st.slice(START_new, END_new)
            elif len(trigger_filtered) >1:
                #trigger = np.median(trigger_filtered)
                ####CHOOSING TRIGGER WITH LARGER PEAK-------------------
                idx = np.argmax(peaks_filtered)
                trigger = trigger_filtered[idx]
                peak = peaks_filtered[idx]
                length = lengths_filtered[idx]
                trigger_type = 'Multiple STA/LTA triggers near arrival, picking largest peak'
                #Trim stream to window of interest-------------
                START_new = START + trigger + window_start- 0.001
                END_new = START_new + WINDOW_LENGTH
                st = st.slice(START_new, END_new)
                ####CHOOSING CLOSEST TO EXPECTED ARRIVAL-----------------
                #idx = np.argmin(np.abs(trigger_filtered - 60))
                #trigger = trigger_filtered[idx]
                #trigger_type = 'Multiple STA/LTA triggers near arrival, picking closest to estimated arrival'
            else:
                trigger = trigger_filtered[0]
                peak = peaks_filtered[0]
                length = lengths_filtered[0]
                trigger_type = 'STA/LTA trigger'
                #Trim stream to window of interest-------------
                START_new = START + trigger + window_start- 0.001
                END_new = START_new + WINDOW_LENGTH
                st = st.slice(START_new, END_new)

            print(trigger_type)
                

            
            #trigger, trigger_type = trigger_associator(st, 60) #60 comes from length of trace (above)
            #print(trigger_type)

            #Trim stream to window of interest-------------
            #START_new = START + trigger + window_start- 0.001
            #END_new = START_new + WINDOW_LENGTH
            #st = st.slice(START_new, END_new)

    
        st1 = st.copy() #creating copy for FK section
        ###Array processing---------------------------------
        ##Least squares--------------------
        if processing == 'lts' or processing == 'ls':
            if processing == 'lts':
                ALPHA = 0.5 #least trimmed squares
            else:
                ALPHA = 1 #least squares
            print('Starting LTS')
            lts_vel, lts_baz, t, mdccm, stdict, sigma_tau, conf_int_vel, conf_int_baz = lts_array.ltsva(st, sta_lats, sta_lons, WINDOW_LENGTH, WINDOW_OVERLAP, ALPHA)

            if len(lts_baz) >1: #pulling out max mdccm
                print('Pulling out max mdccm')
                idx = np.argmax(mdccm)
            else: #should only be one value for trigger time
                idx = 0
            data = {
                'array_baz': lts_baz[idx],
                'array_slow': 1/lts_vel[idx],
                'array_vel': lts_vel[idx],
                'mdccm': mdccm[idx],
                'conf_int_vel': conf_int_vel[idx],
                'conf_int_baz': conf_int_vel[idx],
                'time': str(UTCDateTime(mdates.num2date(t[idx]))),
                'event_id': event_ids[event],
                'baz_error': baz_error(eq_baz[event], lts_baz[idx]),
                'slow_error': eq_slow[event] - (1/lts_vel[idx]),
                'trigger_time': str(START+trigger),
                'trigger_type': trigger_type,
                'sta/lta': peak,
                'trigger_length': length, 
                'num_stations': len(st),
                'array_lat': origin_lat,
                'array_lon': origin_lon
                }
            array_data = pd.DataFrame(data, index=[0]) #print(array_data)
            #array_data_list.append(array_data)
        else: #fk analysis
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
                stime=START+1, etime=END-1 #had to add and subtract 2 to avoid timing errors
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

array_data_comb = pd.merge(array_data_comb1, df, on='event_id', how='inner')

array_data_comb.to_csv(array_name+'_400km_m3_test.csv')

###Finding best fit plane to data
print("Finding best plane")
baz = array_data_comb['backazimuth'].to_numpy()
takeoff = np.rad2deg(np.arctan(array_data_comb['distance'].to_numpy()/array_data_comb['depth'].to_numpy()))
baz_error = array_data_comb['baz_error'].to_numpy()
slow_error = array_data_comb['slow_error'].to_numpy()
#residuals = combined_residuals(initial_guess, baz, takeoff, baz_error, slow_error, weight_baz, weight_slow)
strike_fit, dip_fit, v_oceanic_fit, v_continental_fit = slab_inversion(initial_guess, bounds, baz, takeoff, baz_error, slow_error, weight_baz, weight_slow)
