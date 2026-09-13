import numpy as np

from source.ScenarioReader import PanelSelectionContext

class TpsAltruisticFromLsfGain:
    
    # This function is hardcoded considering that the receiver is equipped with a single panel

    @classmethod
    def perform(cls, context: PanelSelectionContext) -> np.ndarray:

        gains_matrix = context.inter_network_gains

        selected_panels = np.zeros(context.num_terminals, dtype=int)
    
        for term in range(context.num_terminals):

            g_k = gains_matrix[:,term, ...]

            s_p = np.argmin(g_k)

            selected_panels[term] = s_p            
            

        return selected_panels


class TpsAltruisticFromChannelGain:
    
    # This function is hardcoded considering that the receiver is equipped with a single panel

    @classmethod
    def perform(cls, context: PanelSelectionContext) -> np.ndarray:

        channel_matrix = context.inter_network_channel

        num_pn_rx = channel_matrix.shape[0]

        gains_matrix = np.abs(channel_matrix)**2

        selected_panels = np.zeros(context.num_terminals, dtype=int)
    
        for term in range(context.num_terminals):

            # Channel between the k-th UE panels and the FS receiver
            h_k = channel_matrix[0, term, 0, ...]

            h_k_norm = np.linalg.norm(h_k, axis = (1,2))**2

            #print("h norm: ", h_k_norm)

            #g_k = gains_matrix[:,term, ...]

            s_p = np.argmin(h_k_norm)

            #print("s_p: ", s_p)

            selected_panels[term] = s_p            
            

        return selected_panels


class TpsSelfishFromChannelGain:

    @classmethod
    def perform(cls, context: PanelSelectionContext):

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



            #G_k = G_matrix[term,].transpose(1,0,2)
            #G_k = G_k.reshape(num_panels, num_stations * num_arrays)

            #g_k = np.mean(G_k, axis=1)

            #selected_panels[term] = np.argmax(g_k)

        return selected_panels
            
class TpsRandomic:

    @classmethod
    def perform(cls, context: PanelSelectionContext) -> np.ndarray:

        selected_panels = context.rng.integers(0, context.num_panels, size=context.num_terminals)

        #print("Selected_panels: ", selected_panels)

        return selected_panels

class NoSelection:

    @classmethod
    def compute(cls, num_terminals):
        return np.zeros(num_terminals)