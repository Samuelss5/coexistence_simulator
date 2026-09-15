import numpy as np

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
        
        from source.signal import UplinkToDownlinkInterference
        interference = UplinkToDownlinkInterference.compute(
            pn_term_sn_term_H, sn_sched_term, sn_sel_panels, 
            pn_term_combining, sn_term_max_power
        )

        inr = interference / self._pn_noise_variance

        return inr



    def compute_sn_uplink_spectral_efficiency(self,
                        sn_H, pn_stat_sn_stat_H,
                        clustering, sn_sched_term, sn_sel_panels, sn_ul_combining,
                        sn_term_max_power, pn_stat_max_power, rng
                        ):

        # 1. Desired signal component
        from source.signal import DMimoUplinkTargetSignal

        target_signals = DMimoUplinkTargetSignal.compute(
            sn_H, clustering, sn_sched_term, sn_sel_panels, sn_ul_combining, sn_term_max_power
        )

        # 2. Interference signals component
        from source.signal import DMimoIntraUplinkInterference

        intra_interference = DMimoIntraUplinkInterference.compute(
            sn_H, clustering, sn_sched_term, sn_sel_panels, sn_ul_combining, sn_term_max_power
        )

        from source.signal import DownlinkToDMimoUplinkInterference

        inter_interference = DownlinkToDMimoUplinkInterference.compute(
            pn_stat_sn_stat_H, clustering, sn_sched_term, sn_ul_combining, pn_stat_max_power
        )

        # 3. Receiving noise power

        from source.signal import DMimoUplinkNoise 

        receiver_noise = DMimoUplinkNoise.compute(
            clustering, sn_sched_term, sn_ul_combining, self._sn_noise_variance, rng
        )

        sinrs = target_signals / (receiver_noise + intra_interference + inter_interference)
        sinrs[np.where(np.isnan(sinrs))[0]] = 0

        spec_effs = np.log2(1 + sinrs)

        return spec_effs


    def compute_uplink_kpis(self, 
                        sn_H, pn_term_sn_term_H, pn_stat_sn_stat_H,
                        clustering, sn_sched_term, sn_sel_panels, sn_ul_combining, pn_term_combining,
                        sn_term_max_power, pn_stat_max_power, rng
                        ):


        ul_spec_effs = self.compute_sn_uplink_spectral_efficiency(
            sn_H, pn_stat_sn_stat_H,
            clustering, sn_sched_term, sn_sel_panels, sn_ul_combining,
            sn_term_max_power, pn_stat_max_power, rng
        )

        ul_caused_inr = self.compute_sn_uplink_caused_inr(
            pn_term_sn_term_H, sn_sched_term, sn_sel_panels, pn_term_combining, sn_term_max_power
        )

        return ul_spec_effs, ul_caused_inr

    # __________
    # DOWNLINK
    # __________

    def compute_sn_downlink_caused_inr(self,
                        pn_term_sn_stat_H, 
                        clustering, sn_dl_beamforming,
                        ):

    
        from source.signal import DMimoDownlinkToDownlinkInterference
        interference = DMimoDownlinkToDownlinkInterference.compute(
            pn_term_sn_stat_H, sn_dl_beamforming
        )

        inr = interference / self._pn_noise_variance

        return inr

    def compute_sn_downlink_spectral_efficiency(self,
                        sn_H, pn_stat_sn_term_H,
                        clustering, sn_sel_panels, sn_dl_beamforming,
                        pn_stat_max_power, rng
                        ):
        
        # 1. Desired signal component
        from source.signal import DMimoDownlinkTargetSignal

        target_signals = DMimoDownlinkTargetSignal.compute(
            sn_H, clustering, sn_sel_panels, sn_dl_beamforming
        )


        # 2. Interference signals component
        from source.signal import DMimoIntraDownlinkInterference

        intra_interference = DMimoIntraDownlinkInterference.compute(
            sn_H, clustering, sn_sel_panels, sn_dl_beamforming
        )


        from source.signal import FsDownlinkToDMimoDownlinkInterference
        inter_interference = FsDownlinkToDMimoDownlinkInterference.compute(
            sn_H, sn_sel_panels, pn_stat_max_power
        )

        from source.signal import DownlinkNoise
        num_sn_terminals, _, _, _,sn_term_N, _ = sn_H.shape[0]
        receiver_noise = DownlinkNoise.compute(
            num_sn_terminals, sn_term_N, self._sn_noise_variance, rng
        )

        sinrs = target_signals / (receiver_noise + intra_interference + inter_interference)
        sinrs[np.where(np.isnan(sinrs))[0]] = 0

        spec_effs = np.log2(1 + sinrs)

        return spec_effs


    def compute_downlink_kpis(self,
                        sn_H, pn_term_sn_stat_H, pn_stat_sn_term_H, 
                        clustering, sn_sel_panels, sn_dl_beamforming, pn_stat_beamforming,
                        sn_stat_max_power, pn_stat_max_power, rng
                        ):


        dl_spec_effs = self.compute_sn_downlink_spectral_efficiency(
            sn_H, sn_sel_panels, sn_dl_beamforming, pn_stat_max_power, rng
        )

        dl_caused_inr = self.compute_sn_downlink_caused_inr(
            pn_term_sn_stat_H, clustering, sn_dl_beamforming,
        )
        

