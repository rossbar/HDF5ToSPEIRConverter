import numpy as np
import time

# User-defined
from InputFile import InputFileClass
from OutputFile import OutputFileClass

class ConverterClass( object ):
  '''Class for converting the data contained in an InputFile object and 
     writing it out into an OutputFile object.'''
  def __init__( self, inputObj, outputObj, chunked=True, chunksize=1e6 ):
    '''chunksize: amount of sorted readouts the user wants to convert at one
       time. The whole reason for doing this is because dealing with the 
       rawdata is very RAM intensive. For computers with less memory, use a
       smaller chunksize (1 million should be okay for 16 GB machines).'''
    self.VERBOSE = False
    self.hfin = inputObj.hf
    self.hfout = outputObj.hf
    self.edata = inputObj.edata
    self.outTable = outputObj.table
    # Figure out chunking
    self.chunked = chunked	# Default is to do by chunking, but not req'd
    self.starts = np.arange( 0, self.edata.shape[0], chunksize )
    self.nchunks = len( self.starts )
    self.ends = np.array( list(self.starts[1:]) + [ self.edata.shape[0] ] )
    self.chunkTimes = []

  def convertAllData( self ):
    '''Top-level function: converts all data from the input file to the
       speir format and writes it to the table in the output file.'''
    if not self.chunked:	# Do the whole file at once      
      tic = time.time()
      self.rdata = self.hfin.root.RawData.read()
      self.rmin = 0
      self.convertChunk( self.edata, self.rdata )
      toc = time.time()
      self.chunkTimes.append( toc - tic )
    else:	# Do it the chunked way
      # Loop over the chunks
      self.gen = 1
      for s,e in zip( self.starts, self.ends ):
        # Chunk of edata
        if self.VERBOSE: print 'Processing chunk %s out of %s'\
                               %( self.gen, self.nchunks )
        tic = time.time()
        edata = self.edata[ s:e ]
        self.rmin, self.rmax = edata.rid.min(), edata.rid.max()+1
        rdata = self.hfin.root.RawData.read(start=self.rmin, stop=self.rmax)
        self.convertChunk( edata, rdata )
        toc = time.time()
        self.chunkTimes.append( toc - tic )
        self.gen += 1
    # Cleanup
    self.hfin.close()
    self.hfout.flush()
    self.hfout.close()

  def convertChunk( self, edata, rdata ):
    '''Convert the input from the given data chunk to speirtype and write it
       to the table in the output file object.'''
    # Process the raw signals
    self.processRawSignals( rdata )
    # Extract extra params
    self.extractSpeirParams( edata )
    # Write all the data to the output table
    row = self.outTable.row
    for i in range( len(edata) ):
      row['Time']   = edata[i][0]
      row['Energy'] = edata[i][1]
      row['Trig']   = edata[i][3]
      row['Chan']   = self.chan[i]
      row['Side']   = self.side[i]
      row['DetNum'] = self.detNum[i]
      row['Signal'] = self.rdata[ (edata[i][6]-self.rmin),: ]
      row.append()
    self.outTable.flush()

  def processRawSignals( self, rdata, preTrig=30, evPerBit=.43 ):
    '''Do baseline subtraction and rough calibration for all data in rdata.
       rdata should be numSigs x sigLen dimensions (row, col). preTrig is the
       length of the signal that will be averaged over for calculating the
       baseline. evPerBit is the calibration parameter.'''
    # Baseline subtraction
    rdata = rdata - rdata[:, 0:preTrig].mean(axis=1)[:, np.newaxis]
    # Calibration
    rdata *= evPerBit
    self.rdata = rdata

  def extractSpeirParams( self, edata ):
    '''To use SPEIR, some additional information needs to be calculated: the
       detector side, the detector number, and the detector channel. All these
       are derived from the channel number from the parsed data and the known
       mapping between the current SIS card/detector channel layout. NOTE: THIS
       MAPPING IS HARD-CODED HERE! IF THE DETECTOR MAPPING OR THE SPEIR FORMAT
       CHANGE, THIS WILL PRODUCE INCORRECT RESULTS!'''
    # Determine AC or DC ( Speir format: 1 = AC, 0 = DC )
    side = ( edata.detector > 75 ).astype(int)
    # Get boolean matrices for which detector the data is from
    GeI = (edata.detector < 38)|((edata.detector > 75)&(edata.detector < 38*3))
    GeII = np.invert( GeI )
    # Use boolean matrices to determine the detector number (Speir format: 2 = 
    # GeI, 3 = GeII [0 = SiI, 1 = SiII])
    detNum = np.zeros_like( edata.detector )
    detNum[GeI] = 2
    detNum[GeII] = 3
    # Convert the detector number to a channel number (Speir: 1 through 38
    # SIS parser format = 0 through 37 so + 1
    chan = np.zeros_like( edata.detector )
    chan[(detNum==2)&(side==0)] = edata.detector[(detNum == 2)&(side == 0)] -\
                                  (38*0) + 1
    chan[(detNum==2)&(side==1)] = edata.detector[(detNum == 2)&(side == 1)] -\
                                  (38*2) + 1
    chan[(detNum==3)&(side==0)] = edata.detector[(detNum == 3)&(side == 0)] -\
                                  (38*1) + 1
    chan[(detNum==3)&(side==1)] = edata.detector[(detNum == 3)&(side == 1)] -\
                                  (38*3) + 1
    # Send back new stuff
    self.side, self.detNum, self.chan = side, detNum, chan
