cimport numpy as cnp
import numpy as np

def getEventPtrs( cnp.ndarray[cnp.uint64_t, ndim=1] tstamps, \
                  size_t timeThresh ):
  '''Similar to the interaction grouping except doesn't actually group the data
     together, just finds the indices corresponding to the beginning and end of
     events'''
  # Initializations and typing
  cdef size_t i = 0
  cdef size_t aryLen = len(tstamps)
  cdef size_t n
  cdef size_t ind = 1
  cdef cnp.ndarray[cnp.uint64_t, ndim=1] ptrs = np.zeros_like( tstamps )
  cdef cnp.ndarray[cnp.uint64_t, ndim=1] lens = np.zeros_like( tstamps )
  ptrs[0] = 0
  # Do the work
  while i < aryLen:
    n = 1
    while( i+n < aryLen ) and ( tstamps[i+n] <= tstamps[i] + timeThresh ):
      n += 1
    # Check for validity: only take events that are 
    if (n >= 5 and n <= 18):
      ptrs[ind] = i
      lens[ind] = n
      ind += 1
    i += n
  return ptrs[ptrs != 0], lens[lens != 0]
