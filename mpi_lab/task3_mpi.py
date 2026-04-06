from mpi4py import MPI
import numpy as np
import random


comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

data1 = random.randint(0,1000)

value = comm.reduce(data1, op = MPI.MAX, root = 0)
glob = comm.bcast(value, root = 0) #broadcasts to all values

if glob == data1:
    print(f"Rank: {rank} has value {data1} which is the global max {glob}")
else:
    print(f"Rank: {rank} has value {data1} which is less than global max {glob}")


