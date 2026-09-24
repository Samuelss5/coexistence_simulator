import numpy as np

from source.geometry.coordinates import calculate_2d_distances
from source.geometry.coordinates import calculate_3d_distances

from source.utils import db2lin

class UMa_3gpp_large_scale_fading:

    
    K_mu  = 5 # dB
    K_sig = 9 # dB

    sh_los  = 4 # dB
    sh_nlos = 7.8 # dB

    c = 3e8

    @classmethod
    def line_of_sight_probability(cls, d2_dist: np.ndarray, h_ut):

        dist_mask = d2_dist <= 18 # meters

        # parameter
        c = 0

        if h_ut <= 13:
            pass
        elif h_ut > 13 and h_ut <= 23:

            c = pow( (h_ut - 13)/10, 1.5 )

        First_los_prob = ( 18 / d2_dist + np.exp(-d2_dist / 63) * (1 - 18 / d2_dist) ) * (1 + c * (5/4) * pow(d2_dist/100, 3) * np.exp(-d2_dist / 150) )

        Los_prob = np.where(dist_mask, 1, First_los_prob)

        return Los_prob

    @classmethod
    def path_loss(cls, d2_dist, d3_dist, los_mask, h_ut, h_bs, fc):
    
        
        h_e = 1 # metro
        
        # Effective BS antennas height

        dh_bs = h_bs - h_e

        # Effective UT antennas height

        dh_ut = h_ut - h_e
        
        print("dh_bs: ", dh_bs)
        
        print("dh_ut: ", dh_ut)

        # Distance breakpoint
        
        lambda_ =  cls.c / fc
        
        d_bp = 4 * dh_bs * dh_ut / lambda_
        
        print("fc usando em Hz: ", fc)
        print("distance break point: ", d_bp)

        fc = fc / 1e9
        
        print("fc usado em GHz: ", fc)

        # Links with distance less than the bp distance

        dist_mask = d2_dist < d_bp


        # Path-loss expressions for los channels

        pl1_los = 28.0 + 22 * np.log10(d3_dist) + 20 * np.log10(fc)

        pl2_los = 28.0 + 40 * np.log10(d3_dist) + 20 * np.log10(fc) - 9.0 * np.log10( (d_bp * d_bp) + (h_bs - h_ut) * (h_bs - h_ut) )

        # Generic path-loss expression for Nlos channels

        pl_nlos = 32.4 + 20 * np.log10(fc) + 30 * np.log10(d3_dist)

        path_loss = np.zeros( d3_dist.shape, dtype = np.float64 )

        dist_mask = (d2_dist >= 10) & (d_bp >=  d2_dist)


        # first we define with respect to the distance

        path_loss = np.where(dist_mask, pl1_los, pl2_los)

        path_loss = np.where(los_mask, path_loss, pl_nlos)
        
        return -1 * path_loss


    @classmethod 
    def set_line_of_sight_conditions(cls, los_prob, rng):

        random_thresholds = rng.uniform(0,1, size = los_prob.shape)

        mask = los_prob > random_thresholds

        Ks = rng.normal(cls.K_mu, cls.K_sig, size = los_prob.shape)

        Ks = pow(10, Ks/10)

        Ks = np.where(mask, Ks, 0)

        return Ks


    @classmethod
    def uncorrelated_shadowing(cls, los_mask: np.ndarray, rng: object):

        los_case = np.sqrt(cls.sh_los) * rng.normal(0,1, size=los_mask.shape)

        nlos_case = np.sqrt(cls.sh_nlos) * rng.normal(0,1, size=los_mask.shape)

        sh = np.zeros(los_mask.shape, dtype = float)

        sh = np.where(los_mask, los_case, nlos_case) # dB

        #Garantindo valores positivos
        return np.abs(sh)


    @classmethod
    def compute_queued(cls, queue, coord1: np.ndarray, coord2: np.ndarray, h_ut: float, h_bs: float, fc, rng):

        # 2D distances matrix 
        d2_dist = calculate_2d_distances(coord1, coord2)

        d3_dist = calculate_3d_distances(coord1, coord2)


        los_prob = cls.line_of_sight_probability(d2_dist, h_ut)

        # Ricean factors in linear scale
        K_factors = cls.set_line_of_sight_conditions(los_prob, rng)

        path_loss = cls.path_loss(d2_dist, d3_dist, K_factors > 0, h_ut, h_bs, fc)

        shadowing = cls.uncorrelated_shadowing(K_factors > 0, rng)
        
        

        lsf_coefficients = path_loss - shadowing

        lsf_coefficients = db2lin(lsf_coefficients)

        queue.put((lsf_coefficients, K_factors))
    

        #return lsf_coefficients, K_factors
    
    @classmethod
    def compute(cls, coord1: np.ndarray, coord2: np.ndarray, h_ut: float, h_bs: float, fc, rng, certainty_of_los):

        # 2D distances matrix 
        d2_dist = calculate_2d_distances(coord1, coord2)

        d3_dist = calculate_3d_distances(coord1, coord2)

        if certainty_of_los == None:
            los_prob = cls.line_of_sight_probability(d2_dist, h_ut)

        else:
            los_prob = np.ones(d2_dist.shape)

        
        # Ricean factors in linear scale
        K_factors = cls.set_line_of_sight_conditions(los_prob, rng)

        path_loss = cls.path_loss(d2_dist, d3_dist, K_factors > 0, h_ut, h_bs, fc)

        shadowing = cls.uncorrelated_shadowing(K_factors > 0, rng)
        
        lsf_coefficients = path_loss - shadowing

        lsf_coefficients = db2lin(lsf_coefficients)
        
        return lsf_coefficients, K_factors

    @classmethod
    def compute_for_queued(cls, queue, coord1: np.ndarray, coord2: np.ndarray, h_ut: float, h_bs: float, fc, rng, certainty_of_los):

        # 2D distances matrix 
        d2_dist = calculate_2d_distances(coord1, coord2)

        d3_dist = calculate_3d_distances(coord1, coord2)

        if certainty_of_los == None:
            los_prob = cls.line_of_sight_probability(d2_dist, h_ut)

        else:
            los_prob = np.ones(d2_dist.shape)

        
        # Ricean factors in linear scale
        K_factors = cls.set_line_of_sight_conditions(los_prob, rng)

        path_loss = cls.path_loss(d2_dist, d3_dist, K_factors > 0, h_ut, h_bs, fc)

        shadowing = cls.uncorrelated_shadowing(K_factors > 0, rng)

        lsf_coefficients = path_loss - shadowing

        lsf_coefficients = pow(10, lsf_coefficients/10)

        tuple = (lsf_coefficients, K_factors)

        queue.put(tuple)







