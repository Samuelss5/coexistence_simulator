
from dataclasses import dataclass

import importlib.util

from source.NetworkConfig import DMimoConfig, FixedServiceConfig, DMimoGeometryForManySnapshots, FixedServiceGeometryForManySnapshots

from source.RunSnapshots import RunDMimoSnapshots, RunFixedServiceSnapshots

from .LoadMethods import MethodLoader

import numpy as np

class SeedManager:

    # Calling spawn(n) will create n SeedSequences that can be used to seed independent BitGenerators, i.e. for different threads.


    def __init__(self, root_seed=42, num_pools=10,):
        self._root_seed = np.random.SeedSequence(root_seed)
        self._num_pools = num_pools
        self._rngs = [None] * num_pools

    def refresh(self) -> None:
        fresh_seeds = self._root_seed.spawn(self._num_pools)
        self._rngs = [np.random.default_rng(s) for s in fresh_seeds]

    def get(self, index: int)-> np.random.Generator:
        return self._rngs[index]

class ScenarioGenerator:

    def __init__(self, pn_params, sn_params, num_snapshots, root_seed):
        
        self.pn_params = pn_params
        self.sn_params = sn_params

        self.pn_config = FixedServiceConfig.read(pn_params)
        self.sn_config = DMimoConfig.read(sn_params)

        # Secondary network snapshots generator
        
        #self.pn_generator = RunFixedServiceSnapshots(self.pn_config)
        #self.sn_generator = RunDMimoSnapshots(self.sn_config)
        
        self.pn_generator = None
        self.sn_generator = None

        self.root_seed = root_seed

        self.seeds = SeedManager(self.root_seed)

        self.num_snapshots = num_snapshots
        
    def create_networks_generators(self):
        
        pn_gen_class = MethodLoader.load_named(self.pn_params, ["snapshot_runner"])
        self.pn_generator = pn_gen_class["snapshot_runner"](self.pn_config)
        
        # Secondary (SN)
        sn_gen_class = MethodLoader.load_named(self.sn_params, ["snapshot_runner"])
        self.sn_generator = sn_gen_class["snapshot_runner"](self.sn_config)
        


    def run_networks_snapshots(self):

        self.seeds.refresh()

        
        # Isto esta hard-coded
        self.pn_geometry = FixedServiceGeometryForManySnapshots.get_from_tuple(
            self.pn_generator.run(self.num_snapshots, self.seeds.get(0))
        )
        

        self.sn_geometry = DMimoGeometryForManySnapshots.get_from_tuple(
            self.sn_generator.run(self.num_snapshots, self.seeds.get(1), self.root_seed)
            )


    def compute_inter_networks_links(self):

        from source.RunSnapshots import InterNetworkLinksBuilder

        builder = InterNetworkLinksBuilder(self.pn_geometry, self.sn_geometry, self.pn_config, self.sn_config, self.num_snapshots)

        builder.compute_doas()
        builder.compute_large_scale_coeffs(self.seeds.get(0), self.root_seed)
        builder.compute_R_matrices(self.root_seed)
        builder.generate_channels(self.seeds.get(0), self.root_seed)

