import numpy as np
w_input, w1_2, w_out, x_shift, x_span, y_shift, y_span = None, None, None, 0,0,0,0
sample_length = 0
l_out_mean_error = 0
def save_nn_input(res,vlt_sample_size):
    if vlt_sample_size > 1:
        cols = ''
        for i in range(vlt_sample_size):
            cols = cols + 'vlt%d,' % i
        cols = cols + 'right_premium0'
        cols = cols.split(',')
        res[cols].to_csv('../math_files/nn_input.csv', index=False)


def normalize(arr,x_shift_arg=0, x_span_arg=0,tanh=False):
    global x_shift, x_span, y_shift, y_span
    if tanh:
        if x_shift_arg == 0 and x_span_arg == 0:
            x_max = np.max(arr[:,:sample_length])
            x_min = np.min(arr[:,:sample_length])
            y_max = np.max(arr[:,sample_length])
            y_min = np.min(arr[:,sample_length])
            x_shift = (x_max + x_min) / 2
            x_span = x_max - x_min
            y_shift = (y_max + y_min) / 2
            y_span = y_max - y_min
            x = 2.0 * (arr[:, :sample_length] - x_shift) / x_span
            y = 2.0 * (arr[:, sample_length] - y_shift) / y_span
            return x, y, y_shift, y_span
        else:
            x_shift, x_span = x_shift_arg, x_span_arg
            x = 2.0 * (arr[:, :sample_length] - x_shift) / x_span
            return x
    else:
        if x_shift_arg == 0 and x_span_arg == 0:
            x_max = np.max(arr[:,:sample_length])
            x_min = np.min(arr[:,:sample_length])
            y_max = np.max(arr[:,sample_length])
            y_min = np.min(arr[:,sample_length])
            x_span = x_max - x_min
            y_shift = y_min
            y_span = y_max - y_min
            x = (arr[:, :sample_length] - x_shift) / x_span
            y = (arr[:, sample_length] - y_shift) / y_span
            return x, y, y_shift, y_span
        else:
            x_shift, x_span = x_shift_arg, x_span_arg
            x = 2.0 * (arr[:, :sample_length] - x_shift) / x_span
            return x



def denormalize(y, tanh=True):
    if tanh:
        return (y * y_span) / 2. + y_shift
    else:
        return y * y_span + y_shift


def save(out):
    global w_input, w1_2, w_out, y_shift, y_span
    if len(out) > 0:
        np.savetxt('../math_files/nn_out.csv',  out,fmt='%.4f',delimiter=',')
    if len(w_input) > 0:
        np.savetxt('../math_files/w_input.csv',  w_input,delimiter=',')
    if len(w1_2) > 0:
        np.savetxt('../math_files/w1_2.csv',  w1_2,delimiter=',')
    if len(w_out) > 0:
        np.savetxt('../math_files/w_out.csv', w_out,delimiter=',')
    xy_norm = np.array([[x_shift, x_span],[y_shift, y_span]])
    np.savetxt('../math_files/xy_norm.csv', xy_norm,delimiter=',')

def sigm(x,derivative=False):
    if derivative:
        return x*(1-x)
    return 1/(1+np.exp(-x))

def tan(x, derivative=False):
    if derivative:
        return 1. / pow(np.cosh(x), 2)
    return np.tanh(x)
def lin(x,derivative=False):
    if derivative:
        return 1.
    return x

def activate(x, derivative=False, sig=True):
    if sig:
        return sigm(x, derivative)
    else:
        return lin(x, derivative)
def calc_error(desired_value, nn_value):
    delta = desired_value - nn_value
    return delta
def set_initial_weights(seed=1):
    global w_input, w1_2, w_out  # = None, None, None
    if seed:
        np.random.seed(seed)  # for same results each run
    if h1 > 0:
        w_input = (2 * np.random.random((sample_length, h1)) - 1)
        if h2 > 0:
            w1_2 = (2 * np.random.random((h1, h2)) - 1)
            w_out = (2 * np.random.random((h2, 1)) - 1)
        else:
            w_out = (2 * np.random.random((h1, 1)) - 1)
    else:
        w_input = (2 * np.random.random((sample_length, 1)) - 1)
    return w_input, w1_2, w_out

def activate_layers(x):
    global w_input, w1_2, w_out
    if h1 > 0:
        l1 = activate(np.dot(x, w_input))
        if h2 > 0:
            l2 = activate(np.dot(l1, w1_2))
            l_out = activate(np.dot(l2, w_out))
        else:
            l_out = activate(np.dot(l1, w_out))
            l2 = None
    else:
        l_out = activate(np.dot(x, w_input)).reshape(-1,1)
        l1, l2 = None, None
    return l1,l2,l_out

def propagate(x, y):       # , w_input, w1_2, w_out):
    global w_input, w1_2, w_out    # weights


    global lr, l_out_mean_error    # learning rate, l_out_mean_error
    l1, l2, l_out = activate_layers(x)  #
    xf = y - l_out
    yf = xf
#    yf = np.cbrt(xf)
    l_out_error = yf
    # l_out_error = y - l_out
    l_out_mean_error = float(np.mean(np.abs(l_out_error)))
# --------------------------  back propagation: ----------------------------
    if h1 > 0:
        if h2 > 0:
            l_out_delta = l_out_error * activate(l_out, derivative=True)
            l2_error = l_out_delta.dot(w_out.T)
            l2_delta = l2_error * activate(l2, derivative=True)
            l1_error = l2_delta.dot(w1_2.T)
            l1_delta = l1_error * activate(l1, derivative=True)
            w_out += lr * l2.T.dot(l_out_delta)
            w1_2 += lr * l1.T.dot(l2_delta)
            w_input += lr * x.T.dot(l1_delta)
        else:
            l_out_delta = l_out_error * activate(l_out, derivative=True)
            l1_error = l_out_delta.dot(w_out.T)
            l1_delta = l1_error * activate(l1, derivative=True)
            w_out += lr * l1.T.dot(l_out_delta)
            w_input += lr * x.T.dot(l1_delta)
    else:
        l_out_delta = l_out_error * activate(l_out, derivative=True)
        w_input = lr * x.T.dot(l_out_delta)
    return l_out, l_out_error,w_input, w1_2, w_out



def train():
    global w_input, w1_2, w_out, y_shift, y_span,sample_length
    fn = '../math_files/nn_input.csv'
    src_data = np.loadtxt(fn, delimiter=',',skiprows=1)
    sample_length = np.shape(src_data)[1] - 1
    w_input, w1_2, w_out = set_initial_weights()
    x, y, y_shift, y_span = normalize(src_data)  # x-input series, y-desired output, y_shift,
                                                 # y_span will be used for denormalisation of y
    # save normalized input data to file, just for record
    nn_input_norm = np.hstack([x,y.reshape(-1,1)])
    np.savetxt('../math_files/nn_input_norm.csv',nn_input_norm,delimiter=',')

    y = y.reshape(-1,1)
    out = None  # supress python warning

    # train net:
    for i in range(iterations):
        out, out_err,w_input, w1_2, w_out = propagate(x, y)
        mean_err = float(np.mean(np.abs(out_err)))
        if i % mid == 0 or i == iterations - 1:
            print(i,mean_err)

    # save normalized input and output data
    nn_out_norm = np.hstack([nn_input_norm,out])
    np.savetxt('../math_files/nn_out_norm.csv',nn_out_norm,fmt='%.6f',delimiter=',')
    out_denormalized = denormalize(out)   #
    out_arr = np.hstack([src_data,out_denormalized])
    save(out_arr)


def get_nn(vlt):
    global w_input, w1_2, w_out, x_shift, x_span, y_shift, y_span,sample_length
    if w_input is None:
        path = '../math_files'
        w_input = np.loadtxt('%s/w_input.csv' % path, delimiter=',')
        w1_2 = np.loadtxt('%s/w1_2.csv' % path, delimiter=',')
        w_out = np.loadtxt('%s/w_out.csv' % path, delimiter=',')
        xy_norm = np.loadtxt('%s/xy_norm.csv' % path, delimiter=',')
        x_shift, x_span = xy_norm[0,0], xy_norm[0,1]
        y_shift, y_span = xy_norm[1,0], xy_norm[1,1]
        w_input_size = np.shape(w_input)[0]
        vlt_len = len(vlt)
        sample_length = w_input_size
        if vlt_len > 0 and not vlt_len == w_input_size:
            exit('wrong dim')
        elif vlt_len == 0:
            return sample_length
    x_arr = np.array(vlt).reshape(1,sample_length)
    x = normalize(x_arr,x_shift,x_span)
    dum, dum, out = activate_layers(x)
    y = denormalize(out)
    return y

iterations = 100000
mid = 500
h1 = 10
h2 = 10
lr = 0.01
# train()


