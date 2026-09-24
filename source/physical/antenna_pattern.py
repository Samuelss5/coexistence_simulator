import numpy as np

def vertical_angular_distance(angle, boresight):

    d_theta = np.abs(angle - boresight)

    return d_theta


def horizontal_angular_distance(angle, boresight): 

    d_phi = np.abs(
        np.arctan2( np.sin(angle - boresight), np.cos(angle - boresight))
        )
    
    return d_phi


class Stations_3gpp_pattern:

    # According to TR 38.901 V 19.2
    g_max   = 8 
    am      = 30
    gamma_h = 65
    gamma_v = 65


    @classmethod
    def horizontal(cls, angle):

        x = 12 * (angle/cls.gamma_h) * (angle/cls.gamma_h)

        return -1 * np.minimum(x, cls.am) + cls.g_max

    @classmethod
    def vertical(cls, angle):

        x = 12 * (angle/cls.gamma_v) * (angle/cls.gamma_v)

        return -1 * np.minimum(x, cls.am) + cls.g_max

    @classmethod
    def compute(cls, relative_AoAs_h, relative_AoAs_v):

        d_AoAs_h = 180 * relative_AoAs_h / np.pi
        d_AoAs_v = 180 * relative_AoAs_v / np.pi
        
        #d_AoAs_h = d_AoAs_h * 0 
        #d_AoAs_v = d_AoAs_v * 0 

        Gains_h = cls.horizontal(d_AoAs_h)
        Gains_v = cls.vertical(d_AoAs_v)

        # 3D gain
        Gains_e = cls.g_max - np.minimum(-(Gains_h + Gains_v), cls.am) 
        Gains_e = pow(10, Gains_e/10)

        return Gains_e 

    @classmethod
    def compute_for_queue(cls, queue, relative_AoAs_h, relative_AoAs_v):

        d_AoAs_h = 180 * relative_AoAs_h / np.pi
        d_AoAs_v = 180 * relative_AoAs_v / np.pi
        
        #d_AoAs_h = d_AoAs_h * 0 
        #d_AoAs_v = d_AoAs_v * 0 

        Gains_h = cls.horizontal(d_AoAs_h)
        Gains_v = cls.vertical(d_AoAs_v)

        # 3D gain
        Gains_e = cls.g_max - np.minimum(-(Gains_h + Gains_v), cls.am) 
        Gains_e = pow(10, Gains_e/10)

        queue.put(Gains_e) 
    
    


class Terminals_3gpp_pattern:

    g_max   = 5.3 
    am      = 22.5
    gamma_h = 125
    gamma_v = 125


    @classmethod
    def horizontal(cls, angle):

        x = 12 * (angle/cls.gamma_h) * (angle/cls.gamma_h)

        return -1 * np.minimum(x, cls.am)

    @classmethod
    def vertical(cls, angle):

        x = 12 * (angle/cls.gamma_v) * (angle/cls.gamma_v)

        return -1 * np.minimum(x, cls.am)

    @classmethod
    def compute(cls, relative_AoAs_h, relative_AoAs_v):

        d_AoAs_h = 180 * relative_AoAs_h / np.pi
        d_AoAs_v = 180 * relative_AoAs_v / np.pi
        
        #d_AoAs_h = d_AoAs_h * 0 
        #d_AoAs_v = d_AoAs_v * 0 

        Gains_h = cls.horizontal(d_AoAs_h)
        Gains_v = cls.vertical(d_AoAs_v)

        # 3D gain
        Gains_e = cls.g_max - np.minimum(-(Gains_h + Gains_v), cls.am) 
        Gains_e = pow(10, Gains_e/10)

        return Gains_e 

    @classmethod
    def compute_for_queue(cls, queue, relative_AoAs_h, relative_AoAs_v):

        d_AoAs_h = 180 * relative_AoAs_h / np.pi
        d_AoAs_v = 180 * relative_AoAs_v / np.pi
        
        #d_AoAs_h = d_AoAs_h * 0 
        #d_AoAs_v = d_AoAs_v * 0 

        Gains_h = cls.horizontal(d_AoAs_h)
        Gains_v = cls.vertical(d_AoAs_v)

        # 3D gain
        Gains_e = cls.g_max - np.minimum(-(Gains_h + Gains_v), cls.am) 
        Gains_e = pow(10, Gains_e/10)

        queue.put(Gains_e) 
    

class itu_fs_pattern:


    g_max = 47.4 
    diameter_to_wave_ratio = 96.605

    @classmethod
    def horizontal(cls, Angles):

        # antenna gain value according to Lorenza presentation


        # 1. Gains of the first side-lobes

        Gains_1 = 2 + 15 * np.log10(cls.diameter_to_wave_ratio)

        # 2. Auxiliar variables

        Angles_m = 20 * (1/cls.diameter_to_wave_ratio) * np.sqrt(cls.g_max - Gains_1)

        # 3. Setting conditions

        Mask_1 = (Angles >= 0) & (Angles < Angles_m)

        Mask_2 = (Angles >= Angles_m) & (Angles < 100 * (1 / cls.diameter_to_wave_ratio) )

        Mask_3 = (Angles > 100 * (1 / cls.diameter_to_wave_ratio) ) & (Angles < 48)

        Mask_4 = (Angles > 48) & (Angles <= 180)

        Gains = np.zeros(Angles.shape, dtype = np.float64)

        # 1. Applying the condition 1
        Gains = np.where(Mask_1, cls.g_max - 2.5 * pow(10,-3) * (cls.diameter_to_wave_ratio * Angles)**2, 0)

        # 2.
        Gains = np.where(Mask_2, Gains_1, 0)

        # 3.
        safe_angles = np.where(Mask_3, Angles, 1)
        Gains = np.where(Mask_3, 52 - 10 * np.log10(cls.diameter_to_wave_ratio) - 25 * np.log10(safe_angles), 0)

        # 4. 
        Gains = np.where(Mask_4, 10 - 10 * np.log10(cls.diameter_to_wave_ratio), 0)

        return Gains



    @classmethod
    def vertical(cls, Angles):

        # antenna gain value according to Lorenza presentation

        # 1. Gains of the first side-lobes

        Gains_1 = 2 + 15 * np.log10(cls.diameter_to_wave_ratio)

        # 2. Auxiliar variables

        Angles_m = 20 * (1/cls.diameter_to_wave_ratio) * np.sqrt(cls.g_max - Gains_1)

        # 3. Setting conditions

        Mask_1 = (Angles > 0) & (Angles < Angles_m)

        Mask_2 = (Angles >= Angles_m) & (Angles < 100 * (1 / cls.diameter_to_wave_ratio) )

        Mask_3 = (Angles > 100 * (1 / cls.diameter_to_wave_ratio) ) & (Angles < 48)

        Mask_4 = (Angles > 48) & (Angles <= 180)

        Gains = np.zeros(Angles.shape, dtype = np.float64)

        # 1. Applying the condition 1
        Gains = np.where(Mask_1, cls.g_max - 2.5 * pow(10,-3) * (cls.diameter_to_wave_ratio * Angles)**2, 0)

        # 2.
        Gains = np.where(Mask_2, Gains_1, 0)

        # 3.
        safe_angles = np.where(Mask_3, Angles, 1)
        Gains = np.where(Mask_3, 52 - 10 * np.log10(cls.diameter_to_wave_ratio) - 25 * np.log10(safe_angles), 0)

        # 4. 
        Gains = np.where(Mask_4, 10 - 10 * np.log10(cls.diameter_to_wave_ratio), 0)

        return Gains

    @classmethod
    def compute(cls, relative_AoAs_h, relative_AoAs_v):

        d_AoAs_h = 180 * relative_AoAs_h / np.pi
        d_AoAs_v = 180 * relative_AoAs_v / np.pi

        Gains_h = cls.horizontal(d_AoAs_h)
        Gains_v = cls.vertical(d_AoAs_v)

        # 3D gain
        Gains_e = Gains_h + Gains_v
        Gains_e = pow(10, Gains_e/10)

        return Gains_e 

