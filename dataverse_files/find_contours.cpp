

#include "find_contours.h"
#include <iostream>
#include <math.h>

using namespace std;

// we'll use globals to make this all work with python...
vector<vector<double> > x_vals;
vector<vector<double> > y_vals;
vector<int> filtered;

//					   edge 1	     edge 2        edge 3        edge 4
//				   ([    ][    ])([    ][    ])([    ][    ])([    ][    ])
static int edges[16] = { 0, 0, 1, 0,   1, 0, 1, 1,   1, 1, 0, 1,   0, 1, 0, 0 };
//static int edges[16] = { 0, 0, 1, 0,   1, 0, 1, 1,   0, 1, 1, 1,   0, 0, 0, 1 };

// little macro to determine if a given square crosses the threshold across a given side of the square
#define IS_EDGE(px,py,edge) thresholded[img_x*(py+edges[edge*4+1])+px+edges[edge*4]] ^ thresholded[img_x*(py+edges[edge*4+3])+px+edges[edge*4+2]]


extern "C" int get_num_contours( void )
{
	return x_vals.size();
}

extern "C" int get_contour_length( int num ) {
	if( num > x_vals.size() ) { return -1; }
	return x_vals[num].size();
}

extern "C" void set_contour( double * array, int len, int num )
{
	if( num > x_vals.size() ) { return; }
	if( len > x_vals[num].size() ) { return; }
	
	
	for( int i=0; i<len; i++ ) {
		array[2*i] = x_vals[num][i];
		array[2*i+1] = y_vals[num][i];
	}
}

extern "C" void set_contour_rev( double * array, int len, int num )
{
	if( num > x_vals.size() ) { return; }
	if( len > x_vals[num].size() ) { return; }
	
	for( int i=0; i<len; i++ ) {
		array[2*i] = x_vals[num][i];
		array[2*i+1] = y_vals[num][i];
	}
}

double polygon_area( int num )
{
	double area = 0;
	int j = 0; int i = 0;
	int points = x_vals[num].size();
	
	for( i=0; i<points; i++ ) {
		j++; if( j == points ) j = 0;
		area += (x_vals[num][i]+x_vals[num][j])*(y_vals[num][i]-y_vals[num][j]);
	}
	
	return fabs(area*0.5);
}

extern "C" int filter_by_area( double min, double max )
{
	filtered.clear();
	
	double area;
	
	for( int i=0; i<x_vals.size(); i++ ) {
		area = polygon_area(i);
		if( area > min && area < max )
			filtered.push_back(i);
	}
	
	return filtered.size();
}

extern "C" void return_filtered( int * list, int num )
{
	if( num < filtered.size() ) return;
	
	for( int i=0; i<num; i++ ) {
		list[i] = filtered[i];
	}
}


extern "C" void trace_contour( double * img, int img_x, int img_y, double threshold )
{
	// yowzer, this function is a big annoying one. but it has been tested quite extensively.
	// send it an image, img, with dimensions img_x, img_y, and a contour level on that image,
	// and it will send you back all the contour lines at that level, interpolating contour
	// position based off a weighted average of the height variation of all the edges of each
	// square. it's basically identical to the matlab function contourf or whatever.
	
	
	// the coordinates of the contours
	vector<double> empty;
	x_vals.clear();
	y_vals.clear();
		
	x_vals.push_back(empty);
	y_vals.push_back(empty);
	
	// an array that stores whether or not we've visited each element
	int * visited = new int[img_x*img_y];			// we wont use the last element of every row...
	bool * thresholded = new bool[img_x*img_y];     // thresholded element
	
	bool walking, testing, first;
	bool is_saddle, next_saddle;
	bool to_continue;
	int saddle_edge;
	
	// hooey, a lot of points to remember.
	int p0x, p0y;		// point 0
	int p1x, p1y;		// point 1
	int pnx, pny;		// next point
	int ppx, ppy;		// previous point
	int px, py;			// current point
	int tx, ty;			// temp point
	double t;
	int edge;
	
	cout << img_x << " " << img_y<< endl;
	
	
	// look ahead at who's above an who's below the threshold. also, initialize the visited array
	for( int y=0; y < img_y; y++ ) {
		for( int x=0; x < img_x; x++ ) {
			
			if( img[y*img_x+x] >= threshold ) {
				thresholded[y*img_x+x] = true;
			} else {
				thresholded[y*img_x+x] = false;
			}
			
			visited[y*img_x+x] = 0;
		}
	}
	
	// first search for an edge in the image... just by rote
	for( int y=0; y < img_y-1; y++ ) {
		for( int x=0; x < img_x-1; x++ ) {
			
			// if we've already looked at it, keep going
			if( visited[y*img_x+x] > 0 ) continue;
			
			// otherwise, it's on, and we'll walk along the contour until it loops back, or
			// goes off the image
			
			// initialize some stuff
			walking = false; testing = true; first = true;
			is_saddle = false; saddle_edge = 0;
			
			px = x; py = y;			// our current position
			ppx = -1; ppy = -1;		// our previous position
			edge = 0;				// the edge we'll examine
			
			// the walking loop
			while( walking == true || testing == true ) {
				
				// mark the position as visited. do it a little different for a saddle,
				// b/c two contours pass through a saddle
				if( is_saddle ) {
					is_saddle = false;
					edge = saddle_edge;
					if( visited[py*img_x+px] == -1 ) { visited[py*img_x+px] = 1; }
					else { visited[py*img_x+px] = -1; }
				} else {
					visited[py*img_x+px]++;
				}
				
				//if( visited[py*img_x+px] == 2 ) { //cout << "awwww, shit" << endl; }
				
				// loop around
				if( edge >= 4 ) edge = 0;
				if( edge < 0 ) edge = 3; 
				
				// keep track of whether we're examing a point we found in the blue, or whether
				// we're on a walk
				if( testing == true && edge == 3 ) {
					testing = false;
				}
				
				// does the edge we're looking at cross a contour???
				if( IS_EDGE(px, py, edge) ) {
					
					// ok, then select the new edge
					if( edge == 0 ) {
						p0x = px;	p0y = py;
						p1x = px+1;	p1y = py;
						pnx = px;	pny = py-1;
					} else if ( edge == 1 ) {
						p0x = px+1;	p0y = py;
						p1x = px+1;	p1y = py+1;
						pnx = px+1;	pny = py;
					} else if ( edge == 2 ) {
						p0x = px+1;	p0y = py+1;
						p1x = px;	p1y = py+1;
						pnx = px;	pny = py+1;
					} else if ( edge == 3 ) {
						p0x = px;	p0y = py+1;
						p1x = px;	p1y = py;
						pnx = px-1;	pny = py;
					}
					
					
					////cout << "edge: " << edge <<  " pos: " << px << " " << py << " nextp: " << pnx << " " << pny << " lastp: " << ppx << " " << ppy << endl;
					
					// if we're looking back at the way we came in, then we're at the end of a contour
					if( ppx == pnx && ppy == pny ) {
						if( thresholded[p0y*img_x+p0x] == true ) {
							tx = p0x; ty = p0y;
							p0x = p1x; p0y = p1y;
							p1x = tx; p1y = ty;
						}
						
						t = (threshold - img[p0y*img_x+p0x])/(img[p1y*img_x+p1x] - img[p0y*img_x+p0x]);
						
						x_vals.back().push_back( p0x+t*(p1x-p0x)-0.5 );
						y_vals.back().push_back( p0y+t*(p1y-p0y)-0.5 );
						
						x_vals.push_back(empty);
						y_vals.push_back(empty);
						
						walking = false;
						
					}
					else if( visited[pny*img_x+pnx] > 0 ) {	// if the site's already been visited, then keep searching... this should mean we're done
						edge++;
					}
					else {
						// is the spot we're entering a saddle point? if so, mark it as such, and predetermine the next turn.
						if( (IS_EDGE(pnx, pny, 0)) && (IS_EDGE(pnx, pny, 1)) && (IS_EDGE(pnx, pny, 2)) && (IS_EDGE(pnx, pny, 3)) ) {
							if( thresholded[p0y*img_x+p0x] == false ) {		// if this is true, make a left turn.. otherwise, a right turn
								saddle_edge = edge + 1;
							} else {
								saddle_edge = edge - 1;
							}
							is_saddle = true;
						}
						
						
						if( thresholded[p0y*img_x+p0x] == true ) {
							tx = p0x; ty = p0y;
							p0x = p1x; p0y = p1y;
							p1x = tx; p1y = ty;
						}
						
						t = (threshold - img[p0y*img_x+p0x])/(img[p1y*img_x+p1x] - img[p0y*img_x+p0x]);
						
						x_vals.back().push_back( p0x+t*(p1x-p0x)-0.5 );
						y_vals.back().push_back( p0y+t*(p1y-p0y)-0.5 );
						
						if( first ) {	// if this is the first point on a new contour, keep looking around for the other, to close the polygon
							first = false; testing = false; walking = true;
							edge++;
						} else {
							ppx = px; ppy = py;	// remember the last point
							px = pnx; py = pny;	// set the new point
							
							edge--;
						}
					}
					
				} else {
					edge++;
				}
				
				
			}
		}
	}
	
	x_vals.pop_back();
	y_vals.pop_back();
	
	delete[] visited;
	delete[] thresholded;
}
	
