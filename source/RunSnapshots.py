from importlib.resources import path

import numpy as np

from source.geometry.angles import compute_multiple_doas, compute_multiple_relative_doas, compute_multiple_relative_doas_for_queue

import multiprocessing as mp

import os

mp.set_start_method('fork')

from pathlib import Path

dir_path = str(Path(__file__).resolve().parent.parent)






def empty_object_array(n):
    return np.empty(n, dtype=np.ndarray)

def group_slice_bounds(i, num_groups, division, total):
    """Bounds of the i-th chunk when splitting `total` items into `num_groups` groups."""
    idx_b = i * division
    idx_e = (i + 1) * division if i < num_groups - 1 else total
    return idx_b, idx_e


def save_npz(path, filename, **arrays):
    np.savez(path + filename, **arrays)



class RunFixedServiceSnapshots:


    
            
    def __init__(self, config):
        self.config = config

    
    def run(self, num_snapshots: int, rng: np.random.Generator):

        num_receivers    = self.config.num_terminals
        num_transmitters = self.config.num_stations
        receiver_height    = self.config.terminal_height
        transmitter_height = self.config.station_height

        # The FS receiver position is equal for every single snapshot
        receivers_coords = np.empty(num_receivers, dtype=object)
        receivers_coords[0] = (0, 0, receiver_height)

        #print("receivers")
        #print(receivers_coords)

        # The FS transmitter position is equal for every single snapshot
        transmitters_coords = np.empty(num_transmitters, dtype=object)
        transmitters_coords[0] = (10e3, 0, transmitter_height)

        from source.geometry.angles import compute_multiple_doas, compute_multiple_relative_doas

        # Directions of arrival
        (receivers_doas_h, receivers_doas_v), (transmitters_doas_h, transmitters_doas_v) = compute_multiple_doas(receivers_coords, transmitters_coords)

        # Considering that receiver and transmitters are perfectly aligned
        receivers_boresights = (receivers_doas_h, receivers_doas_v)
        transmitters_boresights = (transmitters_doas_h, transmitters_doas_v)

        # Since the positions are the same, the large scale fading is also the same for all snapshots

        # Large scale fading coefficients
        lsf_coeffs, K_coeffs = self.config.methods["lsf_model"].compute(
            receivers_coords, transmitters_coords, receiver_height, transmitter_height, 
            self.config.carrier_frequency, rng, 'Sim'
            )

        receivers_coords_for_all_snapshots    = np.zeros(num_snapshots, dtype=np.ndarray)
        transmitters_coords_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        receivers_boresights_for_all_snapshots    = np.zeros(num_snapshots, dtype=np.ndarray)
        transmitters_boresights_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        for ite in range(num_snapshots):

            #print('Fixed Service snapshot ' + str(ite))
            receivers_coords_for_all_snapshots[ite]    = receivers_coords
            transmitters_coords_for_all_snapshots[ite] = transmitters_coords 

            receivers_boresights_for_all_snapshots[ite]    = receivers_boresights
            transmitters_boresights_for_all_snapshots[ite] = transmitters_boresights



        return (
            receivers_coords_for_all_snapshots, transmitters_coords_for_all_snapshots,

            receivers_boresights_for_all_snapshots, transmitters_boresights_for_all_snapshots

        )
            


# from dataclasses import dataclass

# @dataclass
# class ParalelismContext:



class RunDMimoSnapshots:

    def __init__(self, config):
        self.config = config


    def _start(self, func, arguments):
            queue = mp.Queue()
            args = (queue, *arguments)
            process = mp.Process(target=func, args=args)
            process.start()
            return process, queue

   
        
    
    def generate_coordinates(self, num_snapshots: int, rng: np.random.Generator):

        """
        This function generates the coordinates of the UEs and APs for a given number of snapshots. 
        
        The APs positions are equal for every single snapshot, while the UEs positions are generated randomly for each snapshot.
        
        """

        print("DMimo: generating coordinates")

        # OBS: remember that for the network configuration the UEs are "terminals" and the APs are "stations"

        # Coordinates storage for all snapshots
        ues_coords_for_all_snapshots     = np.empty(num_snapshots, dtype=np.ndarray)
        aps_coords_for_all_snapshots     = np.empty(num_snapshots, dtype=np.ndarray)


        # 1. The APs are fixed
        aps_fixed_coords = self.config.methods["station_deployment"].deploy(
            self.config.station_height, self.config.num_stations, rng
        )

        for ite in range(num_snapshots):
        
            aps_coords_for_all_snapshots[ite] = aps_fixed_coords
        
            # 1. Generating UEs coordinates
            ues_coords = self.config.methods["terminal_deployment"].deploy(
                aps_fixed_coords, self.config.terminal_height, self.config.num_terminals, rng
            )
            ues_coords_for_all_snapshots[ite] = ues_coords

        return (ues_coords_for_all_snapshots, aps_coords_for_all_snapshots)


    def define_boresights_of_panels_and_arrays(self, num_snapshots: int, rng: object):

        print("DMimo: defining boresights")

        ues_boresights_for_all_snapshots = np.empty(num_snapshots, dtype=np.ndarray)
        aps_boresights_for_all_snapshots = np.empty(num_snapshots, dtype=np.ndarray)
        

        for ite in range(num_snapshots):
            # 1. Generating UEs panels boresights
            ues_boresights = self.config.methods["terminal_sectorization"].compute(
                self.config.num_terminals, self.config.num_panels, rng
            )
            ues_boresights_for_all_snapshots[ite] = ues_boresights

            # 1. Generating APs panels boresights
            aps_boresights = self.config.methods["station_sectorization"].compute(
                self.config.num_stations, self.config.num_arrays, self.config.station_downtilt
            )
            aps_boresights_for_all_snapshots[ite] = aps_boresights


        return (ues_boresights_for_all_snapshots, aps_boresights_for_all_snapshots)



    def compute_relative_directions_of_arrival(self, 
                     ues_coords_for_all_snapshots, aps_coords_for_all_snapshots, 
                     ues_boresights_for_all_snapshots, aps_boresights_for_all_snapshots,
                     num_snapshots: int):

        print("DMimo: computing relative directions of arrival")

        # Storage of the DoAs from the UEs POV 
        ues_r_doas_for_all_snapshots = np.zeros(num_snapshots, dtype=tuple)

        # Storage of the DoAs from the APs POV
        aps_r_doas_for_all_snapshots = np.zeros(num_snapshots, dtype=tuple)

        tensor_shape = (
            self.config.num_terminals, 
            self.config.num_stations, 
            self.config.num_panels, 
            self.config.num_arrays
        )


        for ite in range(num_snapshots):

            # Total number of CPU cores
            num_cores = os.cpu_count()
            # Number of available cores (excluding the main one and one for the OS)
            num_aps_groups = num_cores - 2
            aps_division = self.config.num_stations // num_aps_groups
            
            
            # Storage of the DoAs from the UEs POV 
            ues_r_h_doas = np.zeros(tensor_shape, dtype=float)
            ues_r_v_doas = np.zeros(tensor_shape, dtype=float)
    
            # Storage of the DoAs from the APs POV
            aps_r_h_doas = np.zeros(tensor_shape, dtype=float)
            aps_r_h_doas = aps_r_h_doas.transpose(1, 0, 3, 2)
            aps_r_v_doas = np.zeros(tensor_shape, dtype=float)
            aps_r_v_doas = aps_r_v_doas.transpose(1, 0, 3, 2)
            
            processes = []
            queues    = []

            # Computing the DoAs from the POV of the UEs

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                args = (
                    ues_coords_for_all_snapshots[ite], 
                    aps_coords_for_all_snapshots[ite][idx_b:idx_e], 
                    *ues_boresights_for_all_snapshots[ite], 
                    self.config.num_panels, 
                    self.config.num_arrays
                    )

                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)

                processes.append(P)
                queues.append(Q)



            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                (
                ues_r_h_doas[:, idx_b:idx_e], 
                ues_r_v_doas[:, idx_b:idx_e]) = queues[i].get()


            for P in processes:
                P.join()

            ues_r_doas_for_all_snapshots[ite] = (ues_r_h_doas, ues_r_v_doas)


            # Computing the DoAs from the POV of the APs
            processes = []
            queues    = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                args = (
                    aps_coords_for_all_snapshots[ite][idx_b:idx_e], 
                    ues_coords_for_all_snapshots[ite], 
                    *aps_boresights_for_all_snapshots[ite], 
                    self.config.num_arrays, 
                    self.config.num_panels
                    )
        
                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)
                
                processes.append(P)
                queues.append(Q)
    
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                h_doas, v_doas = queues[i].get()
                
                aps_r_h_doas[idx_b:idx_e] = h_doas
                aps_r_v_doas[idx_b:idx_e] = v_doas

            for P in processes:
                P.join()

            aps_r_doas_for_all_snapshots[ite] = (aps_r_h_doas, aps_r_v_doas)
                

        return (ues_r_doas_for_all_snapshots, aps_r_doas_for_all_snapshots)
        
        

    def compute_antennas_gains(self, 
                        ues_r_doas_for_all_snapshots, 
                        aps_r_doas_for_all_snapshots,
                        num_snapshots: int
                        ):

        print("DMimo: computing antennas gains")

        # Total number of CPU cores
        num_cores = os.cpu_count()
        # Number of available cores (excluding the main one and one for the OS)
        num_aps_groups = num_cores - 2
        aps_division = self.config.num_stations // num_aps_groups
                    
        
        # Storage of the antennas gains from the UEs POV 
        ues_gains_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        # Storage of the antennas gains from the APs POV
        aps_gains_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        tensor_shape = (
            self.config.num_terminals, 
            self.config.num_stations, 
            self.config.num_panels, 
            self.config.num_arrays
        )

        print("tensor shape: ", tensor_shape)

        for ite in range(num_snapshots):

            ues_gains = np.zeros(tensor_shape, dtype=float)

            aps_gains = np.zeros(tensor_shape, dtype=float)
            aps_gains = aps_gains.transpose(1, 0, 3, 2)
                                
            processes = []
            queues    = []

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                args = (
                    ues_r_doas_for_all_snapshots[ite][0][:, idx_b:idx_e], 
                    ues_r_doas_for_all_snapshots[ite][1][:, idx_b:idx_e]
                    )

                P, Q = self._start(self.config.methods["terminal_antenna_gain"].compute_for_queue, args)
                processes.append(P)
                queues.append(Q)
        
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                ues_gains[:, idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()


            ues_gains_for_all_snapshots[ite] = ues_gains
            
            processes = []
            queues    = []

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                args = (
                    aps_r_doas_for_all_snapshots[ite][0][idx_b:idx_e], 
                    aps_r_doas_for_all_snapshots[ite][1][idx_b:idx_e]
                    )
                
                P, Q = self._start(self.config.methods["station_antenna_gain"].compute_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations
                aps_gains[idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()

            aps_gains_for_all_snapshots[ite] = aps_gains

        return (
            ues_gains_for_all_snapshots,
            aps_gains_for_all_snapshots
        )

    def compute_spatial_correlation_matrices(self, 
                                             ues_r_doas_for_all_snapshots: np.ndarray,
                                             aps_r_doas_for_all_snapshots: np.ndarray,
                                             num_snapshots: int):

        print("DMimo: computing spatial correlation matrices")

        # Total number of CPU cores
        num_cores = os.cpu_count()
        # Number of available cores (excluding the main one and one for the OS)
        num_aps_groups = num_cores - 2
        aps_division = self.config.num_stations // num_aps_groups
                            
        # Storage of the antennas gains from the UEs POV 
        ues_R_matrices_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        # Storage of the antennas gains from the APs POV
        aps_R_matrices_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        tensor_shape = (
            self.config.num_terminals, 
            self.config.num_stations, 
            self.config.num_panels, 
            self.config.num_arrays
        )

        pan_N_h = self.config.panel_N_h
        pan_N_v = self.config.panel_N_v
        pan_N_tot = pan_N_h * pan_N_v

        arr_N_h = self.config.array_N_h
        arr_N_v = self.config.array_N_v
        arr_N_tot = arr_N_h * arr_N_v

        
        for ite in range(num_snapshots):

            ues_R_matrices = np.zeros((*tensor_shape, pan_N_tot, pan_N_tot), dtype=np.complex128)

            aps_R_matrices = np.zeros((*tensor_shape, arr_N_tot, arr_N_tot), dtype=np.complex128)
            aps_R_matrices = aps_R_matrices.transpose(1, 0, 3, 2, 4, 5)
                                
            processes = []
            queues    = []


            # Computing the correlation matrices from the POV of the UEs
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                args = (
                    ues_r_doas_for_all_snapshots[ite][0][:, idx_b:idx_e], 
                    ues_r_doas_for_all_snapshots[ite][1][:, idx_b:idx_e],
                    pan_N_h, pan_N_v
                    )

                P, Q = self._start(self.config.methods["correlation_model"].compute_fast_integrals_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations
                ues_R_matrices[:, idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()

            ues_R_matrices_for_all_snapshots[ite] = ues_R_matrices


            processes = []
            queues    = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations

                args = (
                    aps_r_doas_for_all_snapshots[ite][0][idx_b:idx_e], 
                    aps_r_doas_for_all_snapshots[ite][1][idx_b:idx_e],
                    arr_N_h, arr_N_v
                    )

                P, Q = self._start(self.config.methods["correlation_model"].compute_fast_integrals_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else self.config.num_stations
                aps_R_matrices[idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()

            aps_R_matrices_for_all_snapshots[ite] = aps_R_matrices
        

        return (
            ues_R_matrices_for_all_snapshots, 
            aps_R_matrices_for_all_snapshots
        )


    def compute_large_scale_fading_coefficients(self, 
                                                ues_coords_for_all_snapshots, 
                                                aps_coords_for_all_snapshots, 
                                                num_snapshots: int,
                                                rng: object):

        print("DMimo: computing large scale fading coefficients")

        ls_fading_coeffs_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)
        K_coeffs_for_all_snapshots   = np.zeros(num_snapshots, dtype=np.ndarray)

        for ite in range(num_snapshots):

            ls_fading_coeffs, K_coeffs = self.config.methods["lsf_model"].compute(
                ues_coords_for_all_snapshots[ite], aps_coords_for_all_snapshots[ite], 
                self.config.terminal_height, self.config.station_height, 
                self.config.carrier_frequency, rng, None
            )

            ls_fading_coeffs_for_all_snapshots[ite] = ls_fading_coeffs
            K_coeffs_for_all_snapshots[ite]   = K_coeffs

        return (
            ls_fading_coeffs_for_all_snapshots, 
            K_coeffs_for_all_snapshots
            )

    def compute_large_scale_gain_coefficients(self,
                                              ls_fading_coeffs_for_all_snapshots,
                                              ues_gains_for_all_snapshots,
                                              aps_gains_for_all_snapshots,
                                              num_snapshots: int):

        print("DMimo: computing large scale gain coefficients")

        ls_gain_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        for ite in range(num_snapshots):

            ls_gain_coeffs = (
                ls_fading_coeffs_for_all_snapshots[ite][..., :, None, None] *  
                ues_gains_for_all_snapshots[ite] *
                aps_gains_for_all_snapshots[ite].transpose(1,0,3,2)
                )

            ls_gain_for_all_snapshots[ite] = ls_gain_coeffs

        return ls_gain_for_all_snapshots


    def generate_channel_coefficients(self, 
                                      ls_gain_coeffs, K_coeffs, 
                                      rx_R_matrices, tx_R_matrices, 
                                      rx_aoas, tx_aoas, 
                                      rx_N, tx_N, 
                                      num_snapshots: int,
                                      rng):

        print("DMimo: generating channel coefficients")

        H_coeffs_for_all_snapshots = np.zeros(num_snapshots, dtype=np.ndarray)

        for ite in range(num_snapshots):

            H_coeffs = self.config.methods["channel_model"].generate_multiple_channels(
                ls_gain_coeffs[ite], K_coeffs[ite], 
                rx_R_matrices[ite], tx_R_matrices[ite], 
                rx_aoas[ite], tx_aoas[ite], 
                rx_N, tx_N, 
                rng
            )

            H_coeffs_for_all_snapshots[ite] = H_coeffs

        return H_coeffs_for_all_snapshots
        


    def run(self, num_snapshots: int, rng: np.random.Generator):


        num_ues = self.config.num_terminals
        num_aps = self.config.num_stations
        num_panels = self.config.num_panels
        num_arrays = self.config.num_arrays
        ue_height = self.config.terminal_height
        ap_height = self.config.station_height

        panel_N_h = self.config.panel_N_h
        panel_N_v = self.config.panel_N_v
        array_N_h = self.config.array_N_h
        array_N_v = self.config.array_N_v
        


        # 1. Generating the coordinates for all snapshots
        (
        ues_coords_for_all_snapshots, 
        aps_coords_for_all_snapshots) = self.generate_coordinates(num_snapshots, rng)

        # 2. Defining the boresights of the panels and arrays for all snapshots
        (
        ues_boresights_for_all_snapshots,
        aps_boresights_for_all_snapshots) = self.define_boresights_of_panels_and_arrays(num_snapshots, rng)

        # 3. Computing the relative directions of arrival for all snapshots
        (
        ues_r_doas_for_all_snapshots,
        aps_r_doas_for_all_snapshots) = self.compute_relative_directions_of_arrival(
            ues_coords_for_all_snapshots, aps_coords_for_all_snapshots,
            ues_boresights_for_all_snapshots, aps_boresights_for_all_snapshots,
            num_snapshots
        )

        # 4. Computing the antenna gains for all snapshots
        (
        ues_gains_for_all_snapshots,
        aps_gains_for_all_snapshots) = self.compute_antennas_gains(
            ues_r_doas_for_all_snapshots, aps_r_doas_for_all_snapshots,
            num_snapshots
        )

        # 5. Computing the spatial correlation matrices for all snapshots
        (
        ues_R_matrices_for_all_snapshots,
        aps_R_matrices_for_all_snapshots) = self.compute_spatial_correlation_matrices(
            ues_r_doas_for_all_snapshots, aps_r_doas_for_all_snapshots,
            num_snapshots
        )

        print(aps_R_matrices_for_all_snapshots)

        # 6. Computing the large scale fading coefficients for all snapshots
        (
        ls_fading_coeffs_for_all_snapshots,
        K_coeffs_for_all_snapshots) = self.compute_large_scale_fading_coefficients(
            ues_coords_for_all_snapshots, aps_coords_for_all_snapshots,
            num_snapshots, rng
        )

        # 7. Computing the large scale gain coefficients for all snapshots
        ls_gain_coeffs_for_all_snapshots = self.compute_large_scale_gain_coefficients(
            ls_fading_coeffs_for_all_snapshots,
            ues_gains_for_all_snapshots,
            aps_gains_for_all_snapshots,
            num_snapshots
        )

        # 8. Generating the channel coefficients for all snapshots
        H_coeffs_for_all_snapshots = self.generate_channel_coefficients(
            ls_gain_coeffs_for_all_snapshots, K_coeffs_for_all_snapshots,
            ues_R_matrices_for_all_snapshots, aps_R_matrices_for_all_snapshots,
            ues_r_doas_for_all_snapshots, aps_r_doas_for_all_snapshots,
            (panel_N_h, panel_N_v), (array_N_h, array_N_v),
            num_snapshots, rng
        )

        
        basic_path = dir_path + '/scenarios_storage/DMimo/'
        

        np.savez(basic_path + 'lsg_parameters/lsg_coeffs_full.npz', lsg_coeffs = ls_gain_coeffs_for_all_snapshots)
        np.savez(basic_path + 'lsg_parameters/K_coeffs_full.npz',   K_coeffs   = K_coeffs_for_all_snapshots)

        np.savez(basic_path + 'R_matrices/ues_R_matrices_full.npz', ues_R_matrices = ues_R_matrices_for_all_snapshots)
        np.savez(basic_path + 'R_matrices/aps_R_matrices_full.npz', aps_R_matrices = aps_R_matrices_for_all_snapshots)

        np.savez(basic_path + 'H_coeffs/H_coeffs_full.npz', H_coeffs = H_coeffs_for_all_snapshots)


        return (ues_coords_for_all_snapshots, 
                aps_coords_for_all_snapshots,
                
                ues_boresights_for_all_snapshots, aps_boresights_for_all_snapshots,

                ls_gain_coeffs_for_all_snapshots,

                H_coeffs_for_all_snapshots
                )            




from collections import namedtuple
 
# Holds the outputs of a single link's LSF + antenna-gain computation, so callers
# don't have to juggle 5 positional values.
LinkLSF = namedtuple('LinkLSF', ['ls_fading', 'K', 'gain_a_to_b', 'gain_b_to_a', 'ls_gain'])



class InterNetworkLinksBuilder:

    def __init__(self, pn_geometry, sn_geometry, pn_config, sn_config, num_snapshots):
        self.pn_geom = pn_geometry
        self.sn_geom = sn_geometry     
        self.pn_conf = pn_config       
        self.sn_conf = sn_config

        self.num_snapshots = num_snapshots



    def _start(self, func, arguments):
        queue = mp.Queue()
        args = (queue, *arguments)
        process = mp.Process(target=func, args=args)
        process.start()
        return process, queue

    def _parallel_relative_doas(self, coords_a, coords_b, boresights_a, boresights_b, 
                                num_panels_a, num_panels_b, split_side):

        """
        Relative DoAs from `a` to `b`, computed in parallel by splitting the SN
        stations (always the "AP" side of the link) across several processes.
 
        split_side='b' -> the SN stations are `coords_b` (sliced on axis 1 of the result)
        split_side='a' -> the SN stations are `coords_a` (sliced on axis 0 of the result)
 
        NOTE: `boresights_a` is always passed whole (never sliced), matching the
        original implementation's behaviour even in the split_side='a' case.
        """


        num_a = len(coords_a)
        num_b = len(coords_b)

        num_groups = os.cpu_count() - 2
        num_sn_stations = self.sn_conf.num_stations
        division = num_sn_stations // num_groups

        doas_h = np.zeros((num_a, num_b, num_panels_a, num_panels_b), dtype=float)
        doas_v = np.zeros((num_a, num_b, num_panels_a, num_panels_b), dtype=float)

        processes, queues = [], []

        for i in range(num_groups):

            idx_b, idx_e = group_slice_bounds(i, num_groups, division, num_sn_stations)
            if split_side == 'b':
                args = (coords_a, coords_b[idx_b:idx_e], *boresights_a, num_panels_a, num_panels_b)

            else:
                args = (coords_a[idx_b:idx_e], coords_b, *boresights_a, num_panels_a, num_panels_b)

            process, queue = self._start(compute_multiple_relative_doas_for_queue, args)
            processes.append(process)
            queues.append(queue)

        for i in range(num_groups):
            idx_b, idx_e = group_slice_bounds(i, num_groups, division, num_sn_stations)
            if split_side == 'b':
                doas_h[:, idx_b:idx_e], doas_v[:, idx_b:idx_e] = queues[i].get()
            else:
                doas_h[idx_b:idx_e], doas_v[idx_b:idx_e] = queues[i].get()
 
        for process in processes:
            process.join()
 
        return doas_h, doas_v


    def _doas_term_to_term(self, ite, pn_term_coords, sn_term_coords, pn_term_bsights, sn_term_bsights,
                         num_pn_panels, num_sn_panels):

        """
        PN terminals <-> SN terminals
        """

        pn_to_sn = compute_multiple_relative_doas(
            pn_term_coords[ite], sn_term_coords[ite], *pn_term_bsights[ite], num_pn_panels, num_sn_panels
        )
        sn_to_pn = compute_multiple_relative_doas(
            sn_term_coords[ite], pn_term_coords[ite], *sn_term_bsights[ite], num_sn_panels, num_pn_panels
        )
        return pn_to_sn, sn_to_pn


    def _doas_pn_term_to_sn_stat(self, ite, pn_term_coords, sn_stat_coords, pn_term_bsights, sn_stat_bsights,
                               num_pn_panels, num_sn_arrays):

        """
        PN terminals <-> SN stations
        """

        pn_to_sn = self._parallel_relative_doas(
            pn_term_coords[ite], sn_stat_coords[ite], pn_term_bsights[ite], sn_stat_bsights[ite], 
            num_pn_panels, num_sn_arrays, split_side = 'b'
        )

        sn_to_pn = self._parallel_relative_doas(
            sn_stat_coords[ite], pn_term_coords[ite], sn_stat_bsights[ite], pn_term_bsights[ite],
            num_sn_arrays, num_pn_panels, split_side = 'a'
        )

        return pn_to_sn, sn_to_pn

    def _doas_pn_stat_to_sn_stat(self, ite, pn_stat_coords, sn_stat_coords, pn_stat_bsights, sn_stat_bsights,
                               num_pn_arrays, num_sn_arrays):

        """
        PN stations <-> SN stations
        """

        pn_to_sn = self._parallel_relative_doas(
            pn_stat_coords[ite], sn_stat_coords[ite], pn_stat_bsights[ite], sn_stat_bsights[ite], 
            num_pn_arrays, num_sn_arrays, split_side = 'b'
        )

        sn_to_pn = self._parallel_relative_doas(
            sn_stat_coords[ite], pn_stat_coords[ite], sn_stat_bsights[ite], pn_stat_bsights[ite],
            num_sn_arrays, num_pn_arrays, split_side = 'a'
        )

        return pn_to_sn, sn_to_pn
        




    def compute_doas(self,):

        num_pn_term = self.pn_conf.num_terminals
        num_pn_stat = self.pn_conf.num_stations

        num_sn_term = self.sn_conf.num_terminals
        num_sn_stat = self.sn_conf.num_stations

        num_pn_panels = 1
        num_pn_arrays = 1

        num_sn_panels = self.sn_conf.num_panels
        num_sn_arrays = self.sn_conf.num_arrays

        pn_term_coords = self.pn_geom.terminals_coords
        pn_stat_coords  = self.pn_geom.stations_coords

        sn_term_coords = self.sn_geom.terminals_coords
        sn_stat_coords  = self.sn_geom.stations_coords

        pn_term_bsights = self.pn_geom.terminals_boresights
        pn_stat_bsights  = self.pn_geom.stations_boresights

        sn_term_bsights = self.sn_geom.terminals_boresights
        sn_stat_bsights  = self.sn_geom.stations_boresights

      



        n = self.num_snapshots

        # Links between PN terminals and SN terminals
        pn_term_to_sn_term_r_doas_for_all_snapshots = empty_object_array(n)
        sn_term_to_pn_term_r_doas_for_all_snapshots = empty_object_array(n)

        # Links between PN terminals and SN stations
        pn_term_to_sn_stat_r_doas_for_all_snapshots = empty_object_array(n)
        sn_stat_to_pn_term_r_doas_for_all_snapshots = empty_object_array(n)

        # Links between PN stations and SN stations
        pn_stat_to_sn_stat_r_doas_for_all_snapshots = empty_object_array(n)
        sn_stat_to_pn_stat_r_doas_for_all_snapshots = empty_object_array(n)



        for ite in range(self.num_snapshots):

            print('Inter network snapshot ' + str(ite))


            # Links between PN terminals and SN terminals
            pn_term_to_sn_term_r_doas_for_all_snapshots[ite], sn_term_to_pn_term_r_doas_for_all_snapshots[ite] = self._doas_term_to_term(
                ite, pn_term_coords, sn_term_coords, pn_term_bsights, sn_term_bsights, num_pn_panels, num_sn_panels
            )

            
            # Links between PN terminals and SN stations

            pn_term_to_sn_stat_r_doas_for_all_snapshots[ite], sn_stat_to_pn_term_r_doas_for_all_snapshots[ite] = self._doas_pn_term_to_sn_stat(
                ite, pn_term_coords, sn_stat_coords, pn_term_bsights, sn_stat_bsights, num_pn_panels, num_sn_arrays
            )


            # Links between PN stations and SN stations

            pn_stat_to_sn_stat_r_doas_for_all_snapshots[ite], sn_stat_to_pn_stat_r_doas_for_all_snapshots[ite] = self._doas_pn_stat_to_sn_stat(
                ite, pn_stat_coords, sn_stat_coords, pn_stat_bsights, sn_stat_bsights, num_pn_arrays, num_sn_arrays
            )

          

        
        self.pn_term_to_sn_term_r_doas_for_all_snapshots = pn_term_to_sn_term_r_doas_for_all_snapshots
        self.sn_term_to_pn_term_r_doas_for_all_snapshots = sn_term_to_pn_term_r_doas_for_all_snapshots

        self.pn_term_to_sn_stat_r_doas_for_all_snapshots = pn_term_to_sn_stat_r_doas_for_all_snapshots
        self.sn_stat_to_pn_term_r_doas_for_all_snapshots = sn_stat_to_pn_term_r_doas_for_all_snapshots

        self.pn_stat_to_sn_stat_r_doas_for_all_snapshots = pn_stat_to_sn_stat_r_doas_for_all_snapshots
        self.sn_stat_to_pn_stat_r_doas_for_all_snapshots = sn_stat_to_pn_stat_r_doas_for_all_snapshots

    # ------------------------------------------------------------------ #
    # 2. Large-scale fading + antenna gains
    # ------------------------------------------------------------------ #

    def _link_ls_fading_and_gain(self, coords_a, coords_b, height_a, height_b, fc, rng,
                            gain_method_a, gain_method_b, r_doas_a_to_b, r_doas_b_to_a):


        ls_fading, K = self.pn_conf.methods["lsf_model"].compute(
            coords_a, coords_b, height_a, height_b, fc, rng, None
        )


        gain_a_to_b = gain_method_a.compute(*r_doas_a_to_b)
        gain_b_to_a = gain_method_b.compute(*r_doas_b_to_a)

        ls_gain = (
            ls_fading[:, :, np.newaxis, np.newaxis] *
            gain_a_to_b *
            gain_b_to_a.transpose(1, 0, 3, 2)
        )

        return LinkLSF(ls_fading, K, gain_a_to_b, gain_b_to_a, ls_gain)




    def compute_large_scale_coeffs(self, rng):

        pn_term_coords = self.pn_geom.terminals_coords
        pn_stat_coords  = self.pn_geom.stations_coords

        sn_term_coords = self.sn_geom.terminals_coords
        sn_stat_coords  = self.sn_geom.stations_coords

        pn_term_height = self.pn_conf.terminal_height
        pn_stat_height = self.pn_conf.station_height

        sn_term_height = self.sn_conf.terminal_height
        sn_stat_height = self.sn_conf.station_height


        fc = self.pn_conf.carrier_frequency


        # SN stations (APs) and the PN terminals/stations (FS rx/tx) are fixed,
        # so these two links only need to be computed once, from the first
        # snapshot's DoAs, and then reused for every snapshot below.
        term_stat_fixed = self._link_ls_fading_and_gain(
            pn_term_coords[0], sn_stat_coords[0], pn_term_height, sn_stat_height, fc, rng,
            self.pn_conf.methods["terminal_antenna_gain"], self.sn_conf.methods["station_antenna_gain"],
            self.pn_term_to_sn_stat_r_doas_for_all_snapshots[0], self.sn_stat_to_pn_term_r_doas_for_all_snapshots[0],
        )

        stat_stat_fixed = self._link_ls_fading_and_gain(
            pn_stat_coords[0], sn_stat_coords[0], pn_stat_height, sn_stat_height, fc, rng,
            self.pn_conf.methods["station_antenna_gain"], self.sn_conf.methods["station_antenna_gain"],
            self.pn_stat_to_sn_stat_r_doas_for_all_snapshots[0], self.sn_stat_to_pn_stat_r_doas_for_all_snapshots[0],
        )


        n = self.num_snapshots

        # Links between PN terminals and SN terminals

        ### 1. Large scale fading and Rician K-factor
        term_term_ls_fading_for_all_snapshots = empty_object_array(n)
        term_term_K_for_all_snapshots         = empty_object_array(n)
        term_term_ls_gain_for_all_snapshots   = empty_object_array(n)


        term_stat_ls_fading_for_all_snapshots = empty_object_array(n)
        term_stat_K_for_all_snapshots         = empty_object_array(n)
        term_stat_ls_gain_for_all_snapshots   = empty_object_array(n)


        stat_stat_ls_fading_for_all_snapshots = empty_object_array(n)
        stat_stat_K_for_all_snapshots         = empty_object_array(n)
        stat_stat_ls_gain_for_all_snapshots   = empty_object_array(n)


        for ite in range(n):

            term_term = self._link_ls_fading_and_gain(
                pn_term_coords[ite], sn_term_coords[ite], pn_term_height, sn_term_height, fc, rng,
                self.pn_conf.methods["terminal_antenna_gain"], self.sn_conf.methods["terminal_antenna_gain"],
                self.pn_term_to_sn_term_r_doas_for_all_snapshots[ite], self.sn_term_to_pn_term_r_doas_for_all_snapshots[ite],
            )
            term_term_ls_fading_for_all_snapshots[ite] = term_term.ls_fading
            term_term_K_for_all_snapshots[ite]         = term_term.K
            term_term_ls_gain_for_all_snapshots[ite]   = term_term.ls_gain


            # Fixed links: reuse the values computed once above.
            term_stat_ls_fading_for_all_snapshots[ite] = term_stat_fixed.ls_fading
            term_stat_K_for_all_snapshots[ite]         = term_stat_fixed.K
            term_stat_ls_gain_for_all_snapshots[ite]   = term_stat_fixed.ls_gain
 
            stat_stat_ls_fading_for_all_snapshots[ite] = stat_stat_fixed.ls_fading
            stat_stat_K_for_all_snapshots[ite]         = stat_stat_fixed.K
            stat_stat_ls_gain_for_all_snapshots[ite]   = stat_stat_fixed.ls_gain




        self.pn_term_sn_term_ls_fading_for_all_snapshots = term_term_ls_fading_for_all_snapshots
        self.pn_term_sn_term_ls_gain_for_all_snapshots   = term_term_ls_gain_for_all_snapshots
        self.pn_term_sn_term_K_for_all_snapshots      = term_term_K_for_all_snapshots

        self.pn_term_sn_stat_ls_fading_for_all_snapshots = term_stat_ls_fading_for_all_snapshots
        self.pn_term_sn_stat_ls_gain_for_all_snapshots   = term_stat_ls_gain_for_all_snapshots
        self.pn_term_sn_stat_K_for_all_snapshots        = term_stat_K_for_all_snapshots

        self.pn_stat_sn_stat_ls_fading_for_all_snapshots = stat_stat_ls_fading_for_all_snapshots
        self.pn_stat_sn_stat_ls_gain_for_all_snapshots   = stat_stat_ls_gain_for_all_snapshots
        self.pn_stat_sn_stat_K_for_all_snapshots         = stat_stat_K_for_all_snapshots


        self._save_lsf_coeffs()


    def _save_lsf_coeffs(self):
        path = dir_path + '/scenarios_storage/InterNetwork/lsg_parameters/'
 
        save_npz(path, 'pn_term_sn_term_ls_fading_full.npz', pn_term_sn_term_ls_fading=self.pn_term_sn_term_ls_fading_for_all_snapshots)
        save_npz(path, 'pn_term_sn_term_ls_gain_full.npz',   pn_term_sn_term_ls_gain=self.pn_term_sn_term_ls_gain_for_all_snapshots)
        save_npz(path, 'pn_term_sn_term_K_full.npz',         pn_term_sn_term_K=self.pn_term_sn_term_K_for_all_snapshots)
 
        save_npz(path, 'pn_term_sn_stat_ls_fading_full.npz', pn_term_sn_stat_ls_fading=self.pn_term_sn_stat_ls_fading_for_all_snapshots)
        save_npz(path, 'pn_term_sn_stat_ls_gain_full.npz',   pn_term_sn_stat_ls_gain=self.pn_term_sn_stat_ls_gain_for_all_snapshots)
        save_npz(path, 'pn_term_sn_stat_K_full.npz',         pn_term_sn_stat_K=self.pn_term_sn_stat_K_for_all_snapshots)
 
        save_npz(path, 'pn_stat_sn_stat_ls_fading_full.npz', pn_stat_sn_stat_ls_fading=self.pn_stat_sn_stat_ls_fading_for_all_snapshots)
        save_npz(path, 'pn_stat_sn_stat_ls_gain_full.npz',   pn_stat_sn_stat_ls_gain=self.pn_stat_sn_stat_ls_gain_for_all_snapshots)
        save_npz(path, 'pn_stat_sn_stat_K_full.npz',         pn_stat_sn_stat_K=self.pn_stat_sn_stat_K_for_all_snapshots)


    def _R(self, r_doas, N_a, N_b):
        return self.sn_conf.methods["correlation_model"].compute_fast_integrals(*r_doas, N_a, N_b)


    def _parallel_R(self, doas_h, doas_v, num_panels_a, num_panels_b,
                                    a_N_h, a_N_v, split_side):
    
            """
            Relative DoAs from `a` to `b`, computed in parallel by splitting the SN
            stations (always the "AP" side of the link) across several processes.
     
            split_side='b' -> the SN stations are `coords_b` (sliced on axis 1 of the result)
            split_side='a' -> the SN stations are `coords_a` (sliced on axis 0 of the result)
     
            NOTE: `boresights_a` is always passed whole (never sliced), matching the
            original implementation's behaviour even in the split_side='a' case.
            """
    
    
            num_a = doas_h.shape[0]
            num_b = doas_v.shape[1]
    
            num_groups = os.cpu_count() - 2
            num_sn_stations = self.sn_conf.num_stations
            division = num_sn_stations // num_groups

            a_N = a_N_h * a_N_v
    
            R_matrices = np.zeros((num_a, num_b, num_panels_a, num_panels_b, a_N, a_N), dtype=np.complex128)
    
            processes, queues = [], []
    
            for i in range(num_groups):
    
                idx_b, idx_e = group_slice_bounds(i, num_groups, division, num_sn_stations)
                if split_side == 'b':
                    args = (doas_h[:, idx_b:idx_e], doas_v[:, idx_b:idx_e], a_N_h, a_N_v)
    
                else:
                    args = (doas_h[idx_b:idx_e], doas_v[idx_b:idx_e], a_N_h, a_N_v)
    
                process, queue = self._start(self.sn_conf.methods["correlation_model"].compute_fast_integrals_for_queue, args)
                processes.append(process)
                queues.append(queue)
    
            for i in range(num_groups):
                idx_b, idx_e = self._group_slice_bounds(i, num_groups, division, num_sn_stations)
                if split_side == 'b':
                    R_matrices[:, idx_b:idx_e], doas_v[:, idx_b:idx_e] = queues[i].get()
                else:
                    R_matrices[idx_b:idx_e], doas_v[idx_b:idx_e] = queues[i].get()
     
            for process in processes:
                process.join()
     
            return R_matrices

    def compute_R_matrices(self):

        """
        
        Compute the spatial correlation matrices for internetwork links. 
        The matrices are computed for each snapshot and stored in arrays for later use.
        
        """

        pn_panel_N_h = 1
        pn_panel_N_v = 1

        pn_array_N_h = 1
        pn_array_N_v = 1

        sn_panel_N_h = self.sn_conf.panel_N_h
        sn_panel_N_v = self.sn_conf.panel_N_v

        sn_array_N_h = self.sn_conf.array_N_h
        sn_array_N_v = self.sn_conf.array_N_v

        n = self.num_snapshots

        ### OBS: The default is [RX] -> [TX] for the R matrices, so the first argument is always the RX and the second is always the TX

        ### Storage of the R matrices for each snapshot
        pn_term_sn_term_R_matrices_for_all_snapshots = empty_object_array(n)
        sn_term_pn_term_R_matrices_for_all_snapshots = empty_object_array(n)

        ### Storage of the R matrices for each snapshot
        pn_term_sn_stat_R_matrices_for_all_snapshots = empty_object_array(n)
        sn_stat_pn_term_R_matrices_for_all_snapshots = empty_object_array(n)

        ### Storage of the R matrices for each snapshot
        pn_stat_sn_stat_R_matrices_for_all_snapshots = empty_object_array(n)
        sn_stat_pn_stat_R_matrices_for_all_snapshots = empty_object_array(n)





        ### OBS: SN stations (APs) and the PN terminals (FS rx) are fixed, the R matrices don't change

        pn_term_sn_stat_R = self._R(self.pn_term_to_sn_stat_r_doas_for_all_snapshots[0], pn_panel_N_v, pn_panel_N_v)

        sn_stat_pn_term_R = self._R(self.sn_stat_to_pn_term_r_doas_for_all_snapshots[0], sn_array_N_h, sn_array_N_v)


        ### OBS: SN stations (APs) and the PN stations (FS tx) are fixed, the R matrices don't change

        pn_stat_sn_stat_R = self._R(self.pn_stat_to_sn_stat_r_doas_for_all_snapshots[0], pn_array_N_h, pn_array_N_v)

        sn_stat_pn_stat_R = self._R(self.sn_stat_to_pn_stat_r_doas_for_all_snapshots[0], sn_array_N_h, sn_array_N_v)


        for ite in range(self.num_snapshots):

            # Links between PN terminals and SN terminals

            pn_term_sn_term_R = self._R(self.pn_term_to_sn_term_r_doas_for_all_snapshots[ite], pn_panel_N_v, pn_panel_N_v)

            sn_term_pn_term_R = self._R(self.sn_term_to_pn_term_r_doas_for_all_snapshots[ite], sn_panel_N_h, sn_panel_N_v)

            pn_term_sn_term_R_matrices_for_all_snapshots[ite] = pn_term_sn_term_R
            sn_term_pn_term_R_matrices_for_all_snapshots[ite] = sn_term_pn_term_R


            ### OBS: SN stations (APs) and the PN terminals (FS rx) are fixed, the R matrices don't change
            pn_term_sn_stat_R_matrices_for_all_snapshots[ite] = pn_term_sn_stat_R
            sn_stat_pn_term_R_matrices_for_all_snapshots[ite] = sn_stat_pn_term_R

            ### OBS: SN stations (APs) and the PN stations (FS tx) are fixed, the R matrices don't change
            pn_stat_sn_stat_R_matrices_for_all_snapshots[ite] = pn_stat_sn_stat_R
            sn_stat_pn_stat_R_matrices_for_all_snapshots[ite] = sn_stat_pn_stat_R


        self.pn_term_to_sn_term_R_matrices_for_all_snapshots = pn_term_sn_term_R_matrices_for_all_snapshots
        self.sn_term_to_pn_term_R_matrices_for_all_snapshots = sn_term_pn_term_R_matrices_for_all_snapshots

        self.pn_term_to_sn_stat_R_matrices_for_all_snapshots = pn_term_sn_stat_R_matrices_for_all_snapshots
        self.sn_stat_to_pn_term_R_matrices_for_all_snapshots = sn_stat_pn_term_R_matrices_for_all_snapshots

        self.pn_stat_to_sn_stat_R_matrices_for_all_snapshots = pn_stat_sn_stat_R_matrices_for_all_snapshots
        self.sn_stat_to_pn_stat_R_matrices_for_all_snapshots = sn_stat_pn_stat_R_matrices_for_all_snapshots





    def _save_R_matrices(self):

        path = dir_path + '/scenarios_storage/InterNetwork/R_matrices/'

        save_npz(path + 'pn_term_sn_term_R_matrices_full', pn_term_sn_term_R_matrices = self.pn_term_to_sn_term_R_matrices_full)
        save_npz(path + 'sn_term_pn_term_R_matrices_full', sn_term_pn_term_R_matrices = self.sn_term_to_pn_term_R_matrices_full)

        save_npz(path + 'pn_term_sn_stat_R_matrices_full', pn_term_sn_stat_R_matrices = self.pn_term_to_sn_stat_R_matrices_full)
        save_npz(path + 'sn_stat_pn_term_R_matrices_full', sn_stat_pn_term_R_matrices = self.sn_stat_to_pn_term_R_matrices_full)

        save_npz(path + 'pn_stat_sn_stat_R_matrices_full', pn_stat_sn_stat_R_matrices = self.pn_stat_to_sn_stat_R_matrices_full)
        save_npz(path + 'sn_stat_pn_stat_R_matrices_full', sn_stat_pn_stat_R_matrices = self.sn_stat_to_pn_stat_R_matrices_full)



    def _generate_channel(self, ite, ls_gain_for_all_snapshots, K_for_all_snapshots, rx_R_for_all_snapshots, tx_R_for_all_snapshots,
                           rx_doas_for_all_snapshots, tx_doas_for_all_snapshots, rx_N, tx_N, rng):
        return self.pn_conf.methods["channel_model"].generate_multiple_channels(
            ls_gain_coeffs=ls_gain_for_all_snapshots[ite],
            K_coeffs=K_for_all_snapshots[ite][:, :, np.newaxis, np.newaxis],
            rx_R_matrices=rx_R_for_all_snapshots[ite],
            tx_R_matrices=tx_R_for_all_snapshots[ite],
            rx_doas=(rx_doas_for_all_snapshots[ite][0], rx_doas_for_all_snapshots[ite][1]),
            tx_doas=(tx_doas_for_all_snapshots[ite][0], tx_doas_for_all_snapshots[ite][1]),
            rx_N=rx_N,
            tx_N=tx_N,
            rng=rng,
        )



    def generate_channels(self, rng):

        """
        
        Generate the channel coefficients for internetwork links.
        The coefficients are generated for each snapshot and stored in arrays for later use.
        
        """

        # Primary network terminal antennas
        pn_pan_N_h = 1
        pn_pan_N_v = 1
        pn_pan_N = (pn_pan_N_h, pn_pan_N_v)

        # Primary network station antennas
        pn_arr_N_h = 1
        pn_arr_N_v = 1
        pn_arr_N = (pn_arr_N_h, pn_arr_N_v)


        sn_pan_N_h = self.sn_conf.panel_N_h
        sn_pan_N_v = self.sn_conf.panel_N_v
        sn_pan_N = (sn_pan_N_h, sn_pan_N_v)
    
        sn_arr_N_h = self.sn_conf.array_N_h
        sn_arr_N_v = self.sn_conf.array_N_v
        sn_arr_N = (sn_arr_N_h, sn_arr_N_v)


        n = self.num_snapshots
        
        # Links between PN terminals and SN terminals
        term_term_H = np.empty(self.num_snapshots, dtype=np.ndarray)

        # Links between PN terminals and SN stations
        term_stat_H = np.empty(self.num_snapshots, dtype=np.ndarray)
        
        # Links between PN stations and SN stations
        stat_stat_H = np.empty(self.num_snapshots, dtype=np.ndarray)


        
        for ite in range(n):
 
            term_term_H[ite] = self._generate_channel(
                ite, self.pn_term_sn_term_ls_gain_for_all_snapshots, self.pn_term_sn_term_K_for_all_snapshots,
                self.pn_term_to_sn_term_R_matrices_for_all_snapshots, self.sn_term_to_pn_term_R_matrices_for_all_snapshots,
                self.pn_term_to_sn_term_r_doas_for_all_snapshots, self.sn_term_to_pn_term_r_doas_for_all_snapshots,
                pn_pan_N, sn_pan_N, rng
            )
 
            term_stat_H[ite] = self._generate_channel(
                ite, self.pn_term_sn_stat_ls_gain_for_all_snapshots, self.pn_term_sn_stat_K_for_all_snapshots,
                self.pn_term_to_sn_stat_R_matrices_for_all_snapshots, self.sn_stat_to_pn_term_R_matrices_for_all_snapshots,
                self.pn_term_to_sn_stat_r_doas_for_all_snapshots, self.sn_stat_to_pn_term_r_doas_for_all_snapshots,
                pn_pan_N, sn_arr_N, rng
            )
 
            stat_stat_H[ite] = self._generate_channel(
                ite, self.pn_stat_sn_stat_ls_gain_for_all_snapshots, self.pn_stat_sn_stat_K_for_all_snapshots,
                self.pn_stat_to_sn_stat_R_matrices_for_all_snapshots, self.sn_stat_to_pn_stat_R_matrices_for_all_snapshots,
                self.pn_stat_to_sn_stat_r_doas_for_all_snapshots, self.sn_stat_to_pn_stat_r_doas_for_all_snapshots,
                pn_arr_N, sn_arr_N, rng
            )
 
        self.pn_term_sn_term_H_for_all_snapshots = term_term_H
        self.pn_term_sn_stat_H_for_all_snapshots = term_stat_H
        self.pn_stat_sn_stat_H_for_all_snapshots = stat_stat_H
 
        self._save_channels()
 
    def _save_channels(self):
        path = dir_path + '/scenarios_storage/InterNetwork/H_coeffs/'
 
        save_npz(path, 'pn_term_sn_term_H_full.npz', pn_term_sn_term_H=self.pn_term_sn_term_H_for_all_snapshots)
        save_npz(path, 'pn_term_sn_stat_H_full.npz', pn_term_sn_stat_H=self.pn_term_sn_stat_H_for_all_snapshots)
        save_npz(path, 'pn_stat_sn_stat_H_full.npz', pn_stat_sn_stat_H=self.pn_stat_sn_stat_H_for_all_snapshots)


