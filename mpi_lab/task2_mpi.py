from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

num_data = 1000
data = None
if rank ==0:
    data = np.arange(0,num_data, 1)
    data = np.array_split(data,size)
    print('Sum of all data points:', np.sum(data))

partial = np.empty(int(num_data/size), dtype = 'd')
partial = comm.scatter(data,root= 0)

reduced = None

if rank ==0:
    reduced = np.empty(size, dtype = 'd')

summ = comm.gather(np.sum(partial), root = 0)

if rank ==0:
    print('Full sum:', np.sum(summ))
