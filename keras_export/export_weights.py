import json
import sys

from keras.models import load_model
from keras import backend as K

import numpy as np

def write_text_file(path, text):
    with open(path, "w") as text_file:
        print(text, file=text_file)

def show_conv2d_layer(layer):
    weights = layer.get_weights()
    weight_flat = np.swapaxes(weights[0], 0, 2).flatten().tolist()
    assert len(weight_flat) > 0
    assert layer.dilation_rate == (1,1)
    assert layer.padding in ['valid', 'same']
    assert len(layer.input_shape) == 4
    assert layer.input_shape[0] == None
    return {
        'weights': weight_flat,
        'biases': weights[1].tolist()
    }

def show_batch_normalization_layer(layer):
    assert layer.axis == -1
    return {
        'gamma': K.get_value(layer.gamma).tolist(),
        'beta': K.get_value(layer.beta).tolist()
        }

def show_dense_layer(layer):
    assert len(layer.input_shape) == 2, "Please flatten for dense layer."
    assert layer.input_shape[0] == None, "Please flatten for dense layer."
    assert layer.use_bias == True
    assert layer.kernel_constraint == None
    assert layer.bias_constraint == None
    weights, bias = layer.get_weights()
    return {
        'weights': weights.flatten().tolist(),
        'bias': bias.tolist()
        }

def get_dict_keys(d):
    return [key for key in d]

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z

def merge_two_disjunct_dicts(x, y):
    assert set(get_dict_keys(x)).isdisjoint(get_dict_keys(y))
    return merge_two_dicts(x, y)

def is_ascii(str):
    try:
        str.encode('ascii')
    except UnicodeEncodeError:
        return False
    else:
        return True

def get_all_weights(model):
    show_layer_functions = {
        'Conv2D': show_conv2d_layer,
        'BatchNormalization': show_batch_normalization_layer,
        'Dense': show_dense_layer
    }
    result = {}
    layers = model.layers
    for layer in layers:
        layer_type = type(layer).__name__
        if layer_type in ['Model', 'Sequential']:
            result = merge_two_disjunct_dicts(result, get_all_weights(layer))
        else:
            show_func = show_layer_functions.get(layer_type, None)
            name = layer.name
            is_ascii(name)
            if show_func:
                result[name] = show_func(layer)
    return result

def main():
    usage = 'usage: [Keras model in HDF5 format] [output path]'
    if len(sys.argv) != 3:
        print(usage)
        sys.exit(1)
    else:
        in_path = sys.argv[1]
        out_path = sys.argv[2]
        model = load_model(in_path)
        weights = get_all_weights(model)
        write_text_file(out_path,
            json.dumps(weights, allow_nan=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()