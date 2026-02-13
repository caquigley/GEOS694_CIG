
import sys
import numpy as np
import matplotlib.pyplot as plt

# def read_guage_file(fid):
#     """
#     Read USGS Guage data and convert date and time to minutes since start

#     parameters
#     fid (str): path to data

#     returns
#     timestamp (list): time in minutes since the start of the month
#     hgt (np.array): guage height in ft
#     """
#     date, time, hgt = np.loadtxt(fid, skiprows=28, usecols=[2,3,5], 
#                                     dtype=str).T

#     hgt = hgt.astype(float)
#     days = [float(d[-2:]) for d in date]  # get DD from YYYY-MM-DD
#     hours = [float(t.split(":")[0]) for t in time]  # get HH from HH:MM
#     mins = [float(t.split(":")[1]) for t in time]  # get MM from HH:MM

#     timestamps = []
#     for d, h, m in zip(days, hours, mins):
#         timestamp = (d * 24 * 60) + (h * 60) + m
#         timestamps.append(timestamp)

#     return timestamps, hgt


# def plot(timestamp, hgt):

#     fig, ax = plt.subplots()
#     ax.plot(timestamp, hgt, color = 'firebrick')
#     ax.grid(alpha = 0.3)
#     ax.set_xlabel('time')
#     ax.set_ylabel('guage height (ft)')
#     plt.show()


# if __name__ == '__main__':
#     if len(sys.argv) == 2:
#         timestamp, hgt = read_guage_file(sys.argv[1])
#         plot(timestamp,hgt)
#         #print(hgt)


class StreamGuage:
    time = []
    data = []
    units = 'ft'

    def __init__(self, fid, station_id, station_name, starttime):
        self.fid = fid
        self.station_id = station_id
        self.station_name = station_name
        self.starttime = starttime


    def read_guage_file(self):
        """
        Read USGS Guage data and convert date and time to minutes since start

        parameters
        fid (str): path to data

        returns
        timestamp (list): time in minutes since the start of the month
        hgt (np.array): guage height in ft
        """
        date, time, hgt = np.loadtxt(self.fid, skiprows=28, usecols=[2,3,5], 
                                        dtype=str).T

        hgt = hgt.astype(float)
        days = [float(d[-2:]) for d in date]  # get DD from YYYY-MM-DD
        hours = [float(t.split(":")[0]) for t in time]  # get HH from HH:MM
        mins = [float(t.split(":")[1]) for t in time]  # get MM from HH:MM

        timestamps = []
        for d, h, m in zip(days, hours, mins):
            timestamp = (d * 24 * 60) + (h * 60) + m
            timestamps.append(timestamp)

        self.time = timestamps
        self.data = hgt


    def plot(self):

        fig, ax = plt.subplots()
        ax.plot(self.time, self.data, color = 'firebrick')
        ax.grid(alpha = 0.3)
        ax.set_xlabel('time')
        ax.set_ylabel('guage height ('+self.units+')')
        ax.set_title(str(self.station_id)+' '+str(self.station_name)+' '
                     +str(self.starttime)+' '
                     +str(np.max(self.data))+' '+self.units)
        plt.show()


    def convert(self):
        #breakpoint()
        self.data = 0.3048*self.data #converts from feet to meters
        self.units = 'meters'
        

    def demean(self):
        self.data = self.data - np.mean(self.data)

    def shift_time(self, minutes):
        shifts = []
        for i in range(len(self.time)):
            shifts.append(self.time[i]+minutes)
            
        self.time = shifts

    def main(self):
         
        self.read_guage_file()   
        self.plot()   

        self.convert()   
        self.demean()   
        self.shift_time(-100)
        self.plot() 

class NOAAStreamGuage(StreamGuage):

    def __init__(self, fid, station_id, station_name, starttime):
        super().__init__(fid, station_id, station_name, starttime)

    units = 'meters'

    def convert(self):
        print('NOAA Stream Gauge so already in meters')

    def read_guage_file(self):
        super().read_guage_file()
        print('I am a NOAA stream guage')
    


if __name__ == "__main__":
    NOAAStreamGuage("/Users/cadequigley/Downloads/phelan_creek_stream_guage_2024-10-07_to_2024-10-14.txt",
                "15478040", "PHELAN CREEK", "2024-10-07 00:00").main()
     

#if __name__ == "__main__":
    #sg = StreamGuage("/Users/cadequigley/Downloads/phelan_creek_stream_guage_2024-09-07_to_2024-09-14.txt",
                      #"15478040", "PHELAN CREEK", "2024-09-07 00:00")  
    #sg.read_guage_file()   
    #sg.plot()   

    #sg.convert()   
    #sg.demean()   
    #sg.shift_time(-100)
    #sg.plot()   

