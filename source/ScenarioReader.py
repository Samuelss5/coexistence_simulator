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


    """
    
    This class is responsible for panel selection and scheduling.

    In order to carry out its respective functions, it needs to know which methods will be used; 
    these are stored as attributes of the class.
    
    """

 
    def __init__(self, config):
        self._config = config


        # --- Terminal panel selection --- #
        self._panel_selection_technique = None

        # --- Terminal scheduling --- #
        self._terminal_scheduling_technique   = None
        self._terminal_scheduling_threshold   = None

 
    def set_panel_selection_technique(self, module_path: str, class_name: str) -> None:
        """
        This function changes the panel selection method to be used
        """
        self._panel_selection_technique = MethodLoader.load(module_path, class_name)

    def set_terminal_scheduling_technique(self, module_path: str, class_name: str, threshold: float) -> None:
        """
        This function changes the scheduling method to be used
        """
        self._terminal_scheduling_technique = MethodLoader.load(module_path, class_name)
        self._terminal_scheduling_threshold = threshold


 
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


        method_name = "perform"

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

        method_name = "perform"

        method_to_call = getattr(self._terminal_scheduling_technique, method_name)

        scheduled_ues = method_to_call(context)

        return scheduled_ues




@dataclass
class CrossChannels:

    """
    This is a data class designed to store channel parameters between elements of two different networks.
    """

    # OBS: Since these variables refer to the links between elements of two networks, we can assume that they store multiple coefficients;
    # So, there is no need for a header saying "coeffs" of "coefficients".

    # 1. large scale fading
    pn_term_sn_term_ls_fading: np.ndarray
    pn_term_sn_stat_ls_fading: np.ndarray
    pn_stat_sn_stat_ls_fading: np.ndarray

    # 2. large scale gain
    pn_term_sn_term_ls_gain: np.ndarray
    pn_term_sn_stat_ls_gain: np.ndarray
    pn_stat_sn_stat_ls_gain: np.ndarray

    # 3. Channels Rician factors
    pn_term_sn_term_K: np.ndarray
    pn_term_sn_stat_K: np.ndarray
    pn_stat_sn_stat_K: np.ndarray

    # 4. Channel matrices
    pn_term_sn_term_H: np.ndarray
    pn_term_sn_stat_H: np.ndarray
    pn_stat_sn_stat_H: np.ndarray

    @classmethod
    def read(cls, list):
        return cls(*list)



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

    """
    
    This class is responsible for receiving the channel parameters that have been generated 
    and calculating the KPIs for each respective scenario.

    In order for the KPIs for each scenario to be calculated, it is necessary to specify 
    to this class which resource management methods it will use: 
        1. panel selection 
        2. scheduling 
        3. threshold
        4. ...


    This class relies on the help of others.

    """

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

    
    def set_terminal_scheduling_technique(self, path, class_name,thresh):

        self._scheduling.set_terminal_scheduling_technique(path, class_name, thresh)

    def set_station_scheduling_technique(self, path, class_name, thresh):
        self._scheduling.set_station_scheduling_technique(path, class_name, thresh)

    def set_panel_selection_technique(self, path, class_name):
        self._scheduling.set_panel_selection_technique(path, class_name)

    
    def compute_kpis_for_sn_uplink(self, ite: int):

        """
        This function calculates the KPIs for the coexistence scenario when the SN is in uplink.

        To compute the KPIs, it's necessary to determine which UEs will transmit in the shared band.

        The process follows this order:

            1. SN performs UE panel selection

            2. SN performs UE scheduling

            3. SN performs channel estimation

            4. SN performs clustering

            5. SN performs uplink combiners computation

        """

        # --- UE panel selection --- #
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

        # --- UE scheduling --- # 
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
        
    

        # --- channel estimation --- # 
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
        
        # --- AP clustering --- # 
        L = self.sn_config.num_stations * self.sn_config.num_arrays
        clustering_matrix = np.ones((self.sn_config.num_terminals, L))
        
        # --- SN uplink combiners computation --- #
        sn_ul_combiners = self._signal_processor.compute_uplink_combiners(
            H_hat_coeffs      = H_hat_coeffs,
            C_error_hat  = C_error_matrices,
            D_clustering = clustering_matrix,
            scheduled_term     = scheduled_ues,
            ul_max_p      = self.sn_config.terminal_max_power,
            n_var         = self.sn_config.noise_variance
            )

        # --- PN downlink precoders computation --- #
        pn_combining = np.ones((self.pn_config.num_terminals, 1))


        # --- SN total SE and caused INR --- #
        (
        spec_effs_sn_ul, 
        inr_caused_by_sn_ul) = self._kpi_calculator.compute_uplink_kpis(
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



        # --- KPI results --- #

        # 1. INR -> converting to logathimic scale
        from source.utils import lin2db
        inr_caused_by_sn_ul = lin2db(inr_caused_by_sn_ul)

        # 2. Number of UEs scheduled in the shared band
        num_scheduled_ues = len(scheduled_ues) 

        # 3. SN total spectral efficiency in the shared band
        total_se_of_sn_ul = np.sum(spec_effs_sn_ul)
        
        return (
            inr_caused_by_sn_ul, 
            num_scheduled_ues, 
            total_se_of_sn_ul
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
        
