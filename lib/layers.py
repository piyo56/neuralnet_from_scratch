# coding : utf-8

import sys, os
sys.path.append(os.pardir)
import numpy as np
from lib.common_functions import *
from lib.utils import im2col, col2im

class Affine:
    def __init__(self, input_size, output_size, init_method="gaussian"):

        self.input_size = input_size
        self.output_size = output_size
        self.W = self.init_params(init_method)
        self.b = np.zeros(output_size)

        self.dW = None
        self.db = None
        self.x  = None

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

        return y

    def backward(self, dy):

        self.dW = np.dot(self.x.T, dy)
        self.db = np.sum(dy, axis=0)

        dx = np.dot(dy, self.W.T)

        return dx.reshape(self.org_shape)

    def set_params(self, W, b):
        self.W = W
        self.b = b

    def update(self, lr):
        self.W -= lr * self.dW
        self.b -= lr * self.db

class Conv:
    def __init__(self, filter_shape, stride=1, padding=0, 
                 init_method="gaussian", train_flg = True):
        
        # self.C, self.IH, self.IW = input_shape
        self.FN, self.C, self.FH, self.FW = filter_shape

        self.W = self.init_params(init_method)
        self.b = np.zeros(self.FN)
        self.S = stride
        self.P = padding

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

        return y

    def backward(self, dy):
        FN, C, FH, FW = self.W.shape
        dy = dy.transpose(0, 2, 3, 1).reshape(-1, FN)

        self.db = np.sum(dy, axis=0)
        self.dW = np.dot(self.col_x.T, dy)
        self.dW = self.dW.transpose(1, 0).reshape(FN, C, FH, FW)

        dcol = np.dot(dy, self.col_W.T)
        dx = col2im(dcol, self.x.shape, FH, FW, self.S, self.P)
        return dx

    def update(self, lr):
        self.W -= lr * self.dW
        self.b -= lr * self.db

class Sigmoid:
    def __init__(self):
        self.x = None
        self.y = None

    def forward(self, x, train_flg=True):
        self.x = x
        self.y = sigmoid(x)

        return self.y
    
    def backward(self, dy):
        dx = dy * (1.0 - self.y) * self.y
        
        return dx

    def update(self, lr = 0.1):
        pass

class Relu:
    def __init__(self):
        self.x = None
        self.y = None

    def forward(self, x, train_flg=True):
        self.x = x
        self.y = relu(self.x)

        return self.y

    def backward(self, dy):
        dx = dy.copy()
        dx[ self.x<=0 ] = 0

        return dx

    def update(self, lr = 0.1):
        pass

class Softmax:
    def __init__(self):
        self.x = None

    def forward(self, x, train_flg=True):
        self.x = x
        y = softmax(self.x)

        return y
    
    def backward(self, dy):
        batch_size = self.x.shape[0]
        dx = dy / batch_size
        
        return dx

    def update(self, lr = 0.1):
        pass

class BatchNormalization:
    def __init__(self, lr=0.1):
        self.eps        = 1e-7
        self.batch_size = None

        self.x      = None
        self.x_norm = None
        self.x_c    = None
        self.mu     = None
        self.var    = None

        self.gamma  = None
        self.beta   = 0.0
        self.dbeta  = None
        self.dgamma = None

    def forward(self, x, train_flg=True):
        if x.ndim != 2:
            self.x = x.reshape(x.shape[0], -1)
        else:
            self.x = x

        self.batch_size = x.shape[0]
        self.input_dim = x.shape[1]

        if self.gamma is None:
            self.gamma = np.ones(self.input_dim, )

        self.mu = np.mean(x, axis = 0)
        self.std = np.std(x, axis = 0)
        self.xc = x - self.mu

        self.x_norm = self.xc / (self.std + self.eps)
        y = self.gamma * self.x_norm + self.beta

        return y

    def backward(self, dy):
        self.dbeta = np.sum(dy)
        self.dgamma = np.sum(self.x_norm * dy, axis = 0)

        dx_norm = dy * self.gamma

        dxc = dx_norm / self.std
        dstd = -np.sum(dx_norm * self.xc / (self.std * self.std), axis=0)
        dvar = 0.5 * dstd / self.std
        dxc += 2.0 / self.batch_size * self.xc * dvar
        dmu = np.sum(dxc, axis=0)
        dx = dxc - dmu / self.batch_size
        # dx = dxc * ( 1.0 - 1.0 / self.batch_size)

        return dx

    def update(self, lr = 0.1):
        self.gamma -= lr * self.dgamma
        self.beta  -= lr * self.dbeta

class Dropout:
    def __init__(self, dropout_rate=0.5):
        self.dropout_rate = dropout_rate

    def forward(self, x, train_flg=True):
        if train_flg:
            self.mask = np.random.rand(*x.shape) > self.dropout_rate
            return x * self.mask
        else:
            return x

    def backward(self, dy):
        return dy * self.mask

    def update(self, lr = 0.1):
        pass

class Pooling:
    def __init__(self, FH, FW, padding=0, stride=1):
        self.FH = FH
        self.FW = FW
        self.S = stride
        self.P = padding

    def forward(self, x, train_flg=True):
        BS, C, IH, IW = x.shape
        OH = int( (IH+2*self.P-self.FH) / self.S + 1 )
        OW = int( (IW+2*self.P-self.FW) / self.S + 1 )

        col_x = im2col(x, self.FH, self.FW, self.S, self.P)
        col_x = col_x.reshape(-1, self.FW*self.FH)

        arg_max = np.argmax(col_x, axis=1)
        col_y = np.max(col_x, axis = 1)
        y = col_y.reshape(BS, OH, OW, C).transpose(0, 3, 1, 2)

        self.x = x
        self.arg_max = arg_max

        return y

    def backward(self, dy):
        dy = dy.transpose(0, 2, 3, 1)
        
        pool_size = self.FH * self.FW
        dmax = np.zeros((dy.size, pool_size))
        dmax[np.arange(self.arg_max.size), self.arg_max.flatten()] = dy.flatten()
        dmax = dmax.reshape(dy.shape + (pool_size,)) 
        
        dcol = dmax.reshape(dmax.shape[0] * dmax.shape[1] * dmax.shape[2], -1)
        dx = col2im(dcol, self.x.shape, self.FH, self.FW, self.S, self.P)
        
        return dx

    def update(self, lr = 0.1):
        pass

class LRN:
    """
    Local Response Normalization
    """
    def __init__(self, alpha=1e-4, k=2, beta=0.75, n=5):
        self.alpha = alpha
        self.k = k
        self.beta = beta
        self.n = n
        self.r = int(self.n / 2.0)
        
        self.x = None
        self.d2 = None
        self.d3 = None
        self.sums = None

    def forward(self, x, train_flg=True):
        BN, C, IH, IW = x.shape
        x = x.transpose(1, 0, 2, 3).reshape(C, BN, -1)

        _sums = np.sum(np.power(x, 2), axis=2)
        sums = np.zeros( (C, BN, ) )
        for i in range(C):
            s = max(0, i-self.r)
            e = min(C, i+self.r)
            sums[i] = np.sum(_sums[s:e], axis=0)

        sums = sums.reshape((C, BN, 1))
        d2 = self.k + self.alpha * sums
        d3 = np.power(d2, -self.beta)

        y = x * d3
        y = y.reshape(C, BN, IH, IW).transpose(1, 0, 2, 3)

        self.x = x
        self.d2 = d2
        self.d3 = d3
        self.sums = sums

        return y

    def backward(self, dy):
        BN, C, IH, IW = dy.shape
        dy = dy.transpose(1, 0, 2, 3).reshape(C, BN, -1)

        dx = dy * self.d3

        dd3 = self.x * dy
        dd2 = dd3 * -self.beta * np.power(self.d2, -(self.beta+1))
        
        # dd1 = np.zeros_like(dd2)
        # ones = np.ones((BN, IH*IW))

        # TODO: should simplify
        # for i in range(C):
        #     s = max(0, i-self.r)
        #     e = min(C, i+self.r)
        #     dd1[s:e] += ones

        dx += dd2 * 2.0 * self.alpha * self.sums # dd1 

        dx = dx.reshape(C, BN, IH, IW).transpose(1, 0, 2, 3)

        return dx

    def update(self, lr = 0.1):
        pass
