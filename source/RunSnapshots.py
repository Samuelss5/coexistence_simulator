from importlib.resources import path

import numpy as np

from source.geometry.angles import compute_multiple_doas, compute_multiple_relative_doas, compute_multiple_relative_doas_for_queue

import multiprocessing as mp

import os

mp.set_start_method('fork')

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
            
    

class RunDMimoSnapshots:

    def __init__(self, config):
        self.config = config

    def _start(self, func, arguments):
            queue = mp.Queue()
            args = (queue, *arguments)
            process = mp.Process(target=func, args=args)
            process.start()
            return process, queue

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
        

        # The APs positions are equal for every single snapshot
        aps_coords = self.config.methods["station_deployment"].deploy(
            ap_height, num_aps, rng
        )


        # Tuple
        aps_boresights = self.config.methods["station_sectorization"].compute(
            num_aps, num_arrays, self.config.station_downtilt
        )

    
        ues_coords_full     = np.empty(num_snapshots, dtype=np.ndarray)
        aps_coords_full     = np.empty(num_snapshots, dtype=np.ndarray)

        ues_boresights_full = np.empty(num_snapshots, dtype=np.ndarray)
        aps_boresights_full = np.empty(num_snapshots, dtype=np.ndarray)

        lsf_coeffs_full     = np.empty(num_snapshots, dtype=np.ndarray)
        lsg_coeffs_full     = np.empty(num_snapshots, dtype=np.ndarray)

        K_coeffs_full       = np.empty(num_snapshots, dtype=np.ndarray)

        ues_R_matrices_full = np.empty(num_snapshots, dtype=np.ndarray)
        aps_R_matrices_full = np.empty(num_snapshots, dtype=np.ndarray)

        H_coeffs_full = np.empty(num_snapshots, dtype=np.ndarray)

        for ite in range(num_snapshots):

            print('DMimo snapshot ' + str(ite))

            aps_coords_full[ite]     = aps_coords
            aps_boresights_full[ite] = aps_boresights

            # 1. Generating UEs coordinates
            ues_coords = self.config.methods["terminal_deployment"].deploy(
                aps_coords, ue_height, num_ues, rng
            )

            ues_coords_full[ite] = ues_coords

            # 2. Generating UEs panels boresights
            ues_boresights = self.config.methods["terminal_sectorization"].compute(
                num_ues, num_panels, rng
            )

            ues_boresights_full[ite] = ues_boresights


            
            num_cores = os.cpu_count()
            num_aps_groups = num_cores - 2
            aps_division = num_aps // num_aps_groups


            # ______________________________________
            #   Relative AoAs from UEs point of view
            # ______________________________________

            ues_r_doas_h = np.zeros((num_ues, num_aps, num_panels, num_arrays), dtype=float)
            ues_r_doas_v = np.zeros((num_ues, num_aps, num_panels, num_arrays), dtype=float)
            
            processes = []
            queues    = []

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                args = (ues_coords, aps_coords[idx_b:idx_e], *ues_boresights, num_panels, num_arrays)

                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)

                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                ues_r_doas_h[:, idx_b:idx_e], ues_r_doas_v[:, idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()

            # ______________________________________
            #   Relative AoAs from APs point of view
            # ______________________________________

            aps_r_doas_h = np.zeros((num_aps, num_ues, num_arrays, num_panels), dtype=float)
            aps_r_doas_v = np.zeros((num_aps, num_ues, num_arrays, num_panels), dtype=float)
                        
            processes = []
            queues    = []

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                args = (aps_coords[idx_b:idx_e], ues_coords, *aps_boresights, num_arrays, num_panels)

                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)
                
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                aps_r_doas_h[idx_b:idx_e], aps_r_doas_v[idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()
            


            ues_gains = np.zeros((num_ues, num_aps, num_panels, num_arrays), dtype=float)
                        
            processes = []
            queues    = []

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                args = (ues_r_doas_h[:, idx_b:idx_e], ues_r_doas_v[:, idx_b:idx_e])

                P, Q = self._start(self.config.methods["terminal_antenna_gain"].compute_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                ues_gains[:, idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()
            

            aps_gains = np.zeros((num_aps, num_ues, num_arrays, num_panels), dtype=float)
            processes = []
            queues    = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                args = (aps_r_doas_h[idx_b:idx_e], aps_r_doas_v[idx_b:idx_e])

                P, Q = self._start(self.config.methods["station_antenna_gain"].compute_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps
                aps_gains[idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()


            
            lsf_coeffs = np.zeros((num_ues, num_aps), dtype=float)
            K_coeffs   = np.zeros((num_ues, num_aps), dtype=float)
            processes = []
            queues    = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                args = (ues_coords, aps_coords[idx_b:idx_e], ue_height, ap_height, self.config.carrier_frequency, rng, None)

                P, Q = self._start(self.config.methods["lsf_model"].compute_for_queued, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps
                lsf_coeffs[:, idx_b:idx_e], K_coeffs[:, idx_b:idx_e] = queues[i].get()

            for P in processes:
                P.join()


            # Large scale fading coefficients
            # lsf_coeffs, K_coeffs = self.config.methods["lsf_model"].compute(ues_coords, aps_coords, ue_height, ap_height, self.config.carrier_frequency, rng, None)
            # lsf_coeffs_full[i] = lsf_coeffs
            

            # Large scale gain coefficients (Certified that it works as it should)
            lsg_coeffs = lsf_coeffs[:, :, np.newaxis, np.newaxis] * ues_gains * aps_gains.transpose(1,0,3,2)
            lsg_coeffs_full[ite] = lsg_coeffs
        
            # Spatial correlation matrixes
            ues_R_matrices = self.config.methods["correlation_model"].compute_fast_integrals(
                ues_r_doas_h, ues_r_doas_v, panel_N_h, panel_N_v
                )


            aps_R_matrices = np.empty((num_aps, num_ues, num_arrays, num_panels), dtype=np.ndarray)
            processes = []
            queues    = []

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps

                args = (aps_r_doas_h[idx_b:idx_e, ...], aps_r_doas_v[idx_b:idx_e, ...], array_N_h, array_N_v)
                P, Q = self._start(self.config.methods["correlation_model"].compute_fast_integrals_for_queue, args)

                processes.append(P)
                queues.append(Q)

    
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_aps
                aps_R_matrices[idx_b:idx_e] = queues[i].get()
            
    
            for P in processes:
                P.join()

    
            ues_R_matrices_full[ite] = ues_R_matrices
            aps_R_matrices_full[ite] = aps_R_matrices


            H_coeffs = self.config.methods["channel_model"].generate_multiple_channels(
                lsg_coeffs, K_coeffs[:, :, np.newaxis, np.newaxis],
                ues_R_matrices, aps_R_matrices,
                ues_r_doas_h, ues_r_doas_v, 
                aps_r_doas_h, aps_r_doas_v,
                panel_N_h, panel_N_v,
                array_N_h, array_N_v,
                rng
            )

            H_coeffs_full[ite] = H_coeffs
        
        basic_path = '/home/samuelserejosilva/Projetos/sim_scenario/scenarios_storage/DMimo/'
        

        # np.savez('aps_coords.npz', aps_coords = aps_coords_for_all_snapshots)
        # np.savez('ues_coords.npz', ues_coords = ues_coords_for_all_snapshots)

        np.savez(basic_path + 'lsg_parameters/lsg_coeffs_full.npz', lsg_coeffs = lsg_coeffs_full)
        np.savez(basic_path + 'lsg_parameters/K_coeffs_full.npz',   K_coeffs   = K_coeffs_full)

        np.savez(basic_path + 'R_matrices/ues_R_matrices_full.npz', ues_R_matrices = ues_R_matrices_full)
        np.savez(basic_path + 'R_matrices/aps_R_matrices_full.npz', aps_R_matrices = aps_R_matrices_full)

        np.savez(basic_path + 'H_coeffs/H_coeffs_full.npz', H_coeffs = H_coeffs_full)


        return (ues_coords_full, 
                aps_coords_full,
                
                ues_boresights_full, aps_boresights_full,

                lsg_coeffs_full,

                H_coeffs_full
                )            




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

      


        # ___________________________________________
        # Links between PN terminals and SN terminals
        # ___________________________________________    

        pn_term_to_sn_term_r_doas_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_term_to_pn_term_r_doas_full = np.empty(self.num_snapshots, dtype=np.ndarray)

        # ___________________________________________
        # Links between PN terminals and SN stations
        # ___________________________________________ 

        pn_term_to_sn_stat_r_doas_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_stat_to_pn_term_r_doas_full = np.empty(self.num_snapshots, dtype=np.ndarray)

        # ___________________________________________
        # Links between PN stations and SN stations
        # ___________________________________________ 

        pn_stat_to_sn_stat_r_doas_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_stat_to_pn_stat_r_doas_full = np.empty(self.num_snapshots, dtype=np.ndarray)



        for ite in range(self.num_snapshots):

            print('Inter network snapshot ' + str(ite))


            # ___________________________________________
            # Links between PN terminals and SN terminals
            # ___________________________________________            

            pn_term_to_sn_term_r_doas_full[ite] = compute_multiple_relative_doas(
                pn_term_coords[ite], sn_term_coords[ite], *pn_term_bsights[ite], num_pn_panels, num_sn_panels
            )

            sn_term_to_pn_term_r_doas_full[ite] = compute_multiple_relative_doas(
                sn_term_coords[ite], pn_term_coords[ite], *sn_term_bsights[ite], num_sn_panels, num_pn_panels
            )

            num_cores = os.cpu_count()
            num_aps_groups = num_cores - 2
            aps_division = self.sn_conf.num_stations // num_aps_groups


            # ___________________________________________
            # Links between PN terminals and SN stations
            # ___________________________________________ 

            pn_term_to_sn_stat_r_doas_h = np.zeros((num_pn_term, num_sn_stat, num_pn_panels, num_sn_arrays), dtype=float)
            pn_term_to_sn_stat_r_doas_v = np.zeros((num_pn_term, num_sn_stat, num_pn_panels, num_sn_arrays), dtype=float)

            processes = []
            queues    = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat

                args = (pn_term_coords[ite], sn_stat_coords[ite][idx_b:idx_e], *pn_term_bsights[ite], num_pn_panels, num_sn_arrays)

                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)
                processes.append(P)
                queues.append(Q)

        
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat

                pn_term_to_sn_stat_r_doas_h[:, idx_b:idx_e], pn_term_to_sn_stat_r_doas_v[:, idx_b:idx_e] = queues[i].get()


            pn_term_to_sn_stat_r_doas_full[ite] = (pn_term_to_sn_stat_r_doas_h, pn_term_to_sn_stat_r_doas_v)

            for P in processes:
                P.join()


            sn_stat_to_pn_term_r_doas_h = np.zeros((num_sn_stat, num_pn_term, num_sn_arrays, num_pn_panels), dtype=float)
            sn_stat_to_pn_term_r_doas_v = np.zeros((num_sn_stat, num_pn_term, num_sn_arrays, num_pn_panels), dtype=float)

            processes = []
            queues    = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat

                args = (sn_stat_coords[ite][idx_b:idx_e], pn_term_coords[ite], *sn_stat_bsights[ite], num_sn_arrays, num_pn_panels)
                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat

                sn_stat_to_pn_term_r_doas_h[idx_b:idx_e], sn_stat_to_pn_term_r_doas_v[idx_b:idx_e] = queues[i].get()

            sn_stat_to_pn_term_r_doas_full[ite] = (sn_stat_to_pn_term_r_doas_h, sn_stat_to_pn_term_r_doas_v)

            for P in processes:
                P.join()

            # ___________________________________________
            # Links between PN stations and SN stations
            # ___________________________________________ 

            pn_stat_sn_stat_r_doas_h = np.zeros((num_pn_stat, num_sn_stat, num_pn_arrays, num_sn_arrays), dtype=float)
            pn_stat_sn_stat_r_doas_v = np.zeros((num_pn_stat, num_sn_stat, num_pn_arrays, num_sn_arrays), dtype=float)

            processes = []
            queues = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat

                args = (pn_stat_coords[ite], sn_stat_coords[ite][idx_b:idx_e], *pn_stat_bsights[ite], num_pn_arrays, num_sn_arrays)
                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat
                pn_stat_sn_stat_r_doas_h[:, idx_b:idx_e], pn_stat_sn_stat_r_doas_v[:, idx_b:idx_e] = queues[i].get()

            pn_stat_to_sn_stat_r_doas_full[ite] = (pn_stat_sn_stat_r_doas_h, pn_stat_sn_stat_r_doas_v)

            for P in processes:
                P.join()


            sn_stat_to_pn_stat_r_doas_h = np.zeros((num_sn_stat, num_pn_stat, num_sn_arrays, num_pn_arrays), dtype=float)
            sn_stat_to_pn_stat_r_doas_v = np.zeros((num_sn_stat, num_pn_stat, num_sn_arrays, num_pn_arrays), dtype=float)

            processes = []
            queues = []
            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat

                args = (sn_stat_coords[ite][idx_b:idx_e], pn_stat_coords[ite], *sn_stat_bsights[ite], num_sn_arrays, num_pn_arrays)
                P, Q = self._start(compute_multiple_relative_doas_for_queue, args)
                processes.append(P)
                queues.append(Q)

            for i in range(num_aps_groups):
                idx_b = i * aps_division
                idx_e = (i + 1) * aps_division if i < num_aps_groups - 1 else num_sn_stat
                sn_stat_to_pn_stat_r_doas_h[idx_b:idx_e], sn_stat_to_pn_stat_r_doas_v[idx_b:idx_e] = queues[i].get()

            sn_stat_to_pn_stat_r_doas_full[ite] = (sn_stat_to_pn_stat_r_doas_h, sn_stat_to_pn_stat_r_doas_v)

        
        self.pn_term_to_sn_term_r_doas_full = pn_term_to_sn_term_r_doas_full
        self.sn_term_to_pn_term_r_doas_full = sn_term_to_pn_term_r_doas_full

        self.pn_term_to_sn_stat_r_doas_full = pn_term_to_sn_stat_r_doas_full
        self.sn_stat_to_pn_term_r_doas_full = sn_stat_to_pn_term_r_doas_full

        self.pn_stat_to_sn_stat_r_doas_full = pn_stat_to_sn_stat_r_doas_full
        self.sn_stat_to_pn_stat_r_doas_full = sn_stat_to_pn_stat_r_doas_full



    def compute_lsf_coeffs(self, rng):

        pn_term_coords = self.pn_geom.terminals_coords
        pn_stat_coords  = self.pn_geom.stations_coords

        sn_term_coords = self.sn_geom.terminals_coords
        sn_stat_coords  = self.sn_geom.stations_coords

        pn_term_height = self.pn_conf.terminal_height
        pn_stat_height = self.pn_conf.station_height

        sn_term_height = self.sn_conf.terminal_height
        sn_stat_height = self.sn_conf.station_height


        fc = self.pn_conf.carrier_frequency

        # ___________________________________________
        # Links between PN terminals and SN terminals
        # ___________________________________________ 

        ### 1. Large scale fading and Rician K-factor
        pn_term_sn_term_ls_fading_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        pn_term_sn_term_K_full         = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### 2. Antenna gains
        pn_term_to_sn_term_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_term_to_pn_term_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### 3. Large scale gains
        pn_term_sn_term_ls_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)


    # ______________________________________________________________________________________
    #   Links between PN terminals and SN stations
    # ______________________________________________________________________________________ 

        ### 1. Storage of Large scale fading and Rician K-factor
        pn_term_sn_stat_ls_fading_full = np.zeros(self.num_snapshots, dtype=np.ndarray)
        pn_term_sn_stat_K_full         = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### 2. Storage of Antenna gain
        pn_term_to_sn_stat_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_stat_to_pn_term_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### 3. Storage of Large scale gains
        pn_term_sn_stat_ls_gain_full = np.empty(self.num_snapshots, dtype=np.ndarray)


        ### 1. Computing of Large scale fading and Rician K-factor
        (
        pn_term_sn_stat_ls_fading, 
        pn_term_sn_stat_K ) = self.pn_conf.methods["lsf_model"].compute( pn_term_coords[0], sn_stat_coords[0], pn_term_height, sn_stat_height, fc, rng, None)

        ### 2. Computing of Antenna gain
        pn_term_to_sn_stat_gain = self.pn_conf.methods["terminal_antenna_gain"].compute(*self.pn_term_to_sn_stat_r_doas_full[0])
        sn_stat_to_pn_term_gain = self.sn_conf.methods["station_antenna_gain"].compute( *self.sn_stat_to_pn_term_r_doas_full[0])

        ### 3. Computing of Large scale gains
        pn_term_sn_stat_ls_gain = (
            pn_term_sn_stat_ls_fading[:, :, np.newaxis, np.newaxis] * 
            pn_term_to_sn_stat_gain * 
            sn_stat_to_pn_term_gain.transpose(1,0,3,2) 
            )

        


    # ______________________________________________________________________________________
    #   Links between PN stations and SN stations
    # ______________________________________________________________________________________
        ### 1. Storage of Large scale fading and Rician K-factor
        pn_stat_sn_stat_ls_fading_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        pn_stat_sn_stat_K_full         = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### 2. Storage of Antenna gain
        pn_stat_to_sn_stat_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_stat_to_pn_stat_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### 3. Storage of Large scale gains
        pn_stat_sn_stat_ls_gain_full   = np.empty(self.num_snapshots, dtype=np.ndarray)


        ### 1. Computing of Large scale fading and Rician K-factor
        (
        pn_stat_sn_stat_ls_fading, 
        pn_stat_sn_stat_K) = self.pn_conf.methods["lsf_model"].compute(pn_stat_coords[0], sn_stat_coords[0], pn_stat_height, sn_stat_height, fc, rng, None)
        
        ### 2. Computing of Antenna gain
        pn_stat_to_sn_stat_gain = self.pn_conf.methods["station_antenna_gain"].compute(*self.pn_stat_to_sn_stat_r_doas_full[0])
        sn_stat_to_pn_stat_gain = self.sn_conf.methods["station_antenna_gain"].compute(*self.sn_stat_to_pn_stat_r_doas_full[0])
                
        ### 3. Computing of Large scale gains
        pn_stat_sn_stat_ls_gain = (
            pn_stat_sn_stat_ls_fading[:, :, np.newaxis, np.newaxis] * 
            pn_stat_to_sn_stat_gain * 
            sn_stat_to_pn_stat_gain.transpose(1,0,3,2) 
                    )

    

        
        

        for ite in range(self.num_snapshots):

            # ___________________________________________
            # Links between PN terminals and SN terminals
            # ___________________________________________    

            ### 1. Computing of Large scale fading and Rician K-factors
            (
            pn_term_sn_term_ls_fading, 
            pn_term_sn_term_K) = self.pn_conf.methods["lsf_model"].compute(pn_term_coords[ite], sn_term_coords[ite], pn_term_height, sn_term_height, fc, rng, None)

            pn_term_sn_term_ls_fading_full[ite] = pn_term_sn_term_ls_fading
            pn_term_sn_term_K_full  [ite] = pn_term_sn_term_K

            ### 2. Computing of Antenna gains
            pn_term_to_sn_term_gain = self.pn_conf.methods["terminal_antenna_gain"].compute(*self.pn_term_to_sn_term_r_doas_full[ite])
            sn_term_to_pn_term_gain = self.sn_conf.methods["terminal_antenna_gain"].compute(*self.sn_term_to_pn_term_r_doas_full[ite])

            pn_term_to_sn_term_gain_full[ite] = pn_term_to_sn_term_gain
            sn_term_to_pn_term_gain_full[ite] = sn_term_to_pn_term_gain

            ### 3. Computing of Large scale gains
            pn_term_sn_term_ls_gain = (
                pn_term_sn_term_ls_fading[:, :, np.newaxis, np.newaxis] * 
                pn_term_to_sn_term_gain * 
                sn_term_to_pn_term_gain.transpose(1,0,3,2) 
                )

            pn_term_sn_term_ls_gain_full[ite] = pn_term_sn_term_ls_gain


            ### OBS: SN stations (APs) and the PN terminals (FS rx) are fixed, the ls parameters don't change
            pn_term_sn_stat_ls_fading_full[ite] = pn_term_sn_stat_ls_fading
            pn_term_sn_stat_K_full  [ite] = pn_term_sn_stat_K
            pn_term_to_sn_stat_gain_full  [ite] = pn_term_to_sn_stat_gain 
            sn_stat_to_pn_term_gain_full  [ite] = sn_stat_to_pn_term_gain
            pn_term_sn_stat_ls_gain_full  [ite] = pn_term_sn_stat_ls_gain       


            ### OBS: SN stations (APs) and the PN stations (FS tx) are fixed, the ls parameters don't change
            pn_stat_sn_stat_ls_fading_full[ite] = pn_stat_sn_stat_ls_fading
            pn_stat_sn_stat_K_full  [ite] = pn_stat_sn_stat_K
            pn_stat_to_sn_stat_gain_full  [ite] = pn_stat_to_sn_stat_gain 
            sn_stat_to_pn_stat_gain_full  [ite] = sn_stat_to_pn_stat_gain
            pn_stat_sn_stat_ls_gain_full  [ite] = pn_stat_sn_stat_ls_gain


        self.pn_term_sn_term_ls_fading_full = pn_term_sn_term_ls_fading_full
        self.pn_term_sn_term_ls_gain_full   = pn_term_sn_term_ls_gain_full
        self.pn_term_sn_term_K_full         = pn_term_sn_term_K_full

        self.pn_term_sn_stat_ls_fading_full = pn_term_sn_stat_ls_fading_full
        self.pn_term_sn_stat_ls_gain_full   = pn_term_sn_stat_ls_gain_full
        self.pn_term_sn_stat_K_full         = pn_term_sn_stat_K_full

        self.pn_stat_sn_stat_ls_fading_full = pn_stat_sn_stat_ls_fading_full
        self.pn_stat_sn_stat_ls_gain_full   = pn_stat_sn_stat_ls_gain_full
        self.pn_stat_sn_stat_K_full         = pn_stat_sn_stat_K_full


        path = '/home/samuelserejosilva/Projetos/sim_scenario/scenarios_storage/InterNetwork/lsg_parameters/'

        np.savez(path + 'pn_term_sn_term_ls_fading_full.npz', pn_term_sn_term_ls_fading = self.pn_term_sn_term_ls_fading_full)
        np.savez(path + 'pn_term_sn_term_ls_gain_full.npz',   pn_term_sn_term_ls_gain   = self.pn_term_sn_term_ls_gain_full)
        np.savez(path + 'pn_term_sn_term_K_full.npz',         pn_term_sn_term_K         = self.pn_term_sn_term_K_full)


        np.savez(path + 'pn_term_sn_stat_ls_fading_full.npz', pn_term_sn_stat_ls_fading = self.pn_term_sn_stat_ls_fading_full)
        np.savez(path + 'pn_term_sn_stat_ls_gain_full.npz',   pn_term_sn_stat_ls_gain   = self.pn_term_sn_stat_ls_gain_full)
        np.savez(path + 'pn_term_sn_stat_K_full.npz',         pn_term_sn_stat_K         = self.pn_term_sn_stat_K_full)

        np.savez(path + 'pn_stat_sn_stat_ls_fading_full.npz', pn_stat_sn_stat_ls_fading = self.pn_stat_sn_stat_ls_fading_full)
        np.savez(path + 'pn_stat_sn_stat_ls_gain_full.npz',   pn_stat_sn_stat_ls_gain   = self.pn_stat_sn_stat_ls_gain_full)
        np.savez(path + 'pn_stat_sn_stat_K_full.npz',         pn_stat_sn_stat_K         = self.pn_stat_sn_stat_K_full)
    


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

        ### OBS: The default is [RX] -> [TX] for the R matrices, so the first argument is always the RX and the second is always the TX

        ### Storage of the R matrices for each snapshot
        pn_term_to_sn_term_R_matrices_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_term_to_pn_term_R_matrices_full = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### Storage of the R matrices for each snapshot
        pn_term_to_sn_stat_R_matrices_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_stat_to_pn_term_R_matrices_full = np.empty(self.num_snapshots, dtype=np.ndarray)

        ### Storage of the R matrices for each snapshot
        pn_stat_to_sn_stat_R_matrices_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        sn_stat_to_pn_stat_R_matrices_full = np.empty(self.num_snapshots, dtype=np.ndarray)

        # ______________________________________________________________________________________
        # Links between PN terminals and SN stations
        # ______________________________________________________________________________________

        ### OBS: SN stations (APs) and the PN terminals (FS rx) are fixed, the R matrices don't change

        pn_term_to_sn_stat_R_matrices = self.sn_conf.methods["correlation_model"].compute_fast_integrals(*self.pn_term_to_sn_stat_r_doas_full[0], pn_panel_N_v, pn_panel_N_v)

        sn_stat_to_pn_term_R_matrices = self.sn_conf.methods["correlation_model"].compute_fast_integrals(*self.sn_stat_to_pn_term_r_doas_full[0], sn_array_N_h, sn_array_N_v)



        # ______________________________________________________________________________________
        # Links between PN stations and SN stations
        # ______________________________________________________________________________________    

        ### OBS: SN stations (APs) and the PN stations (FS tx) are fixed, the R matrices don't change

        pn_stat_to_sn_stat_R_matrices = self.sn_conf.methods["correlation_model"].compute_fast_integrals(*self.pn_stat_to_sn_stat_r_doas_full[0], pn_array_N_h, pn_array_N_v)

        sn_stat_to_pn_stat_R_matrices = self.sn_conf.methods["correlation_model"].compute_fast_integrals(*self.sn_stat_to_pn_stat_r_doas_full[0], sn_array_N_h, sn_array_N_v)


        for ite in range(self.num_snapshots):

            # ___________________________________________
            # Links between PN terminals and SN terminals
            # ___________________________________________    

            pn_term_to_sn_term_R_matrices = self.sn_conf.methods["correlation_model"].compute_fast_integrals(*self.pn_term_to_sn_term_r_doas_full[ite], pn_panel_N_v, pn_panel_N_v)

            sn_term_to_pn_term_R_matrices = self.sn_conf.methods["correlation_model"].compute_fast_integrals(*self.sn_term_to_pn_term_r_doas_full[ite], sn_panel_N_h, sn_panel_N_v)

            pn_term_to_sn_term_R_matrices_full[ite] = pn_term_to_sn_term_R_matrices
            sn_term_to_pn_term_R_matrices_full[ite] = sn_term_to_pn_term_R_matrices


            ### OBS: SN stations (APs) and the PN terminals (FS rx) are fixed, the R matrices don't change
            pn_term_to_sn_stat_R_matrices_full[ite] = pn_term_to_sn_stat_R_matrices
            sn_stat_to_pn_term_R_matrices_full[ite] = sn_stat_to_pn_term_R_matrices

            ### OBS: SN stations (APs) and the PN stations (FS tx) are fixed, the R matrices don't change
            pn_stat_to_sn_stat_R_matrices_full[ite] = pn_stat_to_sn_stat_R_matrices
            sn_stat_to_pn_stat_R_matrices_full[ite] = sn_stat_to_pn_stat_R_matrices


        self.pn_term_to_sn_term_R_matrices_full = pn_term_to_sn_term_R_matrices_full
        self.sn_term_to_pn_term_R_matrices_full = sn_term_to_pn_term_R_matrices_full

        self.pn_term_to_sn_stat_R_matrices_full = pn_term_to_sn_stat_R_matrices_full
        self.sn_stat_to_pn_term_R_matrices_full = sn_stat_to_pn_term_R_matrices_full

        self.pn_stat_to_sn_stat_R_matrices_full = pn_stat_to_sn_stat_R_matrices_full
        self.sn_stat_to_pn_stat_R_matrices_full = sn_stat_to_pn_stat_R_matrices_full

        path = '/home/samuelserejosilva/Projetos/sim_scenario/scenarios_storage/InterNetwork/R_matrices/'

        np.savez(path + 'pn_term_sn_term_R_matrices_full', pn_term_sn_term_R_matrices = self.pn_term_to_sn_term_R_matrices_full)
        np.savez(path + 'sn_term_pn_term_R_matrices_full', sn_term_pn_term_R_matrices = self.sn_term_to_pn_term_R_matrices_full)

        np.savez(path + 'pn_term_sn_stat_R_matrices_full', pn_term_sn_stat_R_matrices = self.pn_term_to_sn_stat_R_matrices_full)
        np.savez(path + 'sn_stat_pn_term_R_matrices_full', sn_stat_pn_term_R_matrices = self.sn_stat_to_pn_term_R_matrices_full)

        np.savez(path + 'pn_stat_sn_stat_R_matrices_full', pn_stat_sn_stat_R_matrices = self.pn_stat_to_sn_stat_R_matrices_full)
        np.savez(path + 'sn_stat_pn_stat_R_matrices_full', sn_stat_pn_stat_R_matrices = self.sn_stat_to_pn_stat_R_matrices_full)




    def generate_channels(self, rng):

        """
        
        Generate the channel coefficients for internetwork links.
        The coefficients are generated for each snapshot and stored in arrays for later use.
        
        """

        pn_panel_N_h = 1
        pn_panel_N_v = 1

        pn_array_N_h = 1
        pn_array_N_v = 1

        sn_panel_N_h = self.sn_conf.panel_N_h
        sn_panel_N_v = self.sn_conf.panel_N_v

        sn_array_N_h = self.sn_conf.array_N_h
        sn_array_N_v = self.sn_conf.array_N_v

        # ___________________________________________
        # Links between PN terminals and SN terminals
        # ___________________________________________  

        pn_term_sn_term_H_full = np.empty(self.num_snapshots, dtype=np.ndarray)

        # ___________________________________________
        # Links between PN terminals and SN stations
        # ___________________________________________  

        pn_term_sn_stat_H_full = np.empty(self.num_snapshots, dtype=np.ndarray)
        
        # ___________________________________________
        # Links between PN stations and SN stations
        # ___________________________________________  

        pn_stat_sn_stat_H_full = np.empty(self.num_snapshots, dtype=np.ndarray)


        
        for ite in range(self.num_snapshots):


            # 1. Generate the channel coefficients for the links between PN terminals and SN terminals
            pn_term_sn_term_H = self.pn_conf.methods["channel_model"].generate_multiple_channels(
                gain_Coefficients = self.pn_term_sn_term_ls_gain_full[ite],
                K_Coefficients = self.pn_term_sn_term_K_full[ite][:, :, np.newaxis, np.newaxis],
                rx_R_Matrixes = self.pn_term_to_sn_term_R_matrices_full[ite],
                tx_R_Matrixes = self.sn_term_to_pn_term_R_matrices_full[ite],
                rx_relative_AoAs_h = self.pn_term_to_sn_term_r_doas_full[ite][0],
                rx_relative_AoAs_v = self.pn_term_to_sn_term_r_doas_full[ite][1],
                tx_relative_AoAs_h = self.sn_term_to_pn_term_r_doas_full[ite][0],
                tx_relative_AoAs_v = self.sn_term_to_pn_term_r_doas_full[ite][1],
                N_h_rx = pn_panel_N_h, N_v_rx = pn_panel_N_v,
                N_h_tx = sn_panel_N_h, N_v_tx = sn_panel_N_v,
                rng = rng
            )
            pn_term_sn_term_H_full[ite] = pn_term_sn_term_H


            # 2. Generate the channel coefficients for the links between PN terminals and SN stations
            pn_term_sn_stat_H = self.pn_conf.methods["channel_model"].generate_multiple_channels(

                gain_Coefficients = self.pn_term_sn_stat_ls_gain_full[ite],
                K_Coefficients = self.pn_term_sn_stat_K_full[ite][:, :, np.newaxis, np.newaxis],
                rx_R_Matrixes = self.pn_term_to_sn_stat_R_matrices_full[ite],
                tx_R_Matrixes = self.sn_stat_to_pn_term_R_matrices_full[ite],
                rx_relative_AoAs_h = self.pn_term_to_sn_stat_r_doas_full[ite][0],
                rx_relative_AoAs_v = self.pn_term_to_sn_stat_r_doas_full[ite][1],
                tx_relative_AoAs_h = self.sn_stat_to_pn_term_r_doas_full[ite][0],
                tx_relative_AoAs_v = self.sn_stat_to_pn_term_r_doas_full[ite][1],
                N_h_rx = pn_panel_N_h, N_v_rx = pn_panel_N_v,
                N_h_tx = sn_array_N_h, N_v_tx = sn_array_N_v,
                rng = rng
            )
            pn_term_sn_stat_H_full[ite] = pn_term_sn_stat_H


            # 3. Generate the channel coefficients for the links between PN stations and SN stations

            pn_stat_sn_stat_H = self.pn_conf.methods["channel_model"].generate_multiple_channels(
                gain_Coefficients = self.pn_stat_sn_stat_ls_gain_full[ite],
                K_Coefficients = self.pn_stat_sn_stat_K_full[ite][:, :, np.newaxis, np.newaxis],
                rx_R_Matrixes = self.pn_stat_to_sn_stat_R_matrices_full[ite],
                tx_R_Matrixes = self.sn_stat_to_pn_stat_R_matrices_full[ite],
                rx_relative_AoAs_h = self.pn_stat_to_sn_stat_r_doas_full[ite][0],
                rx_relative_AoAs_v = self.pn_stat_to_sn_stat_r_doas_full[ite][1],
                tx_relative_AoAs_h = self.sn_stat_to_pn_stat_r_doas_full[ite][0],
                tx_relative_AoAs_v = self.sn_stat_to_pn_stat_r_doas_full[ite][1],
                N_h_rx = pn_array_N_h, N_v_rx = pn_array_N_v,
                N_h_tx = sn_array_N_h, N_v_tx = sn_array_N_v,
                rng = rng
            )

            pn_stat_sn_stat_H_full[ite] = pn_stat_sn_stat_H



        self.pn_term_sn_term_H_full = pn_term_sn_term_H_full
        self.pn_term_sn_stat_H_full = pn_term_sn_stat_H_full
        self.pn_stat_sn_stat_H_full = pn_stat_sn_stat_H_full

        path = '/home/samuelserejosilva/Projetos/sim_scenario/scenarios_storage/InterNetwork/H_coeffs/'

        np.savez(path + 'pn_term_sn_term_H_full.npz', pn_term_sn_term_H = self.pn_term_sn_term_H_full)
        np.savez(path + 'pn_term_sn_stat_H_full.npz', pn_term_sn_stat_H = self.pn_term_sn_stat_H_full)
        np.savez(path + 'pn_stat_sn_stat_H_full.npz', pn_stat_sn_stat_H = self.pn_stat_sn_stat_H_full)



            






            



