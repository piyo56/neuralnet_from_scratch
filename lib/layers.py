# coding : utf-8

import numpy as np
from lib.common_functions import sigmoid, softmax, relu, gaussian_init

class Affine:
    def __init__(self, input_size, output_size, activate_function,
                 init_method="gaussian"):
        self.input_size = input_size
        self.output_size = output_size
        self.W = self.init_params(init_method)
        self.b = np.zeros(output_size)

        self.dW = None
        self.db = None
        self.x  = None
        self.activate_function = activate_function

    def init_params(self, method_name):
        coeffs = {
                "gaussian": 0.01,
                "xavier"  : np.sqrt(self.input_size),
                "he"      : np.sqrt(2.0 / self.input_size),
                }

        return coeffs[method_name] * \
               np.random.randn(self.input_size, self.output_size)

    def forward(self, x):
        self.x = x
        y = np.dot(self.x, self.W) + self.b

        return self.activate_function.forward(y)

    def backward(self, dy):
        dy = self.activate_function.backward(dy)

        self.dW = np.dot(self.x.T, dy)
        self.db = np.sum(dy, axis=0)

        dx = np.dot(dy, self.W.T)

        return dx

    def set_params(self, W, b):
        self.W = W
        self.b = b
