import numpy as np
import sys
import os

# User defined
from src.InputFile import InputFileClass
from src.OutputFile import OutputFileClass
from src.Converter import ConverterClass

# Functions
def printHelp():
  helpstr = '''
Usage:
translateToSPEIR.py [OPTIONS] [TARGET]
OPTIONS:
  -h or --help: print this message
  -n or --no-chunk: Don't chunk file writing. Not recommended for large files
                    or systems with < 8 Gb RAM
  -i or --interactive: Input chunksize from keyboard
TARGET:
  An hdf5 file or directory containing hdf5 files. If a file, will run on that
  single file. If a directory, will run on every file with '.h5' format. 
  Recursive directory search not implemented.
  '''
  print helpstr

def getNewChunksize( llim=1e4, hlim=6e6 ):
  '''Get new chunksize from input and test that its within bounds. Chunksizes
     should not be smaller than 100,000 (for speed concerns) and larger than
     6e6 is unfeasible for systems with < 16 Gb RAM.'''
  # Get input
  inp = raw_input('Enter a new chunksize (default = 1e6): ')
  # Make sure it's an integer
  try: chunksize = int( inp )
  except ValueError:
    print 'Chunksize must be an integer! Exiting'
    sys.exit()
  # Make sure it's in bounds
  if chunksize < llim:
    print 'Chunksize too small! Recommend chunksize larger than %s.' %(llim)
    print 'Either choose a different chunksize or modify src code change lim'
    sys.exit()
  elif chunksize > hlim:
    print 'Chunksize too large! Recommend chunksize < %s' %(hlim)
    print 'Either choose a new chunksize or modify src code to change lim'
    sys.exit()
  return chunksize

def parseInput( argv ):
  '''Parse command line input and return relavent parameters.'''
  # First things first, check for help and that the last arg isn't an opt. flag
  if '-h' in argv or '--help' in argv or argv[-1][0] == '-':
    printHelp()
    sys.exit()
  # Defaults
  chunked = True
  chunksize = 1e6
  # Parse
  argc = len( argList )
  if argc > 4:
    print 'Too many input arguments! Exiting.'
    sys.exit()
  if '-i' in argv or '--interactive' in argv:
    chunked = True
    chunksize = getNewChunksize()
  # --no-chunk overrides --interactive mode
  if '-n' in argv or '--no-chunk' in argv:
    chunked = False
  return chunked, chunksize

def getTargetsFromDir( dirname ):
  '''Get a list of all un-translated hdf5 files from the givn dirname.'''
  # Format the dirname
  if dirname[-1] != '/': dirname += '/'
  # Get the files in dirname
  allfiles = os.listdir( dirname )
  potentialTargets = []
  targets = []
  # First round of checking
  for f in allfiles:
    # Get the full path to the file
    fullpath = dirname + f
    # Make sure it's a file
    if not os.path.isfile( fullpath ): continue
    # Make sure it hasn't already been translated
    if f[0:10] == 'translated': continue
    # Make sure its and hdf5 file
    if f[-3:] != '.h5': continue
    # If all the above checks are passed, then:
    potentialTargets.append( f )
  # Second round of checking: make sure the potentialTargets haven't already
  # been translated
  for f in potentialTargets:
    fname = 'translatedFrom_%s' %( f )
    if fname in allfiles: continue
    else: targets.append( dirname + f )
  return targets

def translateFile( fpath ):
  '''Create inputfile, outputfile, and converter objects. Call the converter
     method to translate between the input and output if no errors encountered.
     '''
  hfin = InputFileClass( fpath, verbose=True )
  hfout = OutputFileClass( hfin )
  converter = ConverterClass( hfin, hfout )
  converter.VERBOSE = True
  converter.convertAllData()

def translateDirectory( dirname ):
  '''Translate every file in dirname that has an .h5 ending'''
  targets = getTargetsFromDir( dirname )
  for fpath in targets:
    print 'Now translating: %s\n' %( fpath.split('/')[-1] )
    translateFile( fpath )
    print
