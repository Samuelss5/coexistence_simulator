import numpy as np

from source.signal import DMimoInternalSignals

class SignalProcessor:
 
    def __init__(self, config):
        self._num_terminals = config.num_terminals
        self._num_stations  = config.num_stations
        self._num_arrays    = config.num_arrays
        self._combining = config.methods["stations_combining"]
        self._beamforming = config.methods["stations_beamforming"]
 
    def compute_uplink_combiners(self, 
                                 H_hat_coeffs, C_error_hat, D_clustering,
                                 scheduled_term,
                                 ul_max_p, n_var) -> np.ndarray:

        # When the DMimo network is in uplink there is no need to cluster the network

        ul_combiners = self._combining.compute(
            H_hat_coeffs, C_error_hat, D_clustering,
            scheduled_term,
            ul_max_p, n_var
        )

        return ul_combiners
        
 
    def compute_downlink_precoders(self, estimated_channel, scheduled_terminals,
                                    channel_error, clustering_matrix,
                                    terminals_max_power, stations_max_power,
                                    noise_variance) -> np.ndarray:
        return self._beamforming.compute(
            estimated_channel, scheduled_terminals, channel_error,
            clustering_matrix, terminals_max_power, stations_max_power,
            noise_variance,
        )


class KpiCalculator:



    def __init__(self, pn_noise_variance: float, sn_noise_variance: float):
        self._pn_noise_variance = pn_noise_variance
        self._sn_noise_variance = sn_noise_variance



        
    def compute_sn_uplink_caused_inr(self, 
                        pn_term_sn_term_H, sn_sched_term, sn_sel_panels, 
                        pn_term_combining, sn_term_max_power
                        ) -> np.ndarray:

        """
        Computes the interference to noise ratio that the SN's uplink causes to the PN
        """


        if len(sn_sched_term) > 0:

            from source.signal import InterNetInterf

            pn_panels_idxs = np.zeros(pn_term_sn_term_H.shape[0], dtype=int)

            # Channel coefficients: PN terminals <-> SN terminals
            #H_term_term = pn_term_sn_term_H[:, sn_sched_term, pn_panels_idxs, sn_sel_panels[sn_sched_term], :]
            
            interference = InterNetInterf.uplink_to_downlink(
                pn_term_sn_term_H,
                sn_sched_term,
                sn_sel_panels,
                sn_term_max_power
            )
            
            inr = interference / self._pn_noise_variance


        else: 

            inr = np.zeros(pn_term_sn_term_H.shape[0], dtype=float)

        return inr



    def compute_sn_uplink_spectral_efficiency(self,
                        sn_H, pn_stat_sn_stat_H,
                        clustering, sn_sched_term, sn_sel_panels, sn_ul_combining,
                        sn_term_max_power, pn_stat_max_power, rng
                        ):



        # 1. Desired signal component
        ul_signals = DMimoInternalSignals.uplink_target_signal(
            sn_H, clustering, sn_sched_term, sn_sel_panels, sn_ul_combining, sn_term_max_power
        )

        # 2. Interference signals component
        ul_intranet_interf = DMimoInternalSignals.uplink_intra_interference(
            sn_H, clustering, sn_sched_term, sn_sel_panels, sn_ul_combining, sn_term_max_power
        )


        # 3. Receiving noise power
        ul_noise = DMimoInternalSignals.uplink_receiving_noise(
            clustering, sn_sched_term, sn_ul_combining, self._sn_noise_variance, rng
        )

        from source.signal import InterNetInterfForDMimo

        # 4. Inter network interference
        ul_internet_interf = InterNetInterfForDMimo.downlink_to_uplink(
            pn_stat_sn_stat_H, 
            clustering, 
            scheduled_ues = sn_sched_term,
            combining_vectors = sn_ul_combining,
            max_dl_power = pn_stat_max_power
        )
        
        #print("ul_noise: ", ul_noise)
        
        #print("ul_signals: ", ul_signals)
        
        #sprint("ul_internet_interf: ", ul_internet_interf)
        
        print("intra interference: ", ul_intranet_interf)
        

        sinrs = ul_signals / (ul_noise + ul_intranet_interf)
        sinrs[np.where(np.isnan(sinrs))[0]] = 0
        
        #print("Sinrs: ", 10*np.log10(sinrs))

        spec_effs = np.log2(1 + sinrs)
        
        print("Soma das SEs: ", np.sum(spec_effs))

        return spec_effs


    def compute_uplink_kpis(self, 
                        sn_H, pn_term_sn_term_H, pn_stat_sn_stat_H,
                        clustering, sn_sched_term, sn_sel_panels, sn_ul_combining, pn_term_combining,
                        sn_term_max_power, pn_stat_max_power, rng
                        ):


        # 1. SN uplink spectral efficiencies (per scheduled UE)
        ul_spec_effs = self.compute_sn_uplink_spectral_efficiency(
            sn_H, pn_stat_sn_stat_H,
            clustering, sn_sched_term, sn_sel_panels, sn_ul_combining,
            sn_term_max_power, pn_stat_max_power, rng
        )

        # 2. Interference to noise ratio caused to the FS receiver
        ul_caused_inr = self.compute_sn_uplink_caused_inr(
            pn_term_sn_term_H, sn_sched_term, sn_sel_panels, pn_term_combining, sn_term_max_power
        )

        return ul_spec_effs, ul_caused_inr


