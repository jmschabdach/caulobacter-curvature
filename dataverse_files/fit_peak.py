from numpy import *
from scipy import optimize
from scipy.ndimage.filters import gaussian_filter
	
def fit(self, data, x, y, **kwds):
	"""Fit a round (as opposed to an eliptical) 2-D gaussian to a spot in an ndarray of floats.
	Must specify a reasonable guess for the x y position, as the algorithm cuts a small window,
	of width gf_size*2+1, out of the data for refinement. Returns the final fit params."""
	
	gf_size = kwds.get('gf_size', 5) # width of the box around the guessed peak position
	fixed_sigma = kwds.get('fixed_sigma', False) # fix the sigma, in pixels, of the gaussian fitter to this value
	
	# our 2-D gaussian functions...
	gauss_2D_err = lambda params, points, data: ravel(- data + params[4]+params[3]*exp( -( ((params[0]-points[0,:])**2/(2*params[2]**2)) + ((params[1]-points[1,:])**2/(2*params[2]**2))) ))
	gauss_2D = lambda params, points: ravel(params[4]+params[3]*exp( -( ((params[0]-points[0,:])**2/(2*params[2]**2)) + ((params[1]-points[1,:])**2/(2*params[2]**2))) ))
		
	gauss_2D_fixedsigma_err = lambda params, sigma, points, data: ravel(- data + params[3]+params[2]*exp( -( ((params[0]-points[0,:])**2/(2*sigma**2)) + ((params[1]-points[1,:])**2/(2*sigma**2))) ))
	gauss_2D_fixedsigma = lambda params, sigma, points: ravel(params[3]+params[2]*exp( -( ((params[0]-points[0,:])**2/(2*sigma**2)) + ((params[1]-points[1,:])**2/(2*sigma**2))) ))
	
	points = indices(((2*gf_size+1),(2*gf_size+1))) # indices at which to evaluate the gaussian functions
	
	# a nested function to do the actual gaussian fitting
	def gaussfit(self, data, points, p0):
		"""This function will refine a 2-D gaussian on the target data,
		with the x,y positions of each point in the array provided by
		points (generally this should be: numpy.indices(data.shape)),
		and then the initial guess for the parameters. Parameters are:
		p[0]: x center p[1]: y center p[2]: width p[3]: amplitude p[4]:
		background. p[5] should exist, and will be filled in with the
		correlation coefficient leastsq uses the original fortan levmar
		algorithm"""
		
		# run the fitting
		if fixed_sigma:
			p0_nosigma = [p0[0], p0[1], p0[3], p0[4]]
			out = optimize.leastsq(gauss_2D_fixedsigma_err, p0_nosigma, args=(fixed_sigma, points, data),maxfev=2000)
			# use numpy's built in corrcoef calculator. output is a matrix, just pull one value out.
			corco = corrcoef( ravel(data), gauss_2D_fixedsigma(out[0], fixed_sigma, points) )[1,0]
			out = [out[0][0], out[0][1], fixed_sigma, out[0][2], out[0][3], corco, 0], out[1]
			return out 
		else:
			out = optimize.leastsq(gauss_2D_err, p0, args=(points, data),maxfev=2000)
			# use numpy's built in corrcoef calculator. output is a matrix, just pull one value out.
			out[0][5] = corrcoef( ravel(data), gauss_2D(out[0], points) )[1,0]
			return out 
		
	
	# make sure our window wont go off the edge of the frame. if it will, return None
	if( x <= gf_size or x >= data.shape[0] - gf_size ):
		return None
	elif( y <= gf_size or y >= data.shape[1] - gf_size ):
		return None
	
	# cut out a slice out of the input array for gaussian refinement
	the_slice = array(data[x-gf_size:x+gf_size+1,y-gf_size:y+gf_size+1])
	
	# make the initial guess object array. order is p[0]: x position, p[1]: y position,
	#  p[2]: width, p[3]: intensity, p[4]: background, p[5] corr coeff (not used in the fit...)
	# and p[6] the background stdev, for snr calculations
	p0 = array([gf_size, gf_size, 1.5, the_slice.max(), 0, 0.],dtype="float")
	
	# do the fitting. catch shape errors. it shouldn't happen, but every once and a while it
	# does, and this makes it easier to find...
	try:	
		result, num = gaussfit(the_slice,p0)
	except ValueError:
		print "Error with sizing... probably running into a boundary?"
		raise
	
	# recenter back in the absolute coordinate system
	result[0] = result[0] + x - gf_size
	result[1] = result[1] + y - gf_size
	
	return result



def return_peak_intensity( image_data, peak_position, **kwds ):
	""" Calculate the intensity of a given peak in an image of a cell. Provide the raw image data,
	the coordinates of the peak, and a couple parameters, and it sends back the integrated intensity
	"""
	
	background_filter_size = kwds.get('bkg_filt_sz', 2.7) # background filter size, in um
	px_sz = kwds.get('px_sz', .108)                       # image pixel size, in um
	
	
	img_data_background_subtracted = image_data - gaussian_filter(image_data, background_filter_size/px_sz)  # use a big gaussian to do local backgroudn subtraction
	
	if kwds.get('fixed_sigma',False):
		res = fit(img_data_background_subtracted, peak_position[1], peak_position[0], fixed_sigma=.108/px_sz)   # fit the peak using a sigma that is roughlty a diffraction limited spot
	else:
		res = fit(img_data_background_subtracted, peak_position[1], peak_position[0]) # fit the peak using a free sigma
	
	# if the sigma got out of control, i.e. greater than 0.3 um, which is much bigger than a diffraction limited spot, fix the sigma
	# so we don't get total garbage out
	if res[2] > 0.3/kwds['pixel_size']:
		res = fit(img_data_background_subtracted, peak_position[1], peak_position[0], fixed_sigma=.162/px_sz)
	
	return res[3]*res[2]**2    # return the integrated area, peak height * (peak width)^2 ok, it's not exactly the integrated area, but its proportional (missing a 2*pi or something)


