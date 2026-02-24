import time
import numpy as np
import matplotlib.pyplot as plt
import sys
'''
Plots a 2D Gaussian curve.

Terminal example:

python 2d_gaussian.py xmin xmax ymin ymax

Inputs to change in code:
STEP: size of step for computation
main(xmin, xmax, ymin, ymax): sets the bounds to do the gaussian over.


'''
####INPUTS######
STEP = .001
#xmin = -2
#xmax = 2
#ymin = -2
#ymax = 2
#--------------------

#Function for computing 2D Gaussian-------------
def gaussian2D(x, y, sigma): 
    return (1/(2*np.pi*sigma**2))*np.exp(-1*(x**2+y**2)/(2*sigma**2))

#Function for plotting Gaussian-----
def plot(z):
    plt.imshow(z.T)
    plt.gca().invert_yaxis()  # flip axes to get imshow to plot representatively
    plt.xlabel("X"); plt.ylabel("Y"); plt.title(f"{z.shape} points")
    plt.gca().set_aspect(1)

#Computing the Gaussian and plotting--------
def main(xmin, xmax, ymin, ymax, sigma=1):
    X = np.arange(float(xmin), float(xmax), STEP)
    Y = np.arange(float(ymin), float(ymax), STEP)
    Z = []  # 1D array
    for x in X:
        for y in Y:
            Z.append(gaussian2D(x, y, sigma))
    ZZ = np.array(Z).reshape(len(X), len(Y))  # 2D array
    plot(ZZ)

#Running it all-----------
if __name__ == "__main__":
    if len(sys.argv) == 5:
        start = time.time()
        result = main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    
    #main(xmin, xmax, ymin, ymax) #sets the bounds for computing
        elapsed = time.time() - start
        print(f"Elapsed Time: {elapsed}s")
        plt.show()