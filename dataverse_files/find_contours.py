
import ctypes as C
import numpy as np
import scipy.misc
import math
import os
import re
import os.path as path

import time
lines_time = 0
midlines_time = 0
inner_loop = 0




import sys
if sys.platform.startswith('linux'):
	if C.sizeof(C.c_voidp) == 4:
		lib_name = 'libcontours32.so'             #32bit linux
	else:
		lib_name = 'libcontours64.so'             #64bit linux
if sys.platform.startswith('darwin'):
	lib_name = 'find_contours.dylib'         # os x
if sys.platform.startswith('win32'):
	lib_name = 'find_contours.dll'           # windoze



full_path = ''
path_ = path.dirname(__file__)


# for py2exe.. comment out all 
#full_path = path_ + '\\..\\..\\' + lib_name

files = os.listdir(path_)
for fn in files:
	if re.search(lib_name, fn) != None:
		full_path = path.join(path_,fn)
		break
if full_path == '':
	raise IOError("could not find library1!!!!111!!11!!!!!!!1!!!!")

# load the lib
_thelib = C.cdll.LoadLibrary(full_path)


# set the types for the functions
_thelib.trace_contour.argtypes = [C.POINTER(C.c_double), C.c_int, C.c_int, C.c_double]


def trace_contour(image, threshold, **kwargs):
	""" Trace contours in input image data at a specified contour level ("threshold").
	Optionally filter by kwarg input argument "area". Also, optionally reverse the
	orientation of the contours (from CCW/CW) using the kwargs param "reverse"
	"""
	
	# pad with zeros
	image = np.array(image, dtype="double")
	image = np.vstack((np.zeros((1,image.shape[1]),dtype=image.dtype), image, np.zeros((1,image.shape[1]),dtype=image.dtype)))
	image = np.hstack((np.zeros((image.shape[0],1),dtype=image.dtype), image, np.zeros((image.shape[0],1),dtype=image.dtype)))
	
	# ok there's a funny thing happening here. at some point, the arrays going in seemed to be striding
	# differently or some BS.... so here's a temporary hack. got to figure this out. if things stop working
	# look at the striding. 
	print image.strides, image.shape
	
	# fire off to the c function
	_thelib.trace_contour(image.ctypes.data_as(C.POINTER(C.c_double)), C.c_int(image.shape[1]), C.c_int(image.shape[0]), C.c_double(threshold))
	
	
	to_copy = []
	if 'area' in kwargs:
		num = _thelib.filter_by_area(C.c_double(kwargs['area'][0]), C.c_double(kwargs['area'][1]))
		to_copy = np.empty(num, dtype='i4')
		_thelib.return_filtered( to_copy.ctypes.data_as(C.POINTER(C.c_int)), C.c_int(num) )
	else:
		# how many contours....
		to_copy = range( _thelib.get_num_contours() )
	
	# copy the data over
	reverse = kwargs.get('reverse', False)
	
	contours = []
	for i in to_copy:
		contours.append(np.empty(( _thelib.get_contour_length(C.c_int(i)), 2 ), dtype="double" ))
		if reverse == False: _thelib.set_contour( contours[-1].ctypes.data_as(C.POINTER(C.c_double)), C.c_int(contours[-1].shape[0]), C.c_int(i) )
		else: _thelib.set_contour_rev( contours[-1].ctypes.data_as(C.POINTER(C.c_double)), C.c_int(contours[-1].shape[0]), C.c_int(i) )
	
	return contours

