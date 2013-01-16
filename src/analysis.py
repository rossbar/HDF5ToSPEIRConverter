import numpy as np
import sys
import os

def processRawSignals( rdata, preTrig=30, evPerBit=.43 ):
  '''Do baseline subtraction and rough calibration for all data in rdata.
     rdata should be numSigs x sigLen dimensions (row, col). preTrig is the
     length of the signal that will be averaged over for calculating the
     baseline. evPerBit is the calibration parameter.'''
  # Baseline subtraction
  rdata = rdata - rdata[:, 0:preTrig].mean(axis=1)[:, np.newaxis]
  # Calibration
  rdata *= evPerBit
  return rdata

def extractSpeirParams( edata ):
  '''To use SPEIR, some additional information needs to be calculated: the
     detector side, the detector number, and the detector channel. All these
     are derived from the channel number from the parsed data and the known
     mapping between the current SIS card/detector channel layout. NOTE: THIS
     MAPPING IS HARD-CODED HERE! IF THE DETECTOR MAPPING OR THE SPEIR FORMAT
     CHANGE, THIS WILL PRODUCE INCORRECT RESULTS!'''
  # Determine AC or DC ( Speir format: 1 = AC, 0 = DC )
  side = ( edata.detector > 75 ).astype(int)
  # Get boolean matrices for which detector the data is from
  GeI = (edata.detector < 38) | ((edata.detector > 75)&(edata.detector < 38*3))
  GeII = np.invert( GeI )
  # Use boolean matrices to determine the detector number (Speir format: 2 = 
  # GeI, 3 = GeII [0 = SiI, 1 = SiII])
  detNum = np.zeros_like( edata.detector )
  detNum[GeI] = 2
  detNum[GeII] = 3
  # Convert the detector number to a channel number (Speir format = 1 through 38
  # SIS parser format = 0 through 37 so + 1
  chan = np.zeros_like( edata.detector )
  chan[(detNum == 2)&(side == 0)] = edata.detector[(detNum == 2)&(side == 0)] -\
                                    (38*0) + 1
  chan[(detNum == 2)&(side == 1)] = edata.detector[(detNum == 2)&(side == 1)] -\
                                    (38*2) + 1
  chan[(detNum == 3)&(side == 0)] = edata.detector[(detNum == 3)&(side == 0)] -\
                                    (38*1) + 1
  chan[(detNum == 3)&(side == 1)] = edata.detector[(detNum == 3)&(side == 1)] -\
                                    (38*3) + 1
  # Send back new stuff
  return side, detNum, chan
