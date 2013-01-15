#! /home/ross/epd/bin/python

import numpy as np
from matplotlib.pyplot import *
import tables
import sys
import os

# Attempt to import cython module
try: from libcy.getptrs_cy import getEventPtrs
except ImportError:
  print 'Warning: Setup incomplete. Run the following commands to install:'
  print 'cd libcy'
  print 'python setup.py build_ext -i'
  sys.exit()

def printHelp():
  helpstr = '''
  Usage:
    python translateToSPIER.py -h or --help: 	print this messge
    python translateToSPIER.py [filename].h5: 	Create file called 
    	translatedFrom_[filename].h5 that has the appropriate data format for
	SPIER. Output file created in same directory as input file
  '''
  print helpstr

def translateFile( fullpath ):
  '''Translate a file from the format of the HDF5 parser (v5.x) to the format
     used by SPIER. Warning: Translation causes the RawData to decompress, so
     the output file will likely be 2-4x larger than the input. 

     If the program segfaults, your system does not have enough memory for the
     "pre-processing raw signals" step. You can comment it out to avoid the
     issue, although then the raw signals will not be properly scaled or 
     baseline-subtracted. '''
  ###### Load data
  print 'Loading data...'
  hf = tables.openFile( fullpath, 'r' )
  edata = hf.root.EventData.read().view(np.recarray)
  #NOTE: Might consider filtering out bad strips here
  edata = edata[ edata.ADC_value > 0 ]	# Get rid of neg. vals due to bad calib/
  rdata = hf.root.RawData.read()
  hf.close()
  
  ###### Sort event data
  print 'Sorting...'
  edata.sort(order='timestamp')
  
  ###### Preprocess raw sigs: baseline sub, rough energy cal
  print 'Pre-processing raw signals...'
  siglen = rdata.shape[-1]
  evPerBit = .43			# Estimate for current setup
  preTrig = 30			# Length of pre-trigger to avg over
  rdata = rdata - rdata[:, 0:preTrig].mean(axis=1)[:, np.newaxis]
  rdata *= .43
  
  ###### Extract extra info from original data
  print 'Extracting additional info from original data...'
  side = (edata.detector > 75).astype(int)
  GeI = (edata.detector < 38) | ((edata.detector > 75) & (edata.detector < 38*3))
  GeII = np.invert(GeI)
  detNum = np.zeros_like(edata.detector)
  detNum[GeI] = 2
  detNum[GeII] = 3
  chan = np.zeros_like( edata.detector )
  chan[(detNum == 2)&(side == 0)] = edata.detector[(detNum == 2)&(side == 0)] - (38*0) + 1
  chan[(detNum == 2)&(side == 1)] = edata.detector[(detNum == 2)&(side == 1)] - (38*2) + 1
  chan[(detNum == 3)&(side == 0)] = edata.detector[(detNum == 3)&(side == 0)] - (38*1) + 1
  chan[(detNum == 3)&(side == 1)] = edata.detector[(detNum == 3)&(side == 1)] - (38*3) + 1
  
  ###### Interaction grouping
  print 'Extracting data pointers...'
  ptrs, lens = getEventPtrs( edata.timestamp, 40 )
  ptrs = np.array( [0] + list(ptrs), dtype=int )
  lens = lens.astype(np.int8)
  
  ###### Write data out to new HDF5 file
  # Write new file in same directory as orig file
  path = fullpath.split('/')
  origName = path.pop()
  foutname = 'translatedFrom_%s' %(origName)
  path.append(foutname)
  foutpath = '/'.join( path )
  
  hf = tables.openFile( foutpath, 'w' )
  hf.createGroup('/', 'SPIER')
  hf.createArray("/SPIER", "evPtrs", ptrs)
  hf.createArray("/SPIER", "evEnds", lens)
  spierout = np.dtype([('Time', '<u8'), ('Energy', '<f4'), ('Trig', '<u2'), ('Chan', '<u2'), ('Side', '|u1'), ('DetNum', '|u1'), ('Signal', np.uint32, (siglen,)) ])
  table = hf.createTable('/SPIER', 'evData', spierout, expectedrows=len(edata))
  row = table.row
  
  print 'Writing data to table...'
  for i in range( len(edata) ):
    row['Time'] = edata[i][0]
    row['Energy'] = edata[i][1]
    row['Trig'] = edata[i][3]
    row['Chan'] = chan[i]
    row['Side'] = side[i]
    row['DetNum'] = detNum[i]
    row['Signal'] = rdata[ edata[i][6],: ]
    row.append()
  table.flush()
  hf.close()
  return

if __name__ == '__main__':
  # Parse command line input
  argc = len(sys.argv)
  if ('-h' in sys.argv) or ('--help' in sys.argv) or (argc == 1):
    printHelp()
    sys.exit(0)
  if argc == 2:
    fullpath = sys.argv[-1]
    if not os.path.exists( fullpath ):
      print 'Warning: invalid input file (or path to file).'
      sys.exit()
    if fullpath.split('.')[-1] != '.h5':
      print 'Warning: input file must be an HDF5 file'
  else:
    printHelp()
    sys.exit()

  translateFile( fullpath )
