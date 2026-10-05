import numpy as np

from source.utils import *

from source.geometry.coordinates import calculate_2d_distances


class IndividualEstimated_INR:
    
    @classmethod
    def perform(cls, context):

        """
        This class method performs UE scheduling considering that it is a second step after UE panel selecion.

        This class method performs UE scheduling by estimating the interference that each UE causes to the fixed service (FS) based on large-scale parameters.

        The main parameter used to schedule a UE is the interference-to-noise (INR) level that it causes to the FS.

        """

        # 1. UEs maximum transmission power
        ue_max_p = context.term_max_p

        # 2. Matrix containing the large-scale gains of the links between UEs and the FS
        ls_gain_coeffs = context.inter_net_ls_gain

        # 3. Vector containing the indexes of the panels selected by each UE
        ue_sel_panels = context.term_sel_panels

        # 4. Fixed service noise variance
        fs_n_var = context.n_var


        # Number of UEs
        K = len(ue_sel_panels)
        

        # OBS: the antenna gains are already included in the large-scale  
        # OBS: the FS is equipped with a single panel or array 
        inrs_hat = ue_max_p * ls_gain_coeffs[0, np.arange(K), 0, ue_sel_panels] / fs_n_var
        inrs_hat = lin2db(inrs_hat)
        
        scheduled_ues = np.where(inrs_hat <= context.threshold)[0]
        
        return scheduled_ues




class CumulativeIndividualEstimated_INR:

    @classmethod
    def perform(cls, context):
    

        # OBS: The difference between ls_fading and ls_gain is that ls_gain takes into account the antenna gains!
        # OBS: "term" is the abbreviation of terminal
        # OBS: "inter_net" means that ...

        # 6. Terminals maximum transmission power 
        term_max_p = context.term_max_p
        
        # 2. Inter network large scale gain coefficients
        inter_net_ls_gain = context.inter_net_ls_gain
        
        # 4. Vector containing the indexes of the panels selected by each terminal
        term_sel_panels = context.term_sel_panels
        
        # 9. PN noise variance
        pn_n_var = context.n_var


        K = len(term_sel_panels)
        
        # OBS: the antenna gains are already included in the large-scale  
        # OBS: the FS is equipped with a single panel or array 
        inrs_hat = term_max_p * inter_net_ls_gain[0, np.arange(K), 0, term_sel_panels] / pn_n_var
        
        ordered_inrs_hat  = np.sort(inrs_hat)
        ordered_inrs_idxs = np.argsort(inrs_hat)
        
    
        cumulative_inrs_hat = np.cumsum(ordered_inrs_hat)
        cumulative_inrs_hat = lin2db(cumulative_inrs_hat)
        
        
        sel_idxs = np.where(cumulative_inrs_hat <= context.threshold)[0]

        scheduled_terms = ordered_inrs_idxs[sel_idxs]
        scheduled_terms = np.sort(scheduled_terms)
        
        return scheduled_terms

