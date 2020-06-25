import numpy as np


def calculate_curvature( data, number_of_points, **kwds ):
	order = kwds.get('order', 3)                     # polynomial order
	curv_at_same = kwds.get('curv_at_same', False)   # evaluate curvature exactly at the input positions
	poly_fit_len = int(kwds.get('fit_len', 5))       # half-width of the sliding window used for the polynomial fit
	pad = kwds.get('pad', 10)                        # region to pad around the ends of the input data
	weighted = kwds.get('weighted', False)           # weight the polynomial fit using a gaussian to the central datapoint, with the value of "weighted" corresonding to 2 time the gaussian width, in sigma
	
	
	# calculate the distances along the x,y input data
	dists = np.hstack([0,np.cumsum(np.sqrt( (data[:-1,1]-data[1:,1])**2+ (data[:-1,0]-data[1:,0])**2 ))])
	
	# use this to make sure there are no zero distance entries.
	if np.sum(np.diff(dists) == 0):
		keep_mask = np.ones(len(data[:,0]), dtype='bool')
		evals = np.where(np.diff(dists)==0)
		keep_mask[evals] = 0
		data = data[keep_mask]
		
		# new dists
		dists = np.hstack([0,np.cumsum(np.sqrt( (data[:-1,1]-data[1:,1])**2+ (data[:-1,0]-data[1:,0])**2 ))])
	
	# determine at which distances to evaluluate curvature
	if curv_at_same == False:
		interp_eval = np.linspace( dists[pad], dists[-pad-1], num=number_of_points )
	else:
		interp_eval = dists[pad:-pad-1]
	
	# initialize the output data structures
	points = np.zeros((len(interp_eval),2), dtype='float')
	curvature = np.zeros(len(interp_eval), dtype='float')
	
	
	# loop through each position
	for i in range(pad, len(dists)-pad):
		# do the polynomial fit
		if weighted:
			min_, max_ = min(dists[i-poly_fit_len:i+poly_fit_len+1]), max(dists[i-poly_fit_len:i+poly_fit_len+1])
			gaussian = lambda x, mu, sig: np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))
			
			weights = gaussian(dists[i-poly_fit_len:i+poly_fit_len+1], dists[i], (max_-min_)/weighted)  # total range is weighted sigma
			
			x_poly = np.poly1d(np.polyfit(dists[i-poly_fit_len:i+poly_fit_len+1], data[i-poly_fit_len:i+poly_fit_len+1,0], order, w=weights))
			y_poly = np.poly1d(np.polyfit(dists[i-poly_fit_len:i+poly_fit_len+1], data[i-poly_fit_len:i+poly_fit_len+1,1], order, w=weights))
		else:
			x_poly = np.poly1d(np.polyfit(dists[i-poly_fit_len:i+poly_fit_len+1], data[i-poly_fit_len:i+poly_fit_len+1,0], order))
			y_poly = np.poly1d(np.polyfit(dists[i-poly_fit_len:i+poly_fit_len+1], data[i-poly_fit_len:i+poly_fit_len+1,1], order))
		
		# make objects for the derivatives
		x_first, x_second = x_poly.deriv(1), x_poly.deriv(2)
		y_first, y_second = y_poly.deriv(1), y_poly.deriv(2)
		
		# figure out which exact sub-pixel distances we'll calculate the curvature for (only calculate curvature within a 1 pixel range for a given loop cycle)
		min_, max_ = (dists[i]+dists[i-1])/2, (dists[i]+dists[i+1])/2
		eval_d = interp_eval[eval_idx]
		
		# evaluate the curvature at the given distances eval_d, using our fit derivatives
		points[eval_idx,0], points[eval_idx,1] = x_poly(eval_d), y_poly(eval_d)
		curvature[eval_idx] = (x_first(eval_d)*y_second(eval_d) - x_second(eval_d)*y_first(eval_d))/np.power(x_first(eval_d)**2 + y_first(eval_d)**2, 3./2)
	
	
	return curvature, points
