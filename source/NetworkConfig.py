
from .LoadMethods import MethodLoader

from dataclasses import dataclass

from source.utils import dbm2lin

import numpy as np

@dataclass
class NetworkConfig:

    num_terminals: int
    num_stations: int

    terminal_height: float
    station_height: float

    terminal_max_power: float
    station_max_power:  float

    carrier_frequency: float

    noise_variance: float


    @classmethod
    def read(cls, parameters) -> "NetworkConfig":

        return cls(
            num_terminals = parameters["num_terminals"],
            num_stations = parameters["num_stations"],

            terminal_height = parameters["terminals_height"],
            station_height = parameters["stations_height"],

            terminal_max_power = parameters["terminals_max_power"],
            station_max_power = parameters["stations_max_power"],

            carrier_frequency = parameters["carrier_frequency"],

            noise_variance = dbm2lin(parameters["noise_density"]) * parameters["bandwidth"]
        )


@dataclass
class FixedServiceConfig(NetworkConfig):

    methods: dict

    @classmethod
    def read(cls, parameters) -> "FixedServiceConfig":

        methods = MethodLoader.load_named(parameters, 
                    ["lsf_model", "channel_model",
                     "terminal_antenna_gain", "station_antenna_gain"
                    ])

        return cls(

            num_terminals = parameters["num_terminals"],
            num_stations = parameters["num_stations"],

            terminal_height = parameters["terminals_height"],
            station_height = parameters["stations_height"],

            terminal_max_power = parameters["terminals_max_power"],
            station_max_power = parameters["stations_max_power"],

            carrier_frequency = parameters["carrier_frequency"],

            noise_variance = dbm2lin(parameters["noise_density"]) * parameters["bandwidth"],

            methods = methods
        )


@dataclass
class DMimoConfig(NetworkConfig):

    num_panels: int
    num_arrays: int

    panel_N_h: int
    panel_N_v: int

    array_N_h: int
    array_N_v: int

    station_downtilt: float

    num_pilot_sequences: int

    methods: dict

    @classmethod
    def read(cls, parameters) -> "DMimoConfig":


        methods = MethodLoader.load_named(parameters, 
                    ["lsf_model", "channel_model", "correlation_model", "channel_estimation",
                     "terminal_antenna_gain", "station_antenna_gain",
                     "terminal_deployment", "station_deployment",
                     "terminal_sectorization", "station_sectorization",
                     "stations_combining", "stations_beamforming"
                    ])

                    

        return cls(
            num_terminals = parameters["num_terminals"],
            num_stations = parameters["num_stations"],

            terminal_height = parameters["terminals_height"],
            station_height = parameters["stations_height"],

            terminal_max_power = parameters["terminals_max_power"],
            station_max_power = parameters["stations_max_power"],

            carrier_frequency = parameters["carrier_frequency"],

            noise_variance = dbm2lin(parameters["noise_density"]) * parameters["bandwidth"],

            num_panels = parameters['num_panels'],
            num_arrays = parameters['num_arrays'],

            panel_N_h = parameters['panel_N_h'],
            panel_N_v = parameters['panel_N_v'],

            array_N_h = parameters['array_N_h'],
            array_N_v = parameters['array_N_v'],

            station_downtilt = parameters['station_downtilt'],

            num_pilot_sequences = parameters['num_pilot_sequences'],

            methods = methods 
        
        )


@dataclass
class FixedServiceGeometryForManySnapshots:

    terminals_coords: np.ndarray
    stations_coords:  np.ndarray

    terminals_boresights: np.ndarray
    stations_boresights:  np.ndarray

    @classmethod
    def get_from_tuple(cls, tuple):

        return cls(*tuple)

@dataclass
class DMimoGeometryForManySnapshots:

    terminals_coords: np.ndarray
    stations_coords:  np.ndarray

    terminals_boresights: np.ndarray
    stations_boresights:  np.ndarray

    lsf_coeffs: np.ndarray

    H_coeffs:   np.ndarray

    @classmethod
    def get_from_tuple(cls, tuple):

        return cls(*tuple)


