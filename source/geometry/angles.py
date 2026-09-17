import numpy as np


def compute_doa(rx_pos: object, tx_pos: object):
    """ Compute the direction of arrival for the receiving link between two objects """

    # 
    x_d = tx_pos[0] - rx_pos[0]
    y_d = tx_pos[1] - rx_pos[1]
    z_d = tx_pos[2] - rx_pos[2]

    d2_d = np.sqrt(x_d**2 + y_d**2)

    h_aoa_rx = np.arctan2(y_d, x_d)
    v_aoa_rx = np.arctan2(z_d, d2_d)

    return h_aoa_rx, v_aoa_rx


def compute_multiple_doas(rx_coords: np.ndarray, tx_coords: np.ndarray):
    """ Compute the Directions of arrival for a given set of receivers and transmitters coordinates """

    num_rx = len(rx_coords)
    num_tx = len(tx_coords)

    rx_shape = (num_rx, num_tx)
    tx_shape = (num_tx, num_rx)

    rx_doas_h = np.zeros(rx_shape, dtype=float)
    rx_doas_v = np.zeros(rx_shape, dtype=float)

    tx_doas_h = np.zeros(tx_shape, dtype=float)
    tx_doas_v = np.zeros(tx_shape, dtype=float)

    for rx in range(num_rx):
        for tx in range(num_tx):
            (rx_doas_h[rx, tx], rx_doas_v[rx, tx]) = compute_doa(rx_coords[rx], tx_coords[tx]) 
            
            (tx_doas_h[tx, rx], tx_doas_v[tx, rx]) = compute_doa(tx_coords[tx], rx_coords[rx])

    return (rx_doas_h, rx_doas_v), (tx_doas_h, tx_doas_v)

def compute_multiple_doas_for_queue(queue, rx_coords: np.ndarray, tx_coords: np.ndarray):
    """ Compute the Directions of arrival for a given set of receivers and transmitters coordinates """

    num_rx = len(rx_coords)
    num_tx = len(tx_coords)

    rx_shape = (num_rx, num_tx)
    tx_shape = (num_tx, num_rx)

    rx_doas_h = np.zeros(rx_shape, dtype=float)
    rx_doas_v = np.zeros(rx_shape, dtype=float)

    tx_doas_h = np.zeros(tx_shape, dtype=float)
    tx_doas_v = np.zeros(tx_shape, dtype=float)

    
    for rx in range(num_rx):
        for tx in range(num_tx):
            (rx_doas_h[rx, tx], rx_doas_v[rx, tx]) = compute_doa(rx_coords[rx], tx_coords[tx]) 
            
            (tx_doas_h[tx, rx], tx_doas_v[tx, rx]) = compute_doa(tx_coords[tx], rx_coords[rx])

    tuple = (rx_doas_h, rx_doas_v), (tx_doas_h, tx_doas_v)
    queue.put(tuple)



def vertical_angular_distance(angle, boresight):
    d_theta = np.abs(angle - boresight)
    return d_theta


def horizontal_angular_distance(angle, boresight): 
    d_phi = np.abs(
        np.arctan2( np.sin(angle - boresight), np.cos(angle - boresight))
        )
    return d_phi


def compute_multiple_relative_doas(rx_coords, tx_coords, rx_h_bsights, rx_v_bsights, num_rx_panels, num_tx_panels):

    # Converting from degrees to radians
    h_bsights = np.deg2rad(rx_h_bsights)
    v_bsights = np.deg2rad(rx_v_bsights)

    (num_rx, num_tx) = (len(rx_coords), len(tx_coords))

    rx_dim = (num_rx, num_tx, num_rx_panels, num_tx_panels)
    tx_dim = (num_tx, num_rx, num_tx_panels, num_rx_panels)

    rx_r_doas_h = np.zeros(rx_dim, dtype=float)
    rx_r_doas_v = np.zeros(rx_dim, dtype=float)


    for rx in range(num_rx):
        for tx in range(num_tx):
            (rx_doa_h, rx_doa_v) = compute_doa(rx_coords[rx], tx_coords[tx])
            for rx_p in range(num_rx_panels):

                    rx_r_doas_h[rx, tx, rx_p, :] = horizontal_angular_distance(rx_doa_h, h_bsights[rx, rx_p])
                    rx_r_doas_v[rx, tx, rx_p, :] = vertical_angular_distance(  rx_doa_v, v_bsights[rx, rx_p])

    return (rx_r_doas_h, rx_r_doas_v)

def compute_multiple_relative_doas_for_queue(queue, rx_coords, tx_coords, rx_h_bsights, rx_v_bsights, num_rx_panels, num_tx_panels):

    # Converting from degrees to radians
    h_bsights = np.deg2rad(rx_h_bsights)
    v_bsights = np.deg2rad(rx_v_bsights)

    (num_rx, num_tx) = (len(rx_coords), len(tx_coords))

    rx_dim = (num_rx, num_tx, num_rx_panels, num_tx_panels)
    tx_dim = (num_tx, num_rx, num_tx_panels, num_rx_panels)

    rx_r_doas_h = np.zeros(rx_dim, dtype=float)
    rx_r_doas_v = np.zeros(rx_dim, dtype=float)


    for rx in range(num_rx):
        for tx in range(num_tx):
            #print("COORDENADAS: ", rx_coords[rx], tx_coords[tx])
            (rx_doa_h, rx_doa_v) = compute_doa(rx_coords[rx], tx_coords[tx])
            for rx_p in range(num_rx_panels):

                    rx_r_doas_h[rx, tx, rx_p, :] = horizontal_angular_distance(rx_doa_h, h_bsights[rx, rx_p])
                    rx_r_doas_v[rx, tx, rx_p, :] = vertical_angular_distance(  rx_doa_v, v_bsights[rx, rx_p])



    tuple = (rx_r_doas_h, rx_r_doas_v)
    queue.put(tuple)

