import numpy as np
import tables
import os

# User-defined
from InputFile import InputFileClass

class OutputFileClass( object ):
  '''Class for creating the output file. Takes an InputFileClass object as 
     input (this guarantees the event data has been properly processed).'''
  def __init__( self, fname, inputFile ):
    # Check if file already exists, don't write over it
    if os.path.exists( fname ):
      print 'Warning: file already exists. Exiting...'
      return
    # Create the file for writing. Use format specified in sandbox.
    if type( inputFile ) != InputFileClass:
      print 'Warning: Input file must be of type InputFileClass. Exiting...'
      return
