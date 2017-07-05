# coding : utf-8

import numpy as np
from lib.common_functions import sigmoid, softmax, relu, gaussian_init

class Affine:
    def __init__(self, input_size, output_size, activation_function,
                 init_method="gaussian", train_flg = True):
        self.input_size = input_size
        self.output_size = output_size
        self.W = self.init_params(init_method)
        self.b = np.zeros(output_size)

        self.dW = None
        self.db = None
        self.x  = None
        self.activation_functions = np.array([activation_function]).flatten()

    def init_params(self, method_name):
        coeffs = {
                "gaussian": 0.01,
                "xavier"  : 1.0 / np.sqrt(self.input_size),
                "he"      : np.sqrt(2.0 / self.input_size),
                }

        return coeffs[method_name] * \
               np.random.randn(self.input_size, self.output_size)

    def forward(self, x, train_flg=True):
        self.x = x
        y = np.dot(self.x, self.W) + self.b
        
        for af in self.activation_functions:
            y = af.forward(y)

        return y

    def backward(self, dy):
        for af in reversed(self.activation_functions):
            dy = af.backward(dy)

        self.dW = np.dot(self.x.T, dy)
        self.db = np.sum(dy, axis=0)

        dx = np.dot(dy, self.W.T)

        return dx

    def set_params(self, W, b):
        self.W = W
        self.b = b

class Conv:
    def __init__(self, W, b, stride=1, padding=0,
                 activation_function, train_flg = True):

        self.W = W
        self.b = b

        self.S = stride
        self.P = padding

        self.dW = None
        self.db = None
        self.x  = None

    def forward(self, x):
        BS, IC, IH, IW = x.shape
        FN, C, FH, FW  = self.W.shape
        OH = int( (IH+2*self.P-FH) / self.S + 1 )
        OW = int( (IW+2*self.P-FW) / self.S + 1 )
        
        # forward
        X = im2col(x, FH, FW, self.S, self.P)
        W = self.W.reshape(FN, -1)
        Y = np.dot(X, W) + self.b
        y = Y.reshape(BS, OW, OH, -1).transpose(0, 3, 1, 2)

        # apply avtivation functions
        for af in self.activation_functions:
            y = af.forward(y)

        return y

    def backward(self, dy):
        pass
