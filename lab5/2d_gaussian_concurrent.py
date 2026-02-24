import time
import numpy as np
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys
import os
'''
Plots a 2D Gaussian curve.

Terminal example:

python 2d_gaussian.py xmin xmax ymin ymax

Inputs to change in code:
STEP: size of step for computation
main(xmin, xmax, ymin, ymax): sets the bounds to do the gaussian over.


'''
####INPUTS######
STEP = .0005
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

def runtime_plot():
    fig, ax = plt.subplots()
    times = np.array([42.93652415275574, 22.389034032821655, 14.734593152999878,
                      11.91014289855957, 9.557326078414917, 7.992908000946045,
                      7.233935117721558, 6.227513790130615, 6.199244022369385,
                        5.911754131317139])
    cores = np.array([1,2,3,4,5,6,7,8,9,10])
    ax.scatter(times, cores, color = 'firebrick')
    ax.plot(times, cores, color = 'gray', alpha = 0.3)
    ax.grid(alpha = 0.3)
    ax.set_xlabel('Run time (seconds)')
    ax.set_ylabel('Number of cores')

#Concurrent 1: 42.93652415275574s
#Concurrent 2: 22.389034032821655s
#Concurrent 3: 14.734593152999878s
#Concurrent 4: 11.91014289855957s
#Concurrent 5: 9.557326078414917s
#Concurrent 6: 7.992908000946045s
#Concurrent 7: 7.233935117721558s
#Concurrent 8: 6.227513790130615s
#Concurrent 9: 6.199244022369385s
#Concurrent 10: 5.911754131317139s

#Computing the Gaussian and plotting--------
def main(xmin, xmax, ymin, ymax, sigma=1):
    X = np.arange(float(xmin), float(xmax), STEP)
    Y = np.arange(float(ymin), float(ymax), STEP)
    Z = []  # 1D array
    for x in X:
        for y in Y:
            Z.append(gaussian2D(x, y, sigma))
    ZZ = np.array(Z).reshape(len(X), len(Y))  # 2D array
    #return ZZ
    #plot(ZZ)
    #plt.show()
    return ZZ

#Running it all-----------
if __name__ == "__main__":
    if len(sys.argv) == 6:
        start = time.time()
        nproc = int(sys.argv[5])
        xmin = int(sys.argv[1])
        xmax = int(sys.argv[2])
        ymin = int(sys.argv[3])
        ymax = int(sys.argv[4])
        N = xmax - xmin
        #step = N // nproc
        step = N / nproc
        
        
        with ProcessPoolExecutor(max_workers=nproc) as executor:
            #futures = [executor.submit(main, i, i+step, j, j+step)
            futures = [executor.submit(main, xmin+(step*i), xmin+(i+1)*step, ymin, ymax)
                    for i in range(nproc)] #executor.submit
            #executor.map(main, xmin+step, xmin*step, ymin, ymax)

                       #for i in range(xmin, xmax, step)
                       #for j in range(ymin, ymax, step)]
            
            #results_list = []
            #for future in as_completed(futures):
                #results_list += future.result()
                #results_list.append(future.result())
            results_list = [f.result() for f in futures]
            
    elapsed = time.time() - start
    print(f"Elapsed Time: {elapsed}s")
    print(os.cpu_count())
    results = np.vstack(results_list)
    plot(results)
    runtime_plot()
    
    plt.show()
    #print(os.cpu_count())
                
        #result = main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    
    #main(xmin, xmax, ymin, ymax) #sets the bounds for computing
    #elapsed = time.time() - start
    #print(f"Elapsed Time: {elapsed}s")
        #plt.show()

#Serial: 39.315 s
#Concurrent 1: 42.93652415275574s
#Concurrent 2: 22.389034032821655s
#Concurrent 3: 14.734593152999878s
#Concurrent 4: 11.91014289855957s
#Concurrent 5: 9.557326078414917s
#Concurrent 6: 7.992908000946045s
#Concurrent 7: 7.233935117721558s
#Concurrent 8: 6.227513790130615s
#Concurrent 9: 6.199244022369385s
#Concurrent 10: 5.911754131317139s

#