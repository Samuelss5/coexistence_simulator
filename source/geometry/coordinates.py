import numpy as np


def calculate_2d_distances(coord1: np.ndarray, coord2: np.ndarray):

    distances = np.zeros((len(coord1), len(coord2)), dtype = float )

    for i in range(len(coord1)):
        for j in range(len(coord2)):

            xd = coord1[i][0] - coord2[j][0]
            yd = coord1[i][1] - coord2[j][1]

            d = np.abs(xd + 1j*  yd)
            distances[i,j] = d

    return distances

def calculate_3d_distances(coord1: np.ndarray, coord2: np.ndarray):

    distances = np.zeros((len(coord1), len(coord2)), dtype = float )

    for i in range(len(coord1)):
        for j in range(len(coord2)):

            xd = coord1[i][0] - coord2[j][0]
            yd = coord1[i][1] - coord2[j][1]
            zd = coord1[i][1] - coord2[j][1]

            d2 = np.abs(xd + 1j * yd)
            d3 = np.abs(d2 + 1j * zd)

            distances[i,j] = d3

    return distances

class UMa3gppTerminalsDeployment:
    """ This method deploys the terminals according to the TR 38.901 requirements of minimum distance in an UMa scenario """

    def deploy(
        stations_coords: np.ndarray, 
        terminals_height: float, 
        num_terminals: int, 
        rng: object
        ):

        ISD = 150
        
        """
        1. Considering that all terminals have the same height

        2. Returns the 3D coordinates as tuples (x,y,z)

        """

        # Minimum distance between UEs and APs: 35 m
        r_min = 10

        # Assuming that the spacing between the APs is of 
        r_max = ISD - r_min

        # Randomic allocation of stations
        Random_stations_allocation = rng.integers(0, stations_coords.shape[0], size = num_terminals)

        Random_angles = rng.uniform(0, 2 * np.pi, size = num_terminals)

        Terminals_coords = np.zeros(num_terminals, dtype=object)

        for term_k in range(num_terminals):

            radius_k = rng.uniform(r_min, r_max)
            sta_idx = Random_stations_allocation[term_k]

            x = stations_coords[sta_idx][0] + np.cos(Random_angles[term_k]) * radius_k
            y = stations_coords[sta_idx][1] + np.sin(Random_angles[term_k]) * radius_k
            Terminals_coords[term_k] = (x, y, terminals_height)

        return Terminals_coords

class RegularGridDeployment:

    def deploy( 
        elements_height: float, 
        num_elements: int, 
        rng: object
        ):

        ISD = 150

        num_row = int(np.sqrt(num_elements))
        num_col = int(np.sqrt(num_elements))

        x = np.arange(num_row) * ISD  - (num_col - 1)* ISD/2
        y = np.arange(num_row) * ISD - (num_col -1) * ISD/2 

        xv, yv = np.meshgrid(x, y)
        x_points, y_points = xv.flatten(), yv.flatten()

        Elements_coords = np.zeros(num_elements, dtype=object)

        for el_k in range(num_elements):
            Elements_coords[el_k] = (x_points[el_k], y_points[el_k], elements_height)

        return Elements_coords
