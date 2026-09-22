from source.ScenarioReader import ScenarioReader
import numpy as np
import yaml
from pathlib import Path
import argparse

def load_inter_network_parameters(task_id: int):

    # OBS: For the current working directory:

    dir_path = Path(__file__).resolve().parent
    
    path_ls_fading = str(dir_path) + '/scenarios_storage/InterNetwork/lsg_parameters/ls_fading/'
    path_ls_gain = str(dir_path) + '/scenarios_storage/InterNetwork/lsg_parameters/ls_gain/'
    path_K_facts =   str(dir_path) + '/scenarios_storage/InterNetwork/lsg_parameters/K_facts/'

    path_H_coeffs   = str(dir_path) + '/scenarios_storage/InterNetwork/H_coeffs/'
    
    link_types = [
        'pn_term_sn_term',
        'pn_term_sn_stat',
        'pn_stat_sn_stat'
    ]

    data = {}

    for link in link_types:
        data[link] = {
            "ls_fading_coeffs": np.load(f"{path_ls_fading}{link}_ls_fading_for_all_snapshots_" + str(task_id) + ".npz",  allow_pickle=True)[f"{link}_ls_fading"],
            "ls_gain_coeffs":   np.load(f"{path_ls_gain}{link}_ls_gain_for_all_snapshots_" + str(task_id) + ".npz",    allow_pickle=True)[f"{link}_ls_gain"],
            "K_coeffs":         np.load(f"{path_K_facts}{link}_K_for_all_snapshots_" + str(task_id) + ".npz",   allow_pickle=True)[f"{link}_K"],
            "H_coeffs":         np.load(f"{path_H_coeffs}{link}_H_for_all_snapshots_" + str(task_id) + ".npz",     allow_pickle=True)[f"{link}_H"]
        }

    return data


    

def read_parallel_scenarios(task_id: int):


    file_path = 'networks_configurations.yaml'

    

    networks_configs = yaml.safe_load(open(file_path))
    
    # 1. Networks Parameters
    pn = networks_configs['Fixed_service']
    sn = networks_configs['Dmimo_network']
    
    # Scenarios reader
    sce_reader = ScenarioReader(pn, sn)
    
    
    inter_net_data = load_inter_network_parameters(task_id)


    sce_reader.set_cross_channels([

        inter_net_data["pn_term_sn_term"]["ls_fading_coeffs"], inter_net_data["pn_term_sn_stat"]["ls_fading_coeffs"], inter_net_data["pn_stat_sn_stat"]["ls_fading_coeffs"],

        inter_net_data["pn_term_sn_term"]["ls_gain_coeffs"], inter_net_data["pn_term_sn_stat"]["ls_gain_coeffs"], inter_net_data["pn_stat_sn_stat"]["ls_gain_coeffs"],

        inter_net_data["pn_term_sn_term"]["K_coeffs"], inter_net_data["pn_term_sn_stat"]["K_coeffs"], inter_net_data["pn_stat_sn_stat"]["K_coeffs"],

        inter_net_data["pn_term_sn_term"]["H_coeffs"], inter_net_data["pn_term_sn_stat"]["H_coeffs"], inter_net_data["pn_stat_sn_stat"]["H_coeffs"]

        ])
        
        
    # Secondary network scenarios parameters    

    dir_path = Path(__file__).resolve().parent

    path   = str(dir_path) + '/scenarios_storage/DMimo/'

    sn_lsg_coeffs = np.load(path + "lsg_parameters/lsg_coeffs_for_all_snapshots_" + str(task_id) + ".npz", allow_pickle = True)['lsg_coeffs']
    sn_R_matrices = np.load(path + "R_matrices/aps_R_matrices_for_all_snapshots_" + str(task_id) + ".npz", allow_pickle = True)['aps_R_matrices']
    sn_H_coeffs = np.load(path + "H_coeffs/H_coeffs_for_all_snapshots_" + str(task_id) + ".npz", allow_pickle = True)['H_coeffs']

    sce_reader.set_geometry([
        sn_lsg_coeffs, sn_R_matrices, sn_H_coeffs
    ])


    # ______________________________
    # scheduling techniques
    # ______________________________

    scheduling_techniques_path = 'source/scheduling/scheduling.py'
    panel_selection_path = 'source/scheduling/panel_selection.py'
   
    # UEs scheduling methods & thresholds
    DMimo_UE_scheduling_techniques = ["IndividualEstimated_INR", "CumulativeIndividualEstimated_INR"]
    DMimo_UE_scheduling_thresholds = [-10.0, -12.5, -15.0]

    # UEs panel selection methods
    DMimo_panel_selection_techniques = ['TpsAltruisticFromLsfGain', "TpsRandomic",]


    # 1. Scheduling before panel selection

    ul_inr_results_dict     = {}
    ul_num_ues_results_dict = {}
    ul_se_results_dict  = {}

    meth_name = "perform_as_second_step"
    
    # Scheduling technique
    for sched_tech in DMimo_UE_scheduling_techniques:
        # Scheduling threshold
        for sched_thresh in DMimo_UE_scheduling_thresholds:
            # Panel selection technique
            for panel_tech in DMimo_panel_selection_techniques:
    
                key = panel_tech + " + " + sched_tech + " + " + str(sched_thresh)

                ul_inr_results_dict[key]     = []
                ul_num_ues_results_dict[key] = []
                ul_se_results_dict[key]      = []

                    

    
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

                    sce_reader.set_terminal_scheduling_technique(
                        scheduling_techniques_path, sched_tech, meth_name, sched_thresh)

                    key = panel_tech + " + " + sched_tech + " + " + str(sched_thresh)
                    
                    (
                    ul_caused_inr, 
                    ul_num_ues, 
                    ul_sum_se) = sce_reader.compute_uplink_kpis_for_panel_selection_first(ite)
                    
                    ul_inr_results_dict[key].append(ul_caused_inr)
                    ul_num_ues_results_dict[key].append(ul_num_ues)
                    ul_se_results_dict[key].append(ul_sum_se)  




    import pandas as pd

    ul_inr_df = pd.DataFrame(ul_inr_results_dict)
    ul_num_ues_df = pd.DataFrame(ul_num_ues_results_dict)
    ul_se_df = pd.DataFrame(ul_se_results_dict)

    path_inr = 'results_storage/inr_results/'
    path_num = 'results_storage/num_ues_results/'
    path_se = 'results_storage/se_results/'

    # Saving INR results
    ul_inr_df.to_csv(path_inr + "ul_inr_" + str(task_id) + ".csv", index=False, sep=',', encoding='utf-8')
    # Saving num scheduled UEs results
    ul_num_ues_df.to_csv(path_num + "ul_num_UEs_" + str(task_id) + ".csv", index=False, sep=',', encoding='utf-8')
    # Saving the sum SE results
    ul_se_df.to_csv(path_se + "ul_sum_se_" + str(task_id) + ".csv", index=False, sep=',', encoding='utf-8')



   
    


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Study')
    parser.add_argument('-s', dest = 'seed', type = int, help = 'SEED', required = True)
    args = parser.parse_args()

    read_parallel_scenarios(args.seed)
