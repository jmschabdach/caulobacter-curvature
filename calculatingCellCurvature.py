"""
calculatingCellCurvature.py

Jenna Schabdach 2018

Read a phase image in and calculate the curvature of each cell in
the image. Produce a composite image of the original image overlaid
with the contours and curvatures of the cells as well as a histogram
of the curvature values.

"""
import SimpleITK as sitk
import pylab
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse

#=========================================================================
# Function Definitions
#=========================================================================

#-------------------------------------------------------------------------
# Part 1: Segment the image and identify individual cells
#-------------------------------------------------------------------------

def segmentCells(origImage, saveIntermediate=False, figFilePath="./"):
    """
    Segment the cells in the original image using multithreshold
    Otsu thresholding followed by opening (to remove small, non-cell
    objects).
    
    Inputs:
    - origImage: the original image (sitk Image)
    - saveIntermediate: flag to indicate whether to save
                        intermediate images (boolean)
    - figFilePath: the path to the location where the figure
                   will be saved (string)

    Returns:
    - segImage: the segmented image (sitk Image)
    """
    # Apply a multiple threshold Otsu filter to the image
    thresholdFilter = sitk.OtsuMultipleThresholdsImageFilter()
    thresholdFilter.SetNumberOfThresholds(2)
    otsuImage = thresholdFilter.Execute(origImage)
    otsuArray = sitk.GetArrayFromImage(otsuImage)
    
    # Save the raw segmentation
    if saveIntermediate:
        outFn = figFilePath+"00-multithreshold-otsu-filtered.png"
        plt.imsave(outFn, otsuArray, cmap='gray')
    
    # Extract the values we care about from the filtered image
    # We know the cells in the phase images should be the darkest
    # Get the darkest thresholded values
    segArray = 1*(otsuArray==0) # (otsuArray==0) produces booleans, multiplying by 1 makes the values int64
    # convert the array back to an image
    segImage = sitk.GetImageFromArray(segArray)
    
    # Pass the segmentation through an opening filter to remove small
    # objects that are not cells
    openingFilter = sitk.BinaryMorphologicalOpeningImageFilter()
    openingFilter.SetKernelRadius(2)
    openingFilter.SetKernelType(sitk.sitkBall)
    segImage = openingFilter.Execute(segImage)
    
    # Save the clean segmentation
    if saveIntermediate:
        outFn = figFilePath+"01-segmentation.png"
        segArray = sitk.GetArrayFromImage(segImage)
        plt.imsave(outFn, segArray, cmap='gray')

    return segImage 


def convertBinToLabelMap(segImage, saveIntermediate=False, figFilePath="./"):
    """
    Convert the binary segmentation image to a label map.
    Each component of the label map will be labelled using
    a separate label (labels are numbers, shown as colors).
    The labels should be separate cells, or closely clumped
    groups of cells.

    Inputs:
    - segImage: the binary segmentation image (sitk Image)
    - saveIntermediate: flag to indicate whether to save
                        intermediate images (boolean)
    - figFilePath: the path to the location where the figure
                   will be saved (string)
    
    Returns:
    - labelImage: the label map image (sitk Image)
    """
    # Set up label map filter
    convertToLabelMap = sitk.BinaryImageToLabelMapFilter()
    labelMap = convertToLabelMap.Execute(segImage)
    labelImageFilter = sitk.LabelMapToLabelImageFilter()
    labelImageFilter.SetNumberOfThreads(4)
    labelImage = labelImageFilter.Execute(labelMap)

    # Show the label map
    pylab.set_cmap('terrain')
    pylab.imshow(sitk.GetArrayFromImage(labelImage))

    # Print information about the label image
    labelArray = sitk.GetArrayFromImage(labelImage)
    print("Number of labels in the label map (including background):",
          np.amax(labelArray)-np.amin(labelArray)+1)

    # Need to change the pixel types
    castFilter = sitk.CastImageFilter()
    castFilter.SetOutputPixelType(sitk.sitkUInt8)
    labelImage = castFilter.Execute(labelImage)

    # The pixel type should be "8-bit unsigned integer"
    assert labelImage.GetPixelIDTypeAsString() == "8-bit unsigned integer"

    if saveIntermediate:
        outFn = figFilePath+"02-labelmap.png"
        segArray = sitk.GetArrayFromImage(segImage)
        plt.imsave(outFn, labelArray, cmap='nipy_spectral')

    return labelImage


#-------------------------------------------------------------------------
# Part 2: Estimate Cell Curvature
#-------------------------------------------------------------------------

def getCellContour(cellImage, saveIntermediate=False, figFilePath="./"):
    """
    Given a binary image of a cell, get the contour for that cell.
    
    Inputs:
    - cellImage: binary image mask of one cell (sitk Image)
    - saveIntermediate: flag to indicate whether to save
                        intermediate images (boolean)
    - figFilePath: the path to the location where the figure
                   will be saved (string)
    
    Returns:
    - contourPixels: a list of coordinates that represent the contour
                     of the cell
    """
    contourPixels = []

    # make a contour object of the segmented image
    contourObj = plt.contour(sitk.GetArrayFromImage(cellImage))
    paths = contourObj.collections[0].get_paths()[0]
    contourPixels = paths.vertices
    
    # save the contours to a file; saves all contours to one file because
    # of how this function is called
    if saveIntermediate:
        outFn = figFilePath+"03-contours.png"
        pylab.savefig(outFn, bbox_inches='tight')

    return contourPixels


def calculateContourCurvature(contourPixels):
    """
    Calculate the curvature of the contour of a cell.

    Inputs:
    - contourPixels: the binary image of the skeleton of the cell

    Returns:
    - contourCurvatures: the curvature of the skeleton of the cell
    - contourPixels: the locations of the curvature, as integers
    """
    # Calculate components for curvature
    # Get first derivatives in x and y
    contourPixels = np.asarray(contourPixels)
    dx = np.gradient(contourPixels[:, 0])
    dy = np.gradient(contourPixels[:, 1])

    # Get second derivatives in x and y
    dx2 = np.gradient(dx)
    dy2 = np.gradient(dy) 

    # Calculate the curvature of the curve
    contourCurvature = np.abs(dx2*dy - dx*dy2)/(dx*dx + dy*dy)**1.5
    
    # Threshold curvature values over 1 to be 1
    for i in range(len(contourCurvature)):
        if contourCurvature[i] > 1.0:
            contourCurvature[i] = 1.0            
    
    # Since the contour points may not be integers, make sure they are
    if type(contourPixels[0, 0]) is not int:
        contourPixels = [[int(round(pt[1])), int(round(pt[0]))] for pt in contourPixels]

    return contourCurvature, contourPixels


#-------------------------------------------------------------------------
# Part 3: Generate resulting images
#-------------------------------------------------------------------------

def saveCurvatureOverlay(origImage, curves, curvatures, figFilePath='./'):
    """
    Show the curvatures of the cells on the original image.
    
    Inputs:
    - origImage: the original greyscale image (sitk Image)
    - curves: the locations of the cell curves (list of lists of ints)
    - curvatures: the curvatures of the curves (list of floats)
    - figFilePath: the path to the location where the figure
                   will be saved (string)
                   
    Effects:
    - Makes a composite image consisting of the original image
    overlaid with colored versions of the curvatures. Also includes
    a colorbar.
    """
    # Make a new figure and show the original image
    pylab.figure(figsize=(35,25))
    pylab.set_cmap('gray')
    pylab.imshow(sitk.GetArrayFromImage(origImage))

    # Set up the overlay image
    shape = origImage.GetSize()
    overlay = np.zeros((shape[1], shape[0]))
    # Make the value 0.0 appear transparent
    overlay[overlay == 0.0] = np.nan

    # Iterate through the curve points and curvatures
    for point, value in zip(curves, curvatures):
        # Since we're capping the curvature value at 1 (potential miscalculations),
        # make sure the curvature values being plotted are at most 1.
        if value < 1:
            overlay[point[0], point[1]] = value
        else:
            overlay[point[0], point[1]] = 1
    
    # Combine the overlay image and the original image
    pylab.imshow(overlay, 'rainbow', alpha=1)
    # Add a colorbar
    pylab.colorbar()

    # Save the image with the curvatures
    outFn = figFilePath+'curvatures.png'
    pylab.savefig(outFn, bbox_inches='tight')


def saveCurvatureHistogram(curvatures, figFilePath='./'):
    """
    Given the list of curvature values, create a histogram of those
    values and save the histogram as a figure.
    
    Inputs:
    - curvatures: a list of the curvature values (list of floats)
    - figFilePath: the path to the location where the figure
                   will be saved (string)
                   
    Effects:
    - Prints a text table of statistics about the curvature
    histogram
    - Makes a histogram of the curvatures and saves it in the
    designated location
    """
    # set the number of bins
    numBins = 20
    outFn = figFilePath+'curvature-histogram.png'
    
    # print information about the histogram
    print('Curvature Statistics')
    print('---------------------------------------')
    print('Min:               ', np.amin(curvatures))
    print('Mean:              ', np.mean(curvatures))
    print('Median:            ', np.median(curvatures))
    print('Max:               ', np.amax(curvatures))
    print('Standard Deviation:', np.std(curvatures))
    
    # show the histogram
    pylab.figure(figsize=(7,7))
    pylab.hist(curvatures, numBins, facecolor='blue', alpha=0.7)
    pylab.title('Histogram of Curvatures')
    pylab.xlabel(u'Curvature (${\mu}m^{-1}$)')
    pylab.ylabel('Frequency')
    
    # save the histogram
    pylab.savefig(outFn, bbox_inches='tight')

#=========================================================================
# Main
#=========================================================================

def main():
    # Set up the arg parser
    parser = argparse.ArgumentParser(description="Identify individual caulobacter bacteria cells and calculate their curvatures.")
    # Arguments
    # - input image
    parser.add_argument('--inFn', type=str, help='Full path to the input image (.png, .jpg, etc; NOT .nd2)', required=True)
    # - save intermediate images (boolean)
    saveFlag = 'saveIntermediateFigures'  # need a variable to indicate whether this arg is used
    parser.add_argument('--saveIntermediateFigures', dest=saveFlag, action='store_true', help='Include this flag to indicate that the intermediately generated figures should be saved.')
    # Parse the arguments
    args = parser.parse_args()
    inputFn = args.inFn
    saveIntermediateFigures = args.saveIntermediateFigures

    # Initialization
    inputFnBase = inputFn.split('/')[-1].split('.')[0]
    figPath = "./figures/"+inputFnBase+"/"
    if not os.path.exists(figPath):
        os.makedirs(figPath)

    # Load the file
    reader = sitk.ImageFileReader()
    reader.SetFileName(inputFn)
    image = reader.Execute()

    # Part 0: Preprocessing
    # If the pixels have 4 components, they have been loaded as RGBA
    # images. All 3 RGB channels contain the same information, and
    # the 4th channel is full of 255s. We extract one channel and
    # use that channel as the image for processing purposes.
    if image.GetNumberOfComponentsPerPixel() == 4:
        # Convert the image to an array
        imageArray = sitk.GetArrayFromImage(image)
        # Pull the first channel from the array
        imageOneChannel = sitk.GetImageFromArray(imageArray[:,:,0])
        # Check the information of the single channel image is correct
        assert imageOneChannel.GetSize() == image.GetSize()
        assert imageOneChannel.GetDimension() == image.GetDimension()
        assert imageOneChannel.GetNumberOfComponentsPerPixel() == 1
        assert imageOneChannel.GetPixelIDTypeAsString() == "8-bit unsigned integer"
        # Use the first channel as the image
        image = imageOneChannel

    # Part 1: Segment and identify the cells
    # Segmentation
    segmentedImage = segmentCells(image, 
                                  saveIntermediate=saveIntermediateFigures,
                                  figFilePath=figPath)
    # Identify the cells
    labelMap = convertBinToLabelMap(segmentedImage, 
                                  saveIntermediate=saveIntermediateFigures,
                                  figFilePath=figPath)

    # Part 2: Calculate the curvature of each cell
    # Calculate the curvatures for all cells in the image
    curvatures = []
    curves = []
    labelArray = sitk.GetArrayFromImage(labelMap)

    # Iterate through each label
    for label in range(1,np.amax(labelArray)+1):
        singleLabel = (labelMap==label)
        # get the contour for the cell
        singleCurve = getCellContour(singleLabel, 
                                     saveIntermediate=saveIntermediateFigures,
                                     figFilePath=figPath)
        # get the curvature for the cell contour
        singleCurvature, singleCurve = calculateContourCurvature(singleCurve)
        # Add the contour points and the curvatures to the master lists of contours and curvatures
        curvatures.extend(singleCurvature)
        curves.extend(singleCurve)

    # Part 3: Generate result figures
    # Make the composite original image with curvatures
    saveCurvatureOverlay(image, curves, curvatures, figFilePath=figPath)
    # Show a histogram of curvatures
    saveCurvatureHistogram(curvatures, figFilePath=figPath)


if __name__ == "__main__":
    main()

