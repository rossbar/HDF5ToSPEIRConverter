import numpy as np
import tables
import os

# User-defined
from cython64 import getPtrs_cy
from InputFile import InputFileClass

class OutputFileClass( object ):
  '''Class for creating the output file. Takes an InputFileClass object as 
     input (this guarantees the event data has been properly processed). The
     name of the output file is: "translatedFrom_<original file name>".'''
  def __init__( self, inputFile ):
    # Set new file name
    path = inputFile.hf.filename.split('/')
    self.origName = path.pop()
    self.foutname = 'translatedFrom_%s' %(self.origName)
    path.append( self.foutname )
    self.foutpath = '/'.join( path )
    # Make sure file doesn't already exist
    if os.path.exists( self.foutpath ):
      print 'Warning: file already exists. Exiting...'
      return
    # Get the event pointers from the input file
    self.ptrs, self.lens = getPtrs_cy.getEventPtrs( inputFile.edata.timestamp,\
                                                    40, 4, 18 )
    # Initialize the file
    self.hf = tables.openFile( self.foutpath, 'w' )
    self.hf.createGroup( '/', 'SPEIR' )
    self.hf.createArray( "/SPEIR", "evPtrs", self.ptrs )
    self.hf.createArray( "/SPEIR", "evEnds", self.lens )
    # Define the spier data type
    exprows, siglen = inputFile.hf.root.RawData.shape
    self.spierout = np.dtype([('Time', '<u8'), ('Energy', '<f4'),\
                    ('Trig', '<u2'), ('Chan', '<u2'), ('Side', '|u1'),\
                    ('DetNum', '|u1'), ('Signal', np.uint32, (siglen,)) ])
    # Create the spier table
    self.table = self.hf.createTable( '/SPEIR', 'evData', self.spierout,\
                 expectedrows=exprows )
    # Make the input file an attribute
    self.inputFile = inputFile

  def __str__ ( self ):
    return str( self.hf )

  def __del__( self ):
    self.hf.flush()
    self.hf.close()
