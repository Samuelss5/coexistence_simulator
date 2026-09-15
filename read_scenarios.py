from source.ScenarioReader import ScenarioReader
import numpy as np
import yaml
from pathlib import Path

def load_inter_network_parameters():

    # OBS: For the current working directory:

    dir_path = Path(__file__).resolve().parent

    # Path to the large scale parameters
    path_lsg = str(dir_path) + '/scenarios_storage/InterNetwork/lsg_parameters/'
    # Path to the channel parameters
    path_H   = str(dir_path) + '/scenarios_storage/InterNetwork/H_coeffs/'
    
    link_types = [
        'pn_term_sn_term',
        'pn_term_sn_stat',
        'pn_stat_sn_stat'
    ]

    data = {}

    for link in link_types:
        data[link] = {
            "ls_fading_coeffs": np.load(f"{path_lsg}{link}_ls_fading_full.npz",  allow_pickle=True)[f"{link}_ls_fading"],
            "ls_gain_coeffs":   np.load(f"{path_lsg}{link}_ls_gain_full.npz",    allow_pickle=True)[f"{link}_ls_gain"],
            "K_coeffs":         np.load(f"{path_lsg}{link}_K_full.npz",   allow_pickle=True)[f"{link}_K"],
            "H_coeffs":         np.load(f"{path_H}{link}_H_full.npz",     allow_pickle=True)[f"{link}_H"]
        }

    return data


    

def main():


    file_path = 'networks_configurations.yaml'

    

    networks_configs = yaml.safe_load(open(file_path))
    
    # 1. Networks Parameters
    pn = networks_configs['Fixed_service']
    sn = networks_configs['Dmimo_network']
    
    # Scenarios reader
    sce_reader = ScenarioReader(pn, sn)
    
    
    inter_net_data = load_inter_network_parameters()


    sce_reader.set_cross_channels([

        inter_net_data["pn_term_sn_term"]["ls_fading_coeffs"], inter_net_data["pn_term_sn_stat"]["ls_fading_coeffs"], inter_net_data["pn_stat_sn_stat"]["ls_fading_coeffs"],

        inter_net_data["pn_term_sn_term"]["ls_gain_coeffs"], inter_net_data["pn_term_sn_stat"]["ls_gain_coeffs"], inter_net_data["pn_stat_sn_stat"]["ls_gain_coeffs"],

        inter_net_data["pn_term_sn_term"]["K_coeffs"], inter_net_data["pn_term_sn_stat"]["K_coeffs"], inter_net_data["pn_stat_sn_stat"]["K_coeffs"],

        inter_net_data["pn_term_sn_term"]["H_coeffs"], inter_net_data["pn_term_sn_stat"]["H_coeffs"], inter_net_data["pn_stat_sn_stat"]["H_coeffs"]

        ])

    dir_path = Path(__file__).resolve().parent

    path   = str(dir_path) + '/scenarios_storage/DMimo/'

    sn_lsg_coeffs = np.load(path + 'lsg_parameters/lsg_coeffs_full.npz', allow_pickle = True)['lsg_coeffs']
    sn_R_matrices = np.load(path + 'R_matrices/aps_R_matrices_full.npz', allow_pickle = True)['aps_R_matrices']
    sn_H_coeffs = np.load(path + 'H_coeffs/H_coeffs_full.npz', allow_pickle = True)['H_coeffs']

    sce_reader.set_geometry([
        sn_lsg_coeffs, sn_R_matrices, sn_H_coeffs
    ])


    # ______________________________
    # scheduling techniques
    # ______________________________

    scheduling_techniques_path = 'source/scheduling/scheduling.py'
    panel_selection_path = 'source/scheduling/panel_selection.py'
   
    # UEs scheduling methods & thresholds
    DMimo_UE_scheduling_techniques = ["IndividualEstimated_INR",]
    DMimo_UE_scheduling_thresholds = [-10]

    # UEs panel selection methods
    DMimo_panel_selection_techniques = ['TpsAltruisticFromLsfGain', 'TpsRandomic']

    DMimo_UE_scheduling_methods_names = [
            "min_antenna_gain_as_first_step", 
            "max_antenna_gain_as_first_step"]

    # 1. Scheduling before panel selection

    ul_inr_sched_first     = {}
    ul_num_ues_sched_first = {}
    ul_se_sched_first      = {}

    # Panel selection technique
    for panel_tech in DMimo_panel_selection_techniques:
        # Scheduling technique
        for sched_tech in DMimo_UE_scheduling_techniques:
            # Scheduling threshold
            for sched_thresh in DMimo_UE_scheduling_thresholds:
                # Scheduling method name
                for meth_name in DMimo_UE_scheduling_methods_names:

                    key = sched_tech + " + " + meth_name + " + " + str(sched_thresh) + " + " + panel_tech

                    print(key)

                    ul_inr_sched_first[key]     = []
                    ul_num_ues_sched_first[key] = []
                    ul_se_sched_first[key]      = []

                    

    
    num_snapshots = networks_configs['num_snapshots']

    for ite in range(num_snapshots):

        print("Iteration number " + str(ite + 1))
        # Panel selection technique
        for panel_tech in DMimo_panel_selection_techniques:
            sce_reader.set_panel_selection_technique(panel_selection_path, panel_tech)

            # Scheduling technique
            for sched_tech in DMimo_UE_scheduling_techniques:
                # Scheduling threshold
                for sched_thresh in DMimo_UE_scheduling_thresholds:
                    # Scheduling method name
                    for meth_name in DMimo_UE_scheduling_methods_names:

                        sce_reader.set_terminal_scheduling_technique(
                            scheduling_techniques_path, sched_tech, meth_name, sched_thresh)

                        key = sched_tech + " + " + meth_name + " + " + str(sched_thresh) + " + " + panel_tech

                        (
                        ul_caused_inr, 
                        ul_num_ues, 
                        ul_sum_se) = sce_reader.compute_uplink_kpis_for_scheduling_first(ite)

                        ul_inr_sched_first[key].append(ul_caused_inr)
                        ul_num_ues_sched_first[key].append(ul_num_ues)
                        ul_se_sched_first[key].append(ul_sum_se)  




    import pandas as pd

    ul_inr_df = pd.DataFrame(ul_inr_sched_first)
    ul_num_ues_df = pd.DataFrame(ul_num_ues_sched_first)
    ul_se_df = pd.DataFrame(ul_se_sched_first)

    path_inr = 'results_storage/scheduling_first/inr_results/'
    path_num = 'results_storage/scheduling_first/num_ues_results/'
    path_se = 'results_storage/scheduling_first/se_results/'

    # Saving INR results
    ul_inr_df.to_csv(path_inr + 'ul_inr.csv', index=False, sep=',', encoding='utf-8')
    # Saving num scheduled UEs results
    ul_num_ues_df.to_csv(path_num + 'ul_num_UEs.csv', index=False, sep=',', encoding='utf-8')
    # Saving the sum SE results
    ul_se_df.to_csv(path_se + 'ul_sum_se.csv', index=False, sep=',', encoding='utf-8')


    DMimo_UE_scheduling_methods_names = ["perform_as_second_step", ]

    # 2. Panel selection before scheduling
    ul_inr_tps_first     = {}
    ul_num_ues_tps_first = {}
    ul_se_tps_first      = {}

    # Panel selection technique
    for panel_tech in DMimo_panel_selection_techniques:
        # Scheduling technique
        for sched_tech in DMimo_UE_scheduling_techniques:
            # Scheduling threshold
            for sched_thresh in DMimo_UE_scheduling_thresholds:
                # Scheduling method name
                for meth_name in DMimo_UE_scheduling_methods_names:

                    key = sched_tech + " + " + meth_name + " + " + str(sched_thresh) + " + " + panel_tech

                    print(key)

                    ul_inr_sched_first[key]     = []
                    ul_num_ues_sched_first[key] = []
                    ul_se_sched_first[key]      = []
    


if __name__ == "__main__":
    main()
