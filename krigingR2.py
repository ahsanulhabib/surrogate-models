
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib import rc
import matplotlib
import scipy
from scipy.optimize import minimize
from matplotlib.colors import LogNorm

FONT_SIZE=14
font = {'family':'sans-serif', 'size':FONT_SIZE}

def printMat(mat, octave=False):
    if octave:
        print('['+';\n'.join([''.join(['{:10.3} '.format(item) for item in row]) for row in mat])+']')
    else:
        print('\n'.join([''.join(['{:10.3}\t'.format(item) for item in row]) for row in mat]))

# this is our sample function
def f(x):
    return math.sin(x) + 0.95 + 0.075*x**2 - 0.001*x**4

#calcs the correlation matrix
def calc_corMat(knwon_x, theta, p, plot_it=False):
    n = len(knwon_x)
    corMat = np.zeros((n, n))
    diff = []
    expFunc = []
    for row in range(0, n):
        for column in range(0, n):
            corMat[row][column] = math.exp(-theta * (abs(knwon_x[row] - knwon_x[column]) ** p))
            # since this is a symetric mat...
            # corMat[column][row] = corMat[row][column]
            diff.append(knwon_x[row] - knwon_x[column])
            expFunc.append(math.exp(-theta * (abs(knwon_x[row] - knwon_x[column]) ** p)))

    if plot_it:
        fig, ax = plt.subplots()
        # rc('text', usetex=True)
        rc('font', **font)
        rc('xtick', labelsize=FONT_SIZE)
        rc('ytick', labelsize=FONT_SIZE)
        plt.plot(diff, expFunc, 'bo', label='p=?, theta=?')
        ax.legend(loc=1, ncol=1)  # , mode="expand")
        ax.set_xlabel('x_i - x', fontdict=font)
        ax.set_ylabel('exp(-\theta |x_i-x|^p)', fontdict=font)
        ax.tick_params(labelsize=16., length=6, width=2)
        plt.tight_layout()
        plt.show()
    return corMat

#calcs the likelyhood
def calc_likelihood(known_x, known_val, theta, p):
    corMat = calc_corMat(known_x, theta, p)
    n = len(known_val)
    known_val = np.array(known_val)
    #LnDetCorMat = np.log(np.linalg.det(corMat))
    LnDetCorMat = np.linalg.slogdet(corMat)[1]
    one = np.ones((n, 1)).flatten()
    mu = (np.transpose(one) @ np.linalg.inv(corMat) @ known_val) / (np.transpose(one) @ np.linalg.inv(corMat) @ one)
    SigmaSqr = (np.transpose(known_val - one * mu) @ np.linalg.inv(corMat) @ (known_val - one * mu)) / n
    NegLnLike = (-1) * (-(n / 2) * np.log(SigmaSqr) - 0.5 * LnDetCorMat)
    if np.isnan(NegLnLike):
        print('Error: nan')
    return NegLnLike

def calc_likelihood_opti(params, *args):
    return calc_likelihood(args[0], args[1], params[0], params[1])

def predict(x_pred, knwon_x, knwon_val, theta, p):
    n = len(knwon_val)
    corMat = calc_corMat(knwon_x, theta, p)
    one = np.ones((n, 1)).flatten()
    mu = (np.transpose(one) @ np.linalg.inv(corMat) @ knwon_val) / (np.transpose(one) @ np.linalg.inv(corMat) @ one)
    psi = np.ones((n, 1)).flatten()
    for i in range(0, len(psi)):
        psi[i] = math.exp(-theta * (abs(knwon_x[i] - x_pred) ** p))
    fx = mu + np.transpose(psi) @ np.linalg.inv(corMat) @ (knwon_val - one * mu)
    return fx

if __name__ == '__main__':
    # the smooth whole function
    fx = np.linspace(1, 11, 1001)
    fy = list(map(f,fx))
    # now we pretend we only know a view points
    px = [1., 3., 5., 7., 9., 11.]
    py = list(map(f,px))
    #first fixed exponent here
    p = 2.
    #first fixed factor here
    theta = .5

    #standardDeviation = np.std(py)
    #sigma = standardDeviation

    NegLnLike = calc_likelihood(px, py, theta, p)
    print('negLnLike = ' + str(NegLnLike))

    #thetas = np.linspace(0.01, 10, 1000+1)
    thetas = np.logspace(-2, 1, num=5000)
    ps = [2.]#np.linspace(1., 2., 100)
    likely = np.zeros((len(ps), len(thetas)))
    for it in range(0, len(thetas)):
        for ip in range(0, len(ps)):
            likely[ip][it] = calc_likelihood(px, py, thetas[it], ps[ip])

    x0 = [1., 2.]
    bnds = [(0.0001, 1000.), (1., 2.)]
    res = minimize(calc_likelihood_opti, x0, args=(px, py), method='SLSQP', tol=1e-11, bounds=bnds)

    bestTheta = res.x[0]
    bestP = res.x[1]
    minLike = calc_likelihood(px, py, bestTheta, bestP)
    print('minLike = '+str(minLike))
    print('@theta = ' + str(bestTheta))
    print('@p = ' + str(bestP))
    fig, ax = plt.subplots()
    rc('text', usetex=True)
    rc('font', **font)
    rc('xtick', labelsize=FONT_SIZE)
    rc('ytick', labelsize=FONT_SIZE)
    ax.semilogx(thetas, likely[-1])
    ax.semilogx(bestTheta, minLike, 'rx', markersize=10, label='Minimum')
    ax.set_xlabel(r'$\theta$', fontdict=font)
    ax.set_ylabel(r'Likelihood', fontdict=font)
    ax.legend(loc='upper right', ncol=1)
    fig.set_size_inches(7, 4)
    plt.tight_layout()
    plt.savefig('dataOut/krigingR2likelihood.svg')
    plt.savefig('dataOut/krigingR2likelihood.pdf')
    plt.show()

    fig, ax = plt.subplots()
    ax.set_xscale('log')
    pcol = ax.pcolor(thetas, ps, likely, cmap='viridis_r')
    fig.colorbar(pcol)
    ax.plot(bestTheta, bestP, 'rx')
    ax.set_xlabel('$\theta$', fontdict=font)
    ax.set_ylabel('p', fontdict=font)
    plt.show()

    fig, ax = plt.subplots()
    #rc('text', usetex=True)
    rc('font', **font)
    rc('xtick', labelsize=FONT_SIZE)
    rc('ytick', labelsize=FONT_SIZE)

    krigY = np.zeros((len(fx),1)).flatten()
    for i in range(0, len(fx)):
        krigY[i] = predict(fx[i], px, py, bestTheta, bestP)
    ax.plot(fx, krigY, 'b-', label=r'$f_{kriging}$ mit $\theta = '+'{0:.3f}'.format(bestTheta)+'$, $p = '+'{0:.1f}'.format(bestP)+'$')

    ax.plot(fx, fy, 'r-', label=r'$f_{original}$')
    ax.plot(px, py, 'ro', label=r'St\"utzstellen', markersize=10)
    ax.legend(loc='lower left', ncol=1)#, mode="expand")
    ax.set_xlabel('Eingang', fontdict=font)
    ax.set_ylabel('Ausgang', fontdict=font)
    ax.tick_params(labelsize=16., length=6, width=2)
    fig.set_size_inches(8, 5)
    plt.tight_layout()
    plt.savefig('dataOut/krigingR2.svg')
    plt.savefig('dataOut/krigingR2.pdf')
    plt.show()
