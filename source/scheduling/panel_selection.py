import numpy as np

from source.ScenarioReader import PanelSelectionContext

class TpsSelfishFromLsfGain:
    
    @classmethod
    def perform(cls, context) -> np.ndarray:
        ls_gain_coeffs = context.intra_net_ls_gain
        
        sel_panels = np.empty(context.num_term, dtype=int)
        
        for ue_id in range(context.num_term):
            
            gains_ue = ls_gain_coeffs[ue_id, ...] # (n_ap, n_ue_panel, n_ap_array)
            gains_ue = gains_ue.transpose(1,0,2)
            gains_ue = gains_ue.reshape(gains_ue.shape[0], -1) # (n_ue_panel, n_ap x n_ap_array)
            gains_ue_mean = gains_ue.mean(axis = 1) # (n_ue_panel,)

            sel_panels[ue_id] = np.argmax(gains_ue_mean)

        return sel_panels


class TpsAltruisticFromLsfGain:

    @classmethod
    def perform(cls, context) -> np.ndarray:

        """
            This panel selection is designed to interfere as little as possible with the PN:
            - Uses the large scale fading parameters to estimate the interference
        """
        
        # Large scale gain coefficientes between the UEs and the FS rx
        ls_gain_coeffs = context.inter_net_ls_gain

        # array storing the indices of the selected panels 
        sel_panels = np.empty(context.num_term, dtype=int)

        for ue_id in range(context.num_term):

            g_vec = ls_gain_coeffs[:,ue_id, ...]

            panel_id = np.argmin(g_vec)

            sel_panels[ue_id] = panel_id

        return sel_panels


class TpsAltruisticFromChannelGain:

    @classmethod
    def perform(cls, context) -> np.ndarray:

        """
            This panel selection is designed to interfere as little as possible with the PN:
            - Uses the estimated channel coefficients to estimate the interference
        """

        ...

        channel_matrix = context.inter_network_channel

        num_pn_rx = channel_matrix.shape[0]

        gains_matrix = np.abs(channel_matrix)**2

        selected_panels = np.zeros(context.num_terminals, dtype=int)
    
        for ue_id in range(context.num_terminals):

            # Channel between the k-th UE panels and the FS receiver
            h_k = channel_matrix[0, term, 0, ...]

            h_k_norm = np.linalg.norm(h_k, axis = (1,2))**2

            s_p = np.argmin(h_k_norm)

            selected_panels[term] = s_p            
            

        return selected_panels




class TpsSelfishFromChannelGain:


    # OBS: Since this panel selection method requires the estimated channel coefficients, it 

    @classmethod
    def perform_as_first_step(cls, context):

        """
        This method consider that the panel selection
        """

        H_matrix = context.intra_network_channel

        num_terminals, num_stations, num_panels, num_arrays, N_p, N_a = H_matrix.shape

        selected_panels = np.zeros(num_terminals, dtype=np.int32)

        for term in range(num_terminals):

            # APs, panels, arrays, N_p, N_a -> 0, 1, 2, 3, 4
            H_k = H_matrix[term]

            # The goal is (APs, arrays, N_a, panels, N_p)  -> (0, 2, 4, 1, 3)
            H_k = H_k.transpose(0,2,4,1,3)

            # The goal is (APs x arrays x N_a, panels, N_p)
            H_k = H_k.reshape(num_stations * num_arrays * N_a, num_panels, N_p)

            # The goal is (panels, APs x arrays x N_a, N_p)
            H_k = H_k.transpose(1,0,2)

            H_k_norm = np.linalg.norm(H_k, axis = (1,2))**2

            selected_panels[term] = np.argmax(H_k_norm)

        return selected_panels

    @classmethod
    def perform_as_second_step(cls, context):
        """
        This method consider that the panel selection
        """
        ...
        # # Estimated channel coefficients
        # H_hat_coeffs = 

        # num_term, num_stat, num_panels, num_arrays, N_p, N_a = H_hat_coeffs.shape



            
class TpsRandomic:

    """
        This panel selection is designed to be performed randomly:
        - Uses no criterion
    """

    @classmethod
    def perform(cls, context: PanelSelectionContext) -> np.ndarray:

        sel_panels = context.rng.integers(0, context.num_panels, size=context.num_term)

        return sel_panels


