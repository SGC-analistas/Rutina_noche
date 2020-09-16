"""
python 3.7.4
v2.0   Autor: Emmanuel Castillo | ecastillo@sgc.gov.co
          Se hiceron mejoras a la rutina funest_json2.py 
          Las mejoras consisten en : -optimización, -se implemento en modo OOP para generalizar en futuras rutinas
          Se creo la clase SGC_performance para : 
              -obtener un inventory con base a unas restricciones
              -obtener porcentajes a partir de un inventory
              -obtener un json para la rutina de la noche
"""
"""
V1.0   Autor: Ángel Agudelo | adagudelo@sgc.gov.co
"""

from obspy.core.stream import _headonly_warning_msg
from obspy.core.inventory import inventory
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import concurrent.futures
import numpy as np
import json
import warnings
import time
import os

class SGC_Performance(object):
    def __init__(self, ip_fdsn, port_fdsn, starttime,endtime):
        self.ip_fdsn = ip_fdsn
        self.port_fdsn = port_fdsn
        self.starttime = starttime
        self.endtime = endtime

    @property
    def sgc_client(self):
        return Client(self.ip_fdsn+":"+self.port_fdsn)

    def __on_inv(self, stations, locations, channel="*Z"):

        try:
            inv = self.sgc_client.get_stations(network="*",
                                station=stations,
                                location= locations,
                                channel = channel,
                                starttime=self.starttime,
                                endtime=self.endtime,
                                level="channel")
        except:
            print('\n \n')
            raise Exception(f"revisar: {stations}_{locations}_{channel}")
            
        return inv

    def _read_in(self, in_path):
        """
        parameters
        ----------
        in_file: str
            path of the in_file that contains information about on stations
                
        returns
        -------
        all_data: list
            List of four elements.
            Three first elements correspond to str for pass them to a client.get_Stations methods
            The last element correspond to network "RSNC,RNAC,SUB,DRL"

        """
        read_stations = open(in_path,"r").readlines()
        stations, locations, channels, networks = [], [], [], []
        for station in read_stations:
            station_parameters = station.strip().split(",")
            first_letter = station_parameters[0][0:1]
            if str(first_letter) != "#":
                sta, loc, cha, net = station_parameters
                stations.append(sta.strip())
                locations.append(loc.strip())
                channels.append(cha.strip())
                networks.append(net.strip())

        all_data = list(zip(stations, locations, channels, networks))

        return all_data

    def _inventories(self, in_dict):
        """
        parameters
        ----------
        in_dict: dictionary
            Each key and value of the dictionary corresponds 
            to the network of the routine and the respective in_file path.

        returns
        -------
        inv_dict: dict
            dict that contains the next inventories: 'RSNC', 'RNAC','DRL','SUB','INTER' 
        """
        inv_dict = {}
        for net,in_path in in_dict.items():
            all_data = self._read_in(in_path)

            sta_0, loc_0, cha_0, _ = all_data[0]
            inv_0 = self.__on_inv(sta_0, loc_0, cha_0)
            for data in all_data[1:]:
                stations, locations, channels, _ = data
                inv = self.__on_inv(stations, locations, channels)
                inv_0 = inv_0.__add__(inv.copy())
                
            inv_dict[net] = inv_0.copy()
            del inv_0

        return inv_dict

    def _get_availability_percentage(self, network, station, location, channel,
                                    starttime, endtime):

        #adapted method from sds client
        """
        Get percentage of available data.

        :type network: str
        :param network: Network code of requested data (e.g. "IU").
        :type station: str
        :param station: Station code of requested data (e.g. "ANMO").
        :type location: str
        :param location: Location code of requested data (e.g. "").
        :type channel: str
        :param channel: Channel code of requested data (e.g. "HHZ").
        :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param starttime: Start of requested time window.
        :type endtime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param endtime: End of requested time window.
        
        :rtype: 2-tuple (float, int)
        :returns: 2-tuple of percentage of available data (``0.0`` to ``1.0``)
            and number of gaps/overlaps.
        """
        if starttime >= endtime:
            msg = ("'endtime' must be after 'starttime'.")
            raise ValueError(msg)

        
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", _headonly_warning_msg, UserWarning,
                "obspy.core.stream")

            try:
                st = self.sgc_client.get_waveforms(network, station, location, channel,
                                        starttime, endtime)
                st_existence = True
            except:
                st_existence = False


        if st_existence == True:
            # even if the warning was silently caught and not shown it gets
            # registered in the __warningregistry__ and will not be shown
            # subsequently in a place were it's not caught
            # see https://bugs.python.org/issue4180
            # see e.g. http://blog.ionelmc.ro/2013/06/26/testing-python-warnings/
            try:
                from obspy.core.stream import __warningregistry__ as \
                    stream_warningregistry
            except ImportError:
                # import error means no warning has been issued from
                # obspy.core.stream before, so nothing to do.
                pass
            else:
                for key in list(stream_warningregistry.keys()):
                    if key[0] == _headonly_warning_msg:
                        stream_warningregistry.pop(key)
            st.sort(keys=['starttime', 'endtime'])
            st.traces = [tr for tr in st
                        if not (tr.stats.endtime < starttime or
                                tr.stats.starttime > endtime)]

            if not st:
                return (0, 1)

            total_duration = endtime - starttime
            # sum up gaps in the middle
            gaps = [gap[6] for gap in st.get_gaps()]
            gap_sum = np.sum(gaps)
            gap_count = len(gaps)
            # check if we have a gap at start or end
            earliest = min([tr.stats.starttime for tr in st])
            latest = max([tr.stats.endtime for tr in st])
            if earliest > starttime:
                gap_sum += earliest - starttime
                gap_count += 1
            if latest < endtime:
                gap_sum += endtime - latest
                gap_count += 1

            percentage = 100*( 1 - (gap_sum / total_duration))
            percentage = int(round(percentage))

        else:
            percentage = 0
            gap_count = 0


        return (percentage, gap_count)

    def _percentage_executor(self,parameters):
        network,station,location,channel = parameters.split('.')
        percentage = self._get_availability_percentage(network=network, 
                                        station=station, 
                                        location=location, 
                                        channel=channel,
                                        starttime=self.starttime,
                                        endtime=self.endtime)
        return percentage

    def _get_percentage_dict(self,inv_dict):
        """
        parameters
        ----------
        inv_dict: dict
        
        returns
        -------
        perc_dict : dict
            dictionary of dictionaries where de deep dictionary contains the percentage
        """
        perc_dict={}
        keys = list(inv_dict.keys())

        inv_towork = inv_dict[keys[0]].copy()
        for i in range(1,len(keys)):
            inv_towork +=  inv_towork.__add__(inv_dict[keys[i]])

        contents = inv_towork.get_contents()['channels']
        contents = list(dict.fromkeys(contents))

        # tic = time.time()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            percentages = executor.map(self._percentage_executor,contents )
            perc_dict = dict(zip(contents,percentages))
        # toc = time.time()
        # print("{0:>15}".format(f'json delay: {toc-tic:.2f}s'))

        # # HACERLO POR ESTACIONES
        # perc_dict={}
        # for key in inv_dict.keys():

            # contents = inv_dict[key].get_contents()['channels']
            # tic = time.time()
            # with concurrent.futures.ProcessPoolExecutor() as executor:
                # percentages = executor.map(self._percentage_executor,contents )
                # contents_dict = dict(zip(contents,percentages))
            # perc_dict[key] = contents_dict

            # toc = time.time()
            # print('\t\t',  "{0:>15}".format(key+': OK'),'\t\t',
                # "{0:>15}".format(f'# stations: {len(contents)}'),'\t\t',
                # "{0:>15}".format(f'delay: {toc-tic:.2f}s'))

        return perc_dict

    def get_percentage_dict(self,inv_dict):
        """
        parameters
        ----------
        inv_dict: dict
                
        returns
        -------
        perc_dict : dict
            dictionary of dictionaries where de deep dictionary contains the percentage
        """
        return self._get_percentage_dict(inv_dict)

    def _create_json(self, in_dict):
        """
        parameters
        ----------
        in_dict: dictionary
            Each key and value of the dictionary corresponds 
            to the network of the routine and the respective in_file path.
        returns
        -------
        jsonlist: list
            list of dictionaries that contains information about the stations 
            in the network of the in_dict 
        """
        inv_dict = self._inventories(in_dict)
        perc_dict = self._get_percentage_dict(inv_dict)
        
        jsonlist= []
        SGC = {}
        for key in inv_dict.keys():
            for network in inv_dict[key]:
                for station in network:
                    for channel in station:
                        content = '.'.join((network.code,station.code,\
                                            channel.location_code,\
                                            channel.code))

                        SGC["administrador"] = key
                        SGC["net"] = network.code
                        SGC["localizacion"] = channel.location_code
                        SGC["estacion"] = station.code
                        SGC["longitud"] = station.longitude
                        SGC["latitud"] = station.latitude
                        # SGC["valor"], SGC["#Gaps"] = perc_dict[key][content] #POR ESTACION
                        SGC["valor"], SGC["#Gaps"] = perc_dict[content]

                        jsonlist.append(SGC.copy())
        return jsonlist

    def create_json(self, filepath, in_dict):
        """
        parameters
        ----------
        filepath: str
            name of the json file
        in_dict: dictionary
            Each key and value of the dictionary corresponds 
            to the network of the routine and the respective in_file path.

        returns
        -------
        creates a json file with name entered in filepath variable
        """
        json2 = self._create_json(in_dict)
        with open(filepath,"w") as jsonfile:
            json.dump(json2, jsonfile)

if __name__ == "__main__":
    ip_fdsn = "http://10.100.100.232"
    port_fdsn = "8091"
    starttime = UTCDateTime(2020,9,15,0,0,0)
    endtime = UTCDateTime(2020,9,16,0,0,0)
    filename = 'prove.json'
    repository = os.path.dirname(os.path.abspath(__file__))
    PATH = os.path.join(repository,'noche_store')
    in_dict = {'DRL':os.path.join(PATH,'on_stations/est_DRL.in'),
                'RSNC':os.path.join(PATH,'on_stations/est_RSNC.in'),
                'RNAC':os.path.join(PATH,'on_stations/est_RNAC.in'),
                'INTER':os.path.join(PATH,'on_stations/est_INTER.in'),
                'SUB':os.path.join(PATH,'on_stations/est_SUB.in')}
    sgc_perf = SGC_Performance(ip_fdsn, port_fdsn, starttime,endtime)
    # inventories = sgc_perf._inventories(in_dict)
    # read_in = sgc_perf._read_in(os.path.join(PATH,'on_stations/est_RSNC.in'))
    # print(inventories)
    sgc_perf.create_json(filename,in_dict)
    # sgc_perf._get_percentage_dict(inv_dict)
