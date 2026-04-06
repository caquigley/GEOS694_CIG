from mpi4py import MPI
import numpy as np
import random
import math

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank ==0:
    val = random.randint(1,10)
    statement = "Hello world! "+str(val)
    print(statement)
    #print('Hello world! '+str(val))
    comm.send(statement, dest=1, tag = rank)
    comm.send(val, dest=1, tag = rank+1)
    statement = comm.recv(source=size-1, tag = size-1)
    print(statement)
elif rank == size-1:
    statement = comm.recv(source=rank-1, tag = rank-1)
    statement = statement + " goodbye world!"
    comm.send(statement, dest = 0, tag = rank)
else:
    statement = comm.recv(source=rank-1, tag=rank-1)
    val = comm.recv(source=rank-1, tag = rank)
    val = val*rank
    statement = statement+' '+str(val)
    comm.send(statement, dest = rank+1, tag = rank)
    comm.send(val, dest = rank+1, tag = rank+1)
    #print(statement)

