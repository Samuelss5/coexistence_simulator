import numpy as np

from source.LoadMethods import MethodLoader

from dataclasses import dataclass

from source.NetworkConfig import DMimoConfig, FixedServiceConfig


@dataclass
class PanelSelectionContext:
    inter_network_gains: np.ndarray
    intra_network_gains: np.ndarray
    inter_network_channel: np.ndarray
    intra_network_channel: np.ndarray
    num_terminals: int
    num_panels: int
    rng: np.random.Generator


@dataclass 
class TerminalSchedulingContext:
    inter_network_lsf: np.ndarray
    inter_network_lsg: np.ndarray
    inter_network_channel: np.ndarray
    terminal_panels: np.ndarray
    scheduling_threshold: float
    terminal_max_power: float
    terminal_max_antenna_gain: float
    pn_noise_variance: float

@dataclass
class StationSchedulingContext:
    inter_network_lsg: np.ndarray
    inter_network_channel: np.ndarray
    scheduling_threshold: float
    station_max_power: float
    pn_noise_variance: float


class SchedulingManager:
 
    def __init__(self, config: NetworkConfig):
        self._config = config
        self._panel_selection_technique = None

        # Terminal scheduling
        self._terminal_scheduling_technique = None
        self._terminal_scheduling_threshold = None

        # Station scheduling
        self._station_scheduling_technique = None
        self._station_scheduling_threshold = None
 

    def set_panel_selection_technique(self, module_path: str, class_name: str) -> None:
        self._panel_selection_technique = MethodLoader.load(module_path, class_name)

    def set_terminal_scheduling_technique(self, module_path: str, class_name: str, threshold: float) -> None:
        self._terminal_scheduling_technique = MethodLoader.load(module_path, class_name)
        self._terminal_scheduling_threshold = threshold

    def set_station_scheduling_technique(self, module_path: str, class_name: str, threshold: float) -> None:
        self._station_scheduling_technique = MethodLoader.load(module_path, class_name)
        self._station_scheduling_threshold = threshold
 
    def select_terminal_panels(self, 
        inter_network_gains, intra_network_gains, inter_network_channel, intra_network_channel,
        num_terminals, rng) -> np.ndarray:

        context = PanelSelectionContext(
            inter_network_gains = inter_network_gains,
            intra_network_gains = intra_network_gains,
            inter_network_channel = inter_network_channel,
            intra_network_channel = intra_network_channel,
            num_terminals = num_terminals,
            num_panels  = self._config.num_panels,
            rng = rng
        )
        return self._panel_selection_technique.perform(context)

 
    def schedule_terminals(self, 
        inter_network_lsf,                   
        inter_network_lsg, 
        inter_network_channel, 

        terminal_panels, 

        terminal_max_power, 
        terminal_max_antenna_gain,
        pn_noise_variance) -> np.ndarray:

        
        context = TerminalSchedulingContext(
            inter_network_lsf = inter_network_lsf,
            inter_network_lsg = inter_network_lsg,
            inter_network_channel = inter_network_channel,

            terminal_panels = terminal_panels,
            scheduling_threshold = self._terminal_scheduling_threshold,

            terminal_max_power = terminal_max_power,
            terminal_max_antenna_gain = ,

            pn_noise_variance = pn_noise_variance
        )

        a = self._terminal_scheduling_technique.perform_as_second_step(context)
        
        return self._terminal_scheduling_technique.perform(context)


    def schedule_stations(self,
        inter_network_lsg, inter_network_channel, 
        station_max_power, pn_noise_variance) -> np.ndarray:

        context = StationSchedulingContext(
            inter_network_lsg = inter_network_lsg,
            inter_network_channel = inter_network_channel,
            scheduling_threshold = self._station_scheduling_threshold,
            station_max_power = station_max_power,
            pn_noise_variance = pn_noise_variance
        )

        return self._station_scheduling_technique.perform(context)






@dataclass
class CrossChannels:

    pn_term_sn_term_lsf: np.ndarray
    pn_term_sn_stat_lsf: np.ndarray
    pn_stat_sn_stat_lsf: np.ndarray

    pn_term_sn_term_gain: np.ndarray
    pn_term_sn_stat_gain: np.ndarray
    pn_stat_sn_stat_gain: np.ndarray

    pn_term_sn_term_K: np.ndarray
    pn_term_sn_stat_K: np.ndarray
    pn_stat_sn_stat_K: np.ndarray

    pn_term_sn_term_H: np.ndarray
    pn_term_sn_stat_H: np.ndarray
    pn_stat_sn_stat_H: np.ndarray

    @classmethod
    def read(cls, list):
        return cls(*list)


@dataclass
class InterGeometry:
    pn_term_sn_term_lsg_coeffs: np.ndarray

@dataclass 
class IntraGeometry:
    lsg_coeffs: np.ndarray
    R_matrices: np.ndarray
    H_coeffs: np.ndarray

    @classmethod
    def read(cls, list):
        return cls(*list)

class ScenarioReader:

    def __init__(self, pn_config, sn_config):
        self.pn_config = FixedServiceConfig.read(pn_config)
        self.sn_config = DMimoConfig.read(sn_config)
        self._scheduling = SchedulingManager(self.sn_config)

        self.pn_geometry = None
        self.sn_geometry = None
        self.cross_channels = None

        from source.kpis import SignalProcessor, KpiCalculator

        self._signal_processor = SignalProcessor(self.sn_config)
        self._kpi_calculator = KpiCalculator(self.pn_config.noise_variance, self.sn_config.noise_variance)

        self.rng = np.random.default_rng(seed=42)


    def set_cross_channels(self, list):
        self.cross_channels = CrossChannels.read(list)

    def set_geometry(self, list):
        self.sn_geometry = IntraGeometry.read(list)

    
    def set_terminal_scheduling_technique(self, path, class_name, thresh):
        self._scheduling.set_terminal_scheduling_technique(path, class_name, thresh)

    def set_station_scheduling_technique(self, path, class_name, thresh):
        self._scheduling.set_station_scheduling_technique(path, class_name, thresh)

    def set_panel_selection_technique(self, path, class_name):
        self._scheduling.set_panel_selection_technique(path, class_name)

    
    def compute_uplink_kpis_for_panel_selection_and_scheduling(self, ite: int):

        # When the SN is in uplink -> UEs scheduling

        # 1. UEs panel selection
        selected_panels = self._scheduling.select_terminal_panels(
            inter_network_gains = self.cross_channels.pn_term_sn_term_lsg[ite],
            intra_network_gains = self.sn_geometry.lsg_coeffs[ite],
            inter_network_channel = self.cross_channels.pn_term_sn_term_H[ite],
            intra_network_channel = self.sn_geometry.H_coeffs[ite],
            num_terminals = self.sn_config.num_terminals,
            rng = self.rng)



        scheduled_terminals = self._scheduling.schedule_terminals(
            inter_network_lsg = self.cross_channels.pn_term_sn_term_lsg[ite],
            inter_network_channel = self.cross_channels.pn_term_sn_term_H[ite],
            terminal_panels = selected_panels,
            terminal_max_power = self.sn_config.terminal_max_power,
            pn_noise_variance  = self.pn_config.noise_variance
        )




        from source.utils import lin2db, db2lin

        # SN performing channel estimation considering all UEs
        H_est, C_error = self.sn_config.methods["channel_estimation"].compute(
            self.sn_geometry.H_coeffs[ite], self.sn_geometry.R_matrices[ite], selected_panels, scheduled_terminals,
            self.sn_config.num_pilot_sequences, self.sn_config.terminal_max_power, self.sn_config.noise_variance
        )

        # All APs serve all UEs
        L = self.sn_config.num_stations * self.sn_config.num_arrays
        clustering_matrix = np.ones((self.sn_config.num_terminals, L))

        sn_combiners = self._signal_processor.compute_uplink_combiners(
            H_est, scheduled_terminals, C_error, clustering_matrix, self.sn_config.terminal_max_power, self.sn_config.noise_variance 
        )

        pn_combining = np.ones((self.pn_config.num_terminals, 1))



        # Computing the SEs and INR level
        sn_ul_spec_effs, sn_ul_caused_inr_by_all_ues = self._kpi_calculator.compute_uplink_kpis(
            self.sn_geometry.H_coeffs[ite], self.cross_channels.pn_term_sn_term_H[ite], self.cross_channels.pn_stat_sn_stat_H[ite],
            clustering_matrix, scheduled_terminals, selected_panels, sn_combiners, pn_combining, 
            self.sn_config.terminal_max_power, self.pn_config.station_max_power, self.rng
                    )

        sn_ul_caused_inr_by_all_ues        = lin2db(sn_ul_caused_inr_by_all_ues[0])




        return (
            sn_ul_caused_inr_by_all_ues, 
            len(scheduled_terminals), 
            np.sum(sn_ul_spec_effs) 

            )


    def compute_uplink_kpis_for_scheduling_first(self, ite: int):

        """
        
        Consider that the UEs scheduling is performed before the panel selection

        """


        scheduled_ues = self._scheduling.schedule_terminals(
            inter_network_lsf = self.cross_channels.,                   
            inter_network_lsg, 
            inter_network_channel, 
                    
                            terminal_panels, 
                    
                            terminal_max_power, 
                            terminal_max_antenna_gain,
                            pn_noise_variance
        )





    def compute_downlink_kpis(self, ite: int):

        scheduled_stations = self._scheduling.schedule_stations(
            inter_network_lsg = self.cross_channels.pn_term_sn_stat_lsg[ite], 
            inter_network_channel = self.cross_channels.pn_term_sn_stat_H[ite],
            station_max_power    = self.sn_config.station_max_power,
            pn_noise_variance    = self.pn_config.noise_variance
        )

        scheduled_terminals = np.arange(0, self.sn_config.num_terminals)

        selected_panels     = 0

        H_est, C_error = self.sn_config.methods["channel_estimation"].compute(
            self.sn_geometry.H_coeffs[ite], self.sn_geometry.R_matrices[ite], selected_panels, scheduled_terminals,
            self.sn_config.num_pilot_sequences, self.sn_config.terminal_max_power, self.sn_config.noise_variance
        )

        # Total number of arrays 
        L = self.sn_config.num_stations * self.sn_config.num_arrays
        clustering_matrix = np.zeros((self.sn_config.num_terminals, L))

        clustering_matrix[:, scheduled_stations] = 1

        

        sn_dl_precoders = self._signal_processor.compute_downlink_precoders(

        )

    def compute_Monte_Carlo_kpis(self, ite: int):


        #self.compute_uplink_kpis(ite)

        self.compute_downlink_kpis(ite)
        
