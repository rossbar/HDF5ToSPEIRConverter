cimport numpy as cnp
import numpy as np

def getEventPtrs( cnp.ndarray[cnp.uint64_t, ndim=1] tstamps, \
                  size_t timeThresh, size_t evSizeMin = 2, \
                  size_t evSizeMax = 18 ):
  '''Similar to the interaction grouping except doesn't actually group the data
     together, just finds the indices corresponding to the beginning and end of
     events. Will only consider events where the final number of readouts are
     in the range [evSizeMin, evSizeMax] (inclusive).'''
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
    if (n >= evSizeMin and n <= evSizeMax ):
      ptrs[ind] = i
      lens[ind] = n
      ind += 1
    i += n
  ptrs, lens = ptrs[ptrs != 0], lens[lens != 0]
  if len(ptrs) == len(lens) - 1: 
    ptrs = np.array( [0] + list(ptrs), dtype=np.uint64 )
  return ptrs, lens
