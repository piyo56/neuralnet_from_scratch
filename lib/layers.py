# coding : utf-8

import numpy as np
from lib.common_functions import sigmoid, softmax, relu
from lib.utils import im2col, col2im

class Affine:
    def __init__(self, input_size, output_size, activation_function,
                 init_method="gaussian"):

        self.input_size = input_size
        self.output_size = output_size
        self.W = self.init_params(init_method)
        self.b = np.zeros(output_size)

        self.dW = None
        self.db = None
        self.x  = None
        self.activation_functions = np.array([activation_function]).flatten()

        self.org_shape = None

    def init_params(self, method_name):
        coeffs = {
                "gaussian": 0.01,
                "xavier"  : 1.0 / np.sqrt(self.input_size),
                "he"      : np.sqrt(2.0 / self.input_size),
                }

        return coeffs[method_name] * \
               np.random.randn(self.input_size, self.output_size)

    def forward(self, x, train_flg=True):
        self.org_shape = x.shape
        self.x = x.reshape(x.shape[0], -1)

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

        return dx.reshape(self.org_shape)

    def set_params(self, W, b):
        self.W = W
        self.b = b

class Conv:
    def __init__(self, activation_function,
                 # input_shape,
                 filter_shape, stride=1, padding=0,
                 init_method="gaussian", train_flg = True):
        
        # self.C, self.IH, self.IW = input_shape
        self.FN, self.C, self.FH, self.FW = filter_shape

        self.W = self.init_params(init_method)
        self.b = np.zeros(self.FN)
        self.S = stride
        self.P = padding

        self.activation_functions = np.array([activation_function]).flatten()

        self.dW = None
        self.db = None
        self.x  = None

    def init_params(self, method_name):
        coeffs = {
                "gaussian": 0.01,
                }
        gaussian_rands = np.random.randn(self.FN, self.C, self.FH, self.FW)

        return coeffs[method_name] * gaussian_rands

    def forward(self, x, train_flg=True):
        BS, IC, IH, IW = x.shape
        FN, C, FH, FW  = self.W.shape
        OH = int( (IH+2*self.P-FH) / self.S + 1 )
        OW = int( (IW+2*self.P-FW) / self.S + 1 )
        
        # forward
        col_x = im2col(x, FH, FW, self.S, self.P)
        col_W = self.W.reshape(-1, FN)
        col_y = np.dot(col_x, col_W) + self.b
        y = col_y.reshape(BS, OW, OH, -1).transpose(0, 3, 1, 2)

        self.x = x
        self.col_x = col_x
        self.col_W = col_W

        # apply avtivation functions
        for af in self.activation_functions:
            y = af.forward(y)

        return y

    def backward(self, dy):
        for af in reversed(self.activation_functions):
            dy = af.backward(dy)

        FN, C, FH, FW = self.W.shape
        dy = dy.transpose(0, 2, 3, 1).reshape(-1, FN)

        self.db = np.sum(dy, axis=0)
        self.dW = np.dot(self.col_x.T, dy)
        self.dW = self.dW.transpose(1, 0).reshape(FN, C, FH, FW)

        dcol = np.dot(dy, self.col_W.T)
        dx = col2im(dcol, self.x.shape, FH, FW, self.S, self.P)

        return dx
