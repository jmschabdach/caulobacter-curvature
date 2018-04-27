===========================================================
README
===========================================================

This code was written by Jenna Schabdach during the Methods
in (Bio)Medical Image Analysis course at CMU in Spring 2018
for use in the Childer's Lab. 

Code files: 
- Identifying and Measuring the Curvature 
    of Caulobactor Cells.ipynb
- caulobactorCellCurvatureAnalysis.py 

===========================================================
Purpose
===========================================================
The enclosed Python code is intended to be use to measure 
the curvature of cells in phase images. There are two
options for running this code: interactively through a
Jupyter notebook (previously iPython) or through the Python
script using a terminal.

===========================================================
Using the Code
===========================================================
-----------------------------------------------------------
Set Up The Environment
-----------------------------------------------------------

To run this code, you will need Python. We recommend using
Anaconda to manage your Python libraries. To install conda
visit https://www.anaconda.com/download/ and follow the
instructions for your operating system.

Once conda is installed, open a command line window
- Windows: Start Menu -> Search for "cmd"
- OS X: Applications/Utilities -> Terminal
- Linux: On Ubuntu, Ctrl+Alt+T opens a new terminal window

In the terminal, type the following lines to install the
Jupyter, matplotlib, scipy, numpy, vtk, and SimpleITK 
libraries. After typing a single line, press enter to run 
the command. You may be asked if you wish to continue with
the install for different commands. You will need to 
respond with a y or n (yes or no) for each request.

    conda update conda
    conda install python=3.6
    conda update jupyter
    conda update matplotlib
    conda update scipy
    conda update ipython
    conda update numpy
    conda install -c clinicalgraphics vtk
    conda install -c simpleitk simpleitk=1.0.1

At this point, you should have all the necessary libraries
installed. Run this code using either the Jupyter notebook
or the Python script.

-----------------------------------------------------------
Option 1: Run the Jupyter Notebook
-----------------------------------------------------------
Open a terminal. Navigate in the terminal to the directory
housing this code and type the following command

    jupyter notebook

and press ENTER. A new page will open in your default web
browser showing a view of this directory. Double click on
the file entitled "Identifying and Measuring the Curvature
of Caulobacter Cells.ipynb". The extension .ipynb indicates
that the file is an iPython notebook. Double clicking on
the filename will open the notebook in a new tab. 

The notebook is made up of different types of cells. The
Markdown cells serve as documentation within the notebook,
and the code cells hold code that can be run. To run a
code cell, click on it and either click the "play"
button in the toolbar or press the key combination 
Shift+Enter.

In this notebook, the first code cell holds import
statements. Run this cell. If an error message appears, you
will need to install or reinstall the library mentioned in
the error message.

The second code cell contains variables that are used later
in the notebook. You should edit the values of the
following variables so that they match the files you want
to analyze:

    - inputFile: the path to the image file to be analyzed; 
        .nd2 not yet supported, use .png, .jpg, etc. 
        instead; please use full path to file
    - saveIntermediateFigures: set to False to only save
        the final results of the notebook, set to True to
        save intermediately generated figures

When you have finished modifying the variables in this
cell, run it and the rest of the code cells in the
notebook.

-----------------------------------------------------------
Option 2: Using the Python Script
-----------------------------------------------------------
Open a terminal. Navigate in the terminal to the directory
housing this code and type the following command:

    python calculatingCellCurvature.py --inFn <path to input
      file> [--saveIntermediateFigures]

The two arguments the script takes are:

    - inFn: filepath for the input function (string)
    - saveIntermediateFigures: presence indicates 
        the intermediate figures should be saved

For further information about the arguments, enter the 
command: 

    python calculatingCellCurvature.py --help

This command will display information about which arguments
to provide to the Python script. 

-----------------------------------------------------------
Examining the Results
-----------------------------------------------------------
After running the code, a directory called 'figures' will
have been created in the directory housing this code. A 
subdirectory will be created within 'figures' for the image
that was processed. The subdirectory will be named after 
the image. In this subdirectory, the following figures will
be created:

    - curvatures.png: composite image of the original image
        overlaid with the contours
    - curvature-histogram.png: a histogram of the curvature
        values

If the 'saveIntermediateFigures' boolean variable is set to
True, the following additional figures will be generated:

    - 00-multithreshold-otsu-filtered.png: the raw
        segmentation generated from the first stage of the
        segmentation step
    - 01-segmentation.png: the cleaned version of the 
        segmentation
    - 02-labelmap.png: the label map image generated from
        the segmentation
    - 03-contours.png: the raw contours of the cells    

===========================================================
Experiments
===========================================================

* Image source

The images were taken on a light microscope and arrived in
.nd2 format. As there were difficulties in configuring a 
Python version of ITK that could read .nd2 files, each 
image instead underwent the following process:

    - Opened the image using Fiji
    - Selected the phase channel (as opposed to 
      fluorescent channels)
    - Took a screenshot of the phase channel and saved it
      as a .png file

* Preprocessing

Upon reading the sample images into the Jupyter notebook,
it was found that they were being read as RGBA images. 
The preprocessing extracts a single channel from the RGBA
image and uses it in the rest of the pipeline. (See
Future Work.)

* Segmentation Pipelines

1. Edge-preserving smoothing, gradient magnitude filter,
sigmoid image filter, fast marching (segmentation 
homework, part 2)
thresholding, etc.
- Benefits: easy starting point
- Drawbacks: blurred boundaries between very close cells
    too much for the cells to be identified as
    separate objects; wanted to not need seed
    points - researchers this tool is intended for
    have limited programming experience, plus it 
    would need a separate seed for each cell

2. Basic thresholding
- Benefits: able to tune the threshold level easily to make
    sure the correct number of cells are identified
    and doesn't require seed points
- Drawbacks: would need to tune the threshold for each
    image separately; decreases generalizability

3. Otsu Thresholding
- Benefits: more generalizable than binary thresholding
- Drawbacks: some images had multiple peaks in their 
    pixel intensity histograms, and the peak Otsu chose 
    did not lead to the best segmentation (identified 
    halos in sample-01 instead of cells)

4. Multithreshold Otsu Thresholding, followed by opening
- Benefits: able to identify cells better in images that 
    have multiple peaks in the pixel histograms; opening
    removes any small pieces of background that are 
    incorrectly categorized as cells
- Drawbacks: could potentially categorize poorly imaged
    cells (that have different brightness levels) as 
    belonging to a different threshold level, resulting in
    cells missing from the segmentation

After segmentation, the segmented image was passed through
a label map. 

* Identifying Contours

All curvature pipelines iterated through the different
labels in the label map produced in the final stage of the
segmentation pipelines.

1. Subtraction of morphologically dilated and eroded images
- Benefits: makes sense
- Drawbacks: contours did not always appear to be
    continous and complete

2. Skeletonize the cell, and find the curvature of the 
skeletonization
- Benefits: find the overall curvature of the cell
- Drawbacks: only find the overall curvature of the cell,
    not the curvature of the shape of the cell 
    (specifically, the curvature at the ends of the cell)

3. Iterate through the coordinates of the pixels of a cell
mask by row, add pixels located at beginning and end of row
as well as discontinuities to a list of edge pixels, use
list of edge pixels as contour; then repeat the process but
iterate through the columns
- Benefits: in theory, should pick up all edge pixels
- Drawbacks: what about edges between pixels; could miss
    pixels

4. Apply matplotlib's contour function to the binary mask
to generate a set of isophotes (QuadContourSet object), 
then convert the set of contour paths into a set of pixel
coordinates
- Benefits: ensure that all edge pixels are in the contour
- Drawbacks: edges are rough, and the curvature values
    can vary along a relatively straight line (see Future 
    Work)

* Curvature

Given a set of points along a contour, calculate the
curvature of the points using the equation

               |x'' y' - x' y'' |
curvature = ------------------------
            ((x')^2 + (y')^2)^(3/2)

where x' and y' indicate the first derivatives in x and y
and x'' and y'' indicate the second derivatives in x and y

===========================================================
Future Work
===========================================================

* Image Preprocessing:

The threshold currently used is dependent on the source
of the input image. If it is from the Childer's Lab, the
threshold value should be 56. If the image is from [2],
the threshold value should be 120. A few preprocessing 
techniques could be used to ensure only one threshold 
value is needed. These techniques include:
    
    - Histogram normalization
    - Replacing high valued pixels (halos around cells, 
      cell scaffolds, etc.) with a mean value, followed
      by Otsu thresholding
    - Using neural networks to learn features of the
      histograms and determining which threshold works
      best with which histogram

These techniques will be explored in the future.

* Contours/Curvatures:

While the method for calculating the curvature of the 
contours is mathematically correct, different methods for 
obtaining cell curvature produce different curvature
values. Currently, the curvature is calculated using 
contours generated using the numpy library, and curvatures
greater than 1/micrometer are being thresholded to 
1/micrometer. 

The curvature values can vary greatly in areas where the 
curve is uneven. We plan to explore 2 approaches for
mitigating this effect in the next stage of development:

    - Fit a polynomial to the curve and calculate the
      curvature of the polynomial
    - Smooth the curves before calculating the curvature

===========================================================
References/Related Work
===========================================================

[1] Z. Gitai, “The New Bacterial Cell Biology: Moving Parts
and Subcellular Architecture,” Cell, vol. 120, pp. 577–586,
2005.

[2] L. D. Renner, P. Eswaramoorthy, K. S. Ramamurthi, and 
D. B. Weibel, “Studying Biomolecule Localization by 
Engineering Bacterial Cell Wall Curvature,” PLoS One, 
vol. 8, no. 12, 2013.

[3] W. Draper and J. Liphardt, “Origins of chemoreceptor 
curvature sorting in Escherichia coli,” Nat. Commun., 
vol. 8, pp. 1–9, 2017.
