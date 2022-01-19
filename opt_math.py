from neural_net import get_nn
import globalvars as gv
# TEST COMMIT
def target_price_formula(open_prc, vlt, is_short):

    diff = vlt[-1] - vlt[0]
    if vlt[-1] < 2.5:
        return open_prc
    else:
        return open_prc
def target_dist_formula(dist_prc, vlt):

    diff = vlt[-1] - vlt[0]
    if diff < -2000:
        return dist_prc
    else:
        return dist_prc
