#include <vector>


extern "C" void trace_contour( double * img, int img_x, int img_y, double threshold );
extern "C" int get_contour_length( int num );
extern "C" int get_num_contours( void );
extern "C" void set_contour( double * array, int len, int num );
extern "C" void set_contour_rev( double * array, int len, int num );
extern "C" void return_filtered( int * list, int num );
extern "C" int filter_by_area( double min, double max );
double polygon_area( int num );

