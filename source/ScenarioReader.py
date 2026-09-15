import numpy as np

from source.LoadMethods import MethodLoader

from dataclasses import dataclass

from source.NetworkConfig import DMimoConfig, FixedServiceConfig


@dataclass
class PanelSelectionContext:

    """
    This is a data class 
        
    """
    # OBS: The difference between ls_fading and ls_gain is that ls_gain takes into account the antenna gains!
    # OBS: "term" is the abbreviation of terminal
    # OBS: "inter_net" means -> Ex: between PN terminals and SN terminals
    # OBS: "intra_net" means -> Ex: between elements of PN or between elements of SN

    # 1. Inter network large scale gain coeffs (PN - SN)
    inter_net_ls_gain: np.ndarray
    # 2. Intra network large scale gain coeffs (SN)
    intra_net_ls_gain: np.ndarray
    # 3. Inter network channel coeffs (PN - SN)
    inter_net_channel: np.ndarray
    # 4. Intra network channel coeffs (SN)
    intra_net_channel: np.ndarray
    # 5. Pre-scheduled terminals (SN)
    scheduled_term: np.ndarray
    # 6. Number of terminals (own network)
    num_term: int
    # 7. Number of panels per terminal (own network)
    num_panels: int
    # 8. Random number generator
    rng: np.random.Generator


@dataclass 
class TerminalSchedulingContext:

    """
    This is a data class 
    
    """

    # OBS: The difference between ls_fading and ls_gain is that ls_gain takes into account the antenna gains!
    # OBS: "term" is the abbreviation of terminal
    # OBS: "inter_net" means that ...

    # 1. Inter network large scale fading coefficients
    inter_net_ls_fading: np.ndarray
    # 2. Inter network large scale gain coefficients
    inter_net_ls_gain: np.ndarray
    # 3. Inter network channel coefficients
    inter_net_channel: np.ndarray
    # 4. Vector containing the indexes of the panels selected by each terminal
    term_sel_panels: np.ndarray
    # 5. Scheduling threshold
    threshold: float
    # 6. Terminals maximum transmission power 
    term_max_p: float
    # 7. Terminals maximum antenna gain
    term_max_ant_gain: float
    # 8. Terminals minimum antenna gain
    term_min_ant_gain: float
    # 9. PN noise variance
    n_var: float

@dataclass
class StationSchedulingContext:
    inter_network_lsg: np.ndarray
    inter_network_channel: np.ndarray
    scheduling_threshold: float
    station_max_power: float
    pn_noise_variance: float


class SchedulingManager:
 
    def __init__(self, config):
        self._config = config
        self._panel_selection_technique = None

        # Terminal scheduling
        self._terminal_scheduling_technique   = None
        self._terminal_scheduling_method_name = None
        self._terminal_scheduling_threshold   = None

        # Station scheduling
        self._station_scheduling_technique   = None
        self._station_scheduling_method_name = None
        self._station_scheduling_threshold   = None
 

    def set_panel_selection_technique(self, module_path: str, class_name: str) -> None:
        self._panel_selection_technique = MethodLoader.load(module_path, class_name)

    def set_terminal_scheduling_technique(self, module_path: str, class_name: str, method_name: str, threshold: float) -> None:
        self._terminal_scheduling_technique = MethodLoader.load(module_path, class_name)
        self._terminal_scheduling_method_name = method_name
        self._terminal_scheduling_threshold = threshold

    def set_station_scheduling_technique(self, module_path: str, class_name: str, method_name: str, threshold: float) -> None:
        self._station_scheduling_technique = MethodLoader.load(module_path, class_name)
        self._station_scheduling_method_name = method_name
        self._station_scheduling_threshold = threshold



 
    def select_terminal_panels(self, 
        inter_net_ls_gain, intra_net_ls_gain, inter_net_channel, intra_net_channel,
        scheduled_terminals, 
        num_terminals, rng,
        method_name) -> np.ndarray:

        """
        
        """

        context = PanelSelectionContext(
            inter_net_ls_gain     = inter_net_ls_gain,
            intra_net_ls_gain     = intra_net_ls_gain,
            inter_net_channel   = inter_net_channel,
            intra_net_channel   = intra_net_channel,
            num_term            = num_terminals,
            num_panels          = self._config.num_panels,
            scheduled_term      = scheduled_terminals,
            rng = rng
        )
        print(context.scheduled_term)

        method_to_call = getattr(self._panel_selection_technique, method_name)
        
        sel_panels = method_to_call(context)

        return sel_panels

 
    def schedule_terminals(self, 
                           inter_net_ls_fading, inter_net_ls_gain, inter_net_channel, 
                           term_sel_panels, 
                            term_max_p, term_max_ant_gain, term_min_ant_gain, pn_n_var) -> np.ndarray:

        """
        
        """
        
        context = TerminalSchedulingContext(
            inter_net_ls_fading = inter_net_ls_fading,
            inter_net_ls_gain   = inter_net_ls_gain,
            inter_net_channel   = inter_net_channel,

            term_sel_panels = term_sel_panels,
            threshold = self._terminal_scheduling_threshold,

            term_max_p = term_max_p,
            term_max_ant_gain = term_max_ant_gain,
            term_min_ant_gain = term_min_ant_gain,

            n_var = pn_n_var
        )

        #getattr

        method_to_call = getattr(self._terminal_scheduling_technique, self._terminal_scheduling_method_name)

        scheduled_ues = method_to_call(context)

        return scheduled_ues



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

    # OBS: Since these variables refer to the links between elements of two networks, we can assume that they store multiple coefficients;
    #      So, there is no need for a header saying "coeffs" of "coefficients".

    pn_term_sn_term_ls_fading: np.ndarray
    pn_term_sn_stat_ls_fading: np.ndarray
    pn_stat_sn_stat_ls_fading: np.ndarray

    pn_term_sn_term_ls_gain: np.ndarray
    pn_term_sn_stat_ls_gain: np.ndarray
    pn_stat_sn_stat_ls_gain: np.ndarray

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

    # OBS: Since these variables refer to the links between elements of the same networks, we can conclude that it is important to
    #      have a header saying "coeffs", "coefficients" or something like that.

    ls_gain_coeffs: np.ndarray
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

    
    def set_terminal_scheduling_technique(self, path, class_name, method_name, thresh):
        self._scheduling.set_terminal_scheduling_technique(path, class_name, method_name, thresh)

    def set_station_scheduling_technique(self, path, class_name, thresh):
        self._scheduling.set_station_scheduling_technique(path, class_name, thresh)

    def set_panel_selection_technique(self, path, class_name):
        self._scheduling.set_panel_selection_technique(path, class_name)

    
    def compute_uplink_kpis_for_panel_selection_first(self, ite: int):

        # When the SN is in uplink -> UEs scheduling

        # 1. SN performing UE panel selection
        tps_method_name = "perform_as_first_step"
        ues_panels = self._scheduling.select_terminal_panels(
            inter_net_ls_gain   = self.cross_channels.pn_term_sn_term_ls_gain[ite],
            intra_net_ls_gain   = self.sn_geometry.ls_gain_coeffs[ite],
            inter_net_channel   = self.cross_channels.pn_term_sn_term_H[ite],
            intra_net_channel   = self.sn_geometry.H_coeffs[ite],
            scheduled_terminals = None, 
            num_terminals       = self.sn_config.num_terminals,
            rng                 = self.rng,
            method_name         = tps_method_name
        )

        # 1. SN performing UE scheduling to avoid interfering too much 
        scheduled_ues = self._scheduling.schedule_terminals(
            inter_net_ls_fading = self.cross_channels.pn_term_sn_term_ls_fading[ite],                   
            inter_net_ls_gain   = self.cross_channels.pn_term_sn_term_ls_gain[ite], 
            inter_net_channel   = self.cross_channels.pn_term_sn_term_H[ite], 
            term_sel_panels     = ues_panels, 
            term_max_p          = self.sn_config.terminal_max_power,
            term_max_ant_gain   = self.sn_config.methods["terminal_antenna_gain"].g_max,
            term_min_ant_gain   = self.sn_config.methods["terminal_antenna_gain"].g_max - self.sn_config.methods["terminal_antenna_gain"].am,
            pn_n_var            = self.pn_config.noise_variance,
        )

        # SN performing channel estimation considering all UEs
        (
        H_hat_coeffs, 
        C_error_matrices)= self.sn_config.methods["channel_estimation"].compute(
            H_coeffs    = self.sn_geometry.H_coeffs[ite],
            R_matrices = self.sn_geometry.R_matrices[ite],
            sel_panels     = ues_panels,
            scheduled_ues = scheduled_ues,
            tau_p = self.sn_config.num_pilot_sequences,
            ul_max_power = self.sn_config.terminal_max_power,
            noise_var = self.sn_config.noise_variance
        )

        from source.utils import lin2db

        # All APs serve all UEs
        L = self.sn_config.num_stations * self.sn_config.num_arrays
        clustering_matrix = np.ones((self.sn_config.num_terminals, L))


        # SN computing the uplink combiners
        sn_ul_combiners = self._signal_processor.compute_uplink_combiners(
            H_hat_coeffs      = H_hat_coeffs,
            C_error_hat  = C_error_matrices,
            D_clustering = clustering_matrix,
            scheduled_term     = scheduled_ues,
            ul_max_p      = self.sn_config.terminal_max_power,
            n_var         = self.sn_config.noise_variance
            )

        # PN dl (terminal) combiners
        pn_combining = np.ones((self.pn_config.num_terminals, 1))


        # Computing SN spectral efficiencies and the caused interference to the PN
        (
        sn_ul_spec_effs, 
        sn_ul_caused_inr_by_all_ues) = self._kpi_calculator.compute_uplink_kpis(
            sn_H              = self.sn_geometry.H_coeffs[ite], 
            pn_term_sn_term_H = self.cross_channels.pn_term_sn_term_H[ite], 
            pn_stat_sn_stat_H = self.cross_channels.pn_stat_sn_stat_H[ite],
            clustering        = clustering_matrix, 
            sn_sched_term     = scheduled_ues, 
            sn_sel_panels     = ues_panels, 
            sn_ul_combining   = sn_ul_combiners, 
            pn_term_combining = pn_combining, 
            sn_term_max_power = self.sn_config.terminal_max_power, 
            pn_stat_max_power = self.pn_config.station_max_power, 
            rng = self.rng
            )

        sn_ul_caused_inr_by_all_ues = lin2db(sn_ul_caused_inr_by_all_ues[0])

        return (
            sn_ul_caused_inr_by_all_ues, 
            len(scheduled_ues), 
            np.sum(sn_ul_spec_effs) 

            )
        
      


    def compute_uplink_kpis_for_scheduling_first(self, ite: int):

        """
        
        Consider that the UEs scheduling is performed before the panel selection

        """

        # 1. SN performing UE scheduling to avoid interfering too much 
        scheduled_ues = self._scheduling.schedule_terminals(
            inter_net_ls_fading = self.cross_channels.pn_term_sn_term_ls_fading[ite],                   
            inter_net_ls_gain   = self.cross_channels.pn_term_sn_term_ls_gain[ite], 
            inter_net_channel   = self.cross_channels.pn_term_sn_term_H[ite], 
            term_sel_panels     = None, 
            term_max_p          = self.sn_config.terminal_max_power,
            term_max_ant_gain   = self.sn_config.methods["terminal_antenna_gain"].g_max,
            term_min_ant_gain   = self.sn_config.methods["terminal_antenna_gain"].g_max - self.sn_config.methods["terminal_antenna_gain"].am,
            pn_n_var            = self.pn_config.noise_variance,
        )

        # Terminal panel selection techniques names
        tps_method_name = "perform_as_second_step"

        # 2. SN performing UE panel selection
        ues_panels = self._scheduling.select_terminal_panels(
            inter_net_ls_gain   = self.cross_channels.pn_term_sn_term_ls_gain[ite],
            intra_net_ls_gain   = self.sn_geometry.ls_gain_coeffs[ite],
            inter_net_channel   = self.cross_channels.pn_term_sn_term_H[ite],
            intra_net_channel   = self.sn_geometry.H_coeffs[ite],
            scheduled_terminals = scheduled_ues, 
            num_terminals       = self.sn_config.num_terminals,
            rng                 = self.rng,
            method_name         = tps_method_name
        )

        print("Paineis dos UEs: ", ues_panels)

        from source.utils import lin2db, db2lin

        # SN performing channel estimation considering all UEs
        (
        H_hat_coeffs, 
        C_error_matrices)= self.sn_config.methods["channel_estimation"].compute(
            H_coeffs        = self.sn_geometry.H_coeffs[ite],
            R_matrices      = self.sn_geometry.R_matrices[ite],
            sel_panels      = ues_panels,
            scheduled_ues   = scheduled_ues,
            tau_p           = self.sn_config.num_pilot_sequences,
            ul_max_power    = self.sn_config.terminal_max_power,
            noise_var       = self.sn_config.noise_variance
        )

        # All APs serve all UEs
        L = self.sn_config.num_stations * self.sn_config.num_arrays
        clustering_matrix = np.ones((self.sn_config.num_terminals, L))


        # SN computing the uplink combiners
        sn_ul_combiners = self._signal_processor.compute_uplink_combiners(
            H_hat_coeffs      = H_hat_coeffs,
            C_error_hat  = C_error_matrices,
            D_clustering = clustering_matrix,
            scheduled_term     = scheduled_ues,
            ul_max_p      = self.sn_config.terminal_max_power,
            n_var         = self.sn_config.noise_variance
            )

        # PN dl (terminal) combiners
        pn_combining = np.ones((self.pn_config.num_terminals, 1))


        # Computing SN spectral efficiencies and the caused interference to the PN
        (
        sn_ul_spec_effs, 
        sn_ul_caused_inr_by_all_ues) = self._kpi_calculator.compute_uplink_kpis(
            sn_H              = self.sn_geometry.H_coeffs[ite], 
            pn_term_sn_term_H = self.cross_channels.pn_term_sn_term_H[ite], 
            pn_stat_sn_stat_H = self.cross_channels.pn_stat_sn_stat_H[ite],
            clustering        = clustering_matrix, 
            sn_sched_term     = scheduled_ues, 
            sn_sel_panels     = ues_panels, 
            sn_ul_combining   = sn_ul_combiners, 
            pn_term_combining = pn_combining, 
            sn_term_max_power = self.sn_config.terminal_max_power, 
            pn_stat_max_power = self.pn_config.station_max_power, 
            rng = self.rng
            )

        sn_ul_caused_inr_by_all_ues = lin2db(sn_ul_caused_inr_by_all_ues[0])

        return (
            sn_ul_caused_inr_by_all_ues, 
            len(scheduled_ues), 
            np.sum(sn_ul_spec_effs) 

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
        
