import sys
import os
import argparse
from pathlib import Path
import yaml
from source.ScenarioGenerator import ScenarioGenerator

def run_simulation(args_obj):

    # Simulation root Seed
    sim_root_seed = args_obj.seed
    
    # Networks yaml config file path
    nets_config_file_path = "networks_configurations.yaml"

    networks_configs = yaml.safe_load(open(nets_config_file_path))

    # 1. Primary network configs
    pn = networks_configs['Fixed_service']
    
    # 2. Secondary network configs
    sn = networks_configs['Dmimo_network']

    # Number of snapshots
    num_snapshots = networks_configs['num_snapshots']

    # Scenario Generator object
    scenario_gen = ScenarioGenerator(pn, sn, num_snapshots, sim_root_seed)
    
    # Create the "generation" objects for both networks
    scenario_gen.create_networks_generators()
    
    # Running individual networks snapshots
    scenario_gen.run_networks_snapshots()
    
    # Running inter networks snapshots
    scenario_gen.compute_inter_networks_links()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Study')
    
    # Simulation root Seed
    parser.add_argument('-s', dest = 'seed', type = int, help = 'SEED', required = True)
    args = parser.parse_args()

    run_simulation(args)

