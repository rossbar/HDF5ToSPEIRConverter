Dependencies:
- Python 2.6 or greater (but not 3.0) with modules:
	- pytables
	- numpy
- C compiler for cython (should be handled by setup.py)

To install:
# OPTIONAL
# 1) change the shebang (first line) of translateToSPIER.py to the location of
#    your preferred python distribution (must include numpy and pytables)
# 2) Make sure the permissions are correct for executing (on linux:
#    chmod u+x translateToSPIER.py

 3) In the libcy directory, run the following command:

    python setup.py build_ext -i

    Assuming you have a properly set up compililing environment for C, this 
    should create a dynamic library called getptrs_cy.so[dll].
 3) You're ready to go

To Run:

python translateToSPIER.py -h or --help: print help message

python translateToSPIER.py [filename]:
  Given an hdf5 file called [filename], create a second hdf5 called
  translatedFrom_[filename] that has data in the appropriate format to be read
  in by SPIER (using getCCI2RecordFromHDF5 function in matlab). The output file
  is built in the same directory that the input file came from.

  Format of input file:
  - Must have table called EventData with the following fields in the following
    order
	timestamp
	energy   (calibrated)
	channel# [0-151]
	trigger
	pileup
	retrigger
	raw_id	(ptr to the corresponding raw signal)
  - Also needs a CArray called RawData with dims numReadout x numSamples/Signal
  Files with these formats are automatically produced by the SIS parser v5.x
  (Cameron Bates/Ross Barnowski - contact:rossbar@berkeley.edu)

Known issues:
 - The reformatting causes the raw data to un-compress, so the output HDF5 file
   will be 2-4x larger than the input file
 - The "pre-processing raw signals" step does some rough calibration of the
   raw signal energy as well as baseline subtraction. The implementation is 
   extremely memory intensive ( about 2x RawData.nbytes ). Some python 
   interpreters don't always gracefully catch memory errors and can result in a
   seg fault. 
   If the RawData is > (1/3) the size of available RAM, consider rewriting the
   script to read the data in by chunks (or split the input file into smaller
   input files)
