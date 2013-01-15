import numpy as np
#from matplotlib.pyplot import *

import tables
#import recon.eventRecon as recon
#from multiprocessing import Pool, cpu_count
#import util.parallelize as par
#from itertools import repeat

from cython.getptrs_cy import getEventPtrs

###### Load data
print 'Loading data...'
fullpath = '/media/DATAPART1/CCI-2/June_2012/09-13-12/09-13-12_Cs137_trig=50_nnON.h5'
#fullpath = '/home/ross/Desktop/DATA/09-13-12_Cs137_trig=50_nnON.h5'
#fullpath = '/home/ross/Desktop/09-13-12_Cs137_trig=50_nnON.h5'
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

###### Make a new array that has dtype slots for the newly extracted data
#NOTE: Probably unnecessary
# print 'Reorganizing data...'
# speirdtype = np.dtype([('timestamp', '<u8'), ('ADC_value', '<f4'), ('detector', '<u2'), ('trigger', '<u2'), ('pileup', '<u2'), ('retrigger', '<u2'), ('rid', '<u4'), ('t50', '<f4'), ('chan', np.int16), ('side', np.int8), ('detNum', np.int8)])
# speirdata = np.zeros( len(edata), dtype=speirdtype )
# for name in edata.dtype.names:
#     speirdata[name] = edata[name]
# speirdata['chan'] = chan
# speirdata['side'] = side
# speirdata['detNum'] = detNum
# edata = speirdata.view(np.recarray)

# def getEventPtrs( tstamps, timeThresh=40):
#   '''Similar to the interaction grouping except doesn't actually group the data
#      together, just finds the indices corresponding to the beginning and end of
#      events'''
#   i = 0
#   ptrs = [0]
#   while i < len(tstamps):
#     n = 1
#     while( i+n < len(tstamps) ) and ( tstamps[i+n] <= tstamps[i] + timeThresh ):
#       n += 1
#     i += n
#     ptrs.append( i )
#   return np.array( ptrs )

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

print 'Writing data to table...'
#spierout = np.dtype([('Time', '<u8'), ('Energy', '<f4'), ('Trig', '<u2'), ('Chan', '<u2'), ('Side', '|u1'), ('DetNum', '|u1'), ('Valid', np.uint8), ('rid', np.int32) ])
spierout = np.dtype([('Time', '<u8'), ('Energy', '<f4'), ('Trig', '<u2'), ('Chan', '<u2'), ('Side', '|u1'), ('DetNum', '|u1'), ('Signal', np.uint32, (siglen,)) ])
table = hf.createTable('/SPIER', 'evData', spierout, expectedrows=len(edata))
row = table.row
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


# print 'Begin interaction grouping...'
# splitEdata = par.split_ev_seq( edata, 40, cpu_count())
# # Replace with cumsum!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# pool = Pool(cpu_count())
# args = zip(splitEdata, repeat(40))
# res = pool.map_async( recon.separateEvents, args )
# result = res.get()
# pool.close()
# events = np.concatenate( result )

###### NOW LOOP THROUGH THE EVENT DATA AND SAVE IT IN THE SAME FORMAT AS SPEIR
# evlens = np.array( [len(ev) for ev in events] )		# Need to gen ptrs
# ptrs = np.array( [0] + list(np.cumsum(evlens)) )	# Use to save/load edata

#foutName = raw_input('Enter name of h5 save file: ')



#foutName = '/home/ross/Desktop/data.h5'
#h5out = tables.openFile( foutName, mode='w')
#h5out.createArray("/", "evPtrs", ptrs)
#
#siglen = rdata.shape[-1]
#spierout = np.dtype([('Time', '<u8'), ('Energy', '<f4'), ('Trigger', '<u2'), ('Chan', '<u2'), ('Side', '|u1'), ('DetNum', '|u1'), ('Valid', np.uint8), ('Signals', np.uint32, (siglen,)) ])
#table = h5out.createTable('/', 'evData', spierout, expectedrows=len(edata) )
#row = table.row
#print 'Filling the table...'
#for i in range(len(edata)):
#  row['Time'] = edata[i][0]
#  row['Energy'] = edata[i][1]
#  row['Trigger'] = edata[i][3]
#  row['Chan'] = chan[i]
#  row['Side'] = side[i]
#  row['DetNum'] = detNum[i]
#  row['Signals'] = rdata[edata[i][6], :]
#  row.append()
#table.flush()
#h5out.close()
