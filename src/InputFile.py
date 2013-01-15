import numpy as np
import tables
import time

#NOTE: Consider using decorator for tic toc profiling

class InputFileClass( object ):
  '''Class for holding the input HDF5. This is the file that is output from
     parsing the binary data. All the data for the output file will be 
     derived from it (either directly or via some manipulation).'''
  def __init__( self, fpath, filt=True, verbose=False ):
    self.VERBOSE = verbose
    # Attempt to open the file
    self.hf = tables.openFile( fpath, 'r' )
    # Print the size of the event data
    self.eventDataSize = self.hf.root.EventData.nrows *\
                         self.hf.root.EventData.rowsize / 1e6
    self.rawDataSize = self.hf.root.RawData.nrows*\
                       self.hf.root.RawData.rowsize / 1e9
    if self.VERBOSE: print 'Event data table size: %s' %( self.eventDataSize )
    # Load the data
    if self.VERBOSE: print 'Loading event data...'
    tic = time.time()
    edata = self.hf.root.EventData.read().view(np.recarray)
    toc = time.time()
    self.loadTime = toc - tic
    if self.VERBOSE: print 'Done.'
    # Filter data
    self.originalShape = edata.shape[0]
    if filt:
      if self.VERBOSE: print 'Filtering event data...'
      tic = time.time()
      edata = edata[edata.ADC_value > 0]	# Positive energies only
      self.afterEnergy = edata.shape[0]
      edata = edata[edata.trigger < 2]		# No pileup
      self.afterPileup = edata.shape[0]
      #NOTE: implement bad strip filter here
      self.edata = edata
      toc = time.time()
      self.filterTime = toc - tic
      if self.VERBOSE: print 'Done.'
    else: 
      self.edata = edata
      self.afterEnergy, self.afterPileup = [ self.originalShape ]*2
    # Sort by time
    if self.VERBOSE: print 'Sorting data...'
    tic = time.time()
    self.edata.sort(order='timestamp')
    toc = time.time()
    self.sortTime = toc - tic
    if self.VERBOSE: print 'Done.'
    # Done loading
    if self.VERBOSE: print 'Input file successfully loaded.'

  def __str__( self ):
    '''Print the file information.'''
    outstr = '''
    filename = %s

    Data size:
      Event Data = %s MB
      Raw Data   = %s GB
    Filtering Statistics:
      Original readouts:	%s
      After energy filter:	%s
      After pileup filter:	%s
    Profiling statistics:
      Load time:	%s sec
      Filter time:	%s sec
      Sorting time:	%s sec
    ''' %( self.hf.filename, self.eventDataSize, self.rawDataSize, \
           self.originalShape, self.afterEnergy, self.afterPileup, \
           self.loadTime, self.filterTime, self.sortTime )
    return outstr
