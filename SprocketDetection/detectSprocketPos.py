import cv2
import numpy as np
import time
import sys
import os
import matplotlib.pyplot as plt # debug only

## simple sprocket detection algorithm
## returns the detected sprocket position
## relative to vertical scan center and left horizontal edge
def detectSprocketPos(img, roi = [0.15,0.30,0.01,0.45],     # region-of-interest - set as small as possible
                           thresholds = [0.5,0.2],          # edge thresholds; first one higher, second one lower
                           filterSize = 25,                 # smoothing kernel - leave it untouched
                           minSize = 0.05,                  # min. relative sprocket size to be expected - used for checks
                           horizontal = False,              # if you want a simple horizontal alignment as well
                           fileName = 'debug',               # filename of original image for debug outpu
                           debugHist = False):             

    ## inital preparations
    #620x531: 93,217,5,239
    
    # get the size of the image     
    dy,dx,dz = img.shape

    # convert roi coords to real image coords
    x0 = int(roi[0]*dx)
    x1 = int(roi[1]*dx)
    
    y0 = int(roi[2]*dy)
    y1 = int(roi[3]*dy)        

    # cutting out the strip to work with
    sprocketStrip = img[y0:y1,x0:x1,:]

    # now calculating the vertical sobel edges
    sprocketEdges = np.absolute(cv2.Sobel(sprocketStrip,cv2.CV_64F,0,1,ksize=3))

    # by averaging horizontally, only promient horizontal edges
    # show up in the histogram
    histogram     = np.mean(sprocketEdges,axis=(1,2))

    # we dont need the smoothed histogram - its detrimental in some cases because the film header
    # contains letters that get puicked up by the algorithm

    # debug - save histogram
    if debugHist:
        outName = 'hist_' + fileName + '.png'
        plt.plot(histogram)
        plt.savefig(outName)
        plt.close()

    # smoothing the histogram to make signal more stable.
    # sigma==0 -> it is autocalculated
    # smoothedHisto = cv2.GaussianBlur(histogram,(1,filterSize),0)

    # debug - save histogram
    # outName = 'smoothhist_' + datetime.now().strftime('%H%M%S.%f') + '.png'
    # plt.plot(smoothedHisto)
    # plt.savefig(outName)
    # plt.close()

    ## now analyzing the smoothed histogram
    
    # everything is relative to the detected maximum of the histogram
    # we only work in the region where the sprocket is expected
    # maxPeakValue   = smoothedHisto[y0:y1].max()
    maxPeakValue   = histogram[y0:y1].max()

    # the outer threshold is used to search for high peaks from the outside
    # it should be as high as possible in order to suppress that the algorithm
    # locks onto bright imprints of the film stock
    outerThreshold = thresholds[0]*maxPeakValue

    # the inner threshold is used to really search for the boundaries of
    # the sprocket. Implicitly it is assumed here that the area within
    # the sprocket is very evenly lit. If a lot of dust is present in
    # the material, this threshold should be raised higher
    innerThreshold = thresholds[1]*maxPeakValue

    # searching for the sprocket from the outside, first from below
    # we start not right at the border of the histogram in order to
    # avoid locking at bad cuts which look like tiny sprockets
    # to the algorithm    
    outerLow       = y0
    for y in range(y0,y1):
        if histogram[y]>outerThreshold:
            outerLow = y                 
            break
        
    # now searching from above
    outerHigh      = y1
    for y in range(y1 - y0 - 1,outerLow,-1):
        if histogram[y]>outerThreshold:
            outerHigh = y
            break

    # simple check for valid sprocket size. We require it
    # to be less than a third of the total scan height.
    # Otherwise, we give up and start the inner search
    # just from the top third of the frame. This could be
    # improved - usually, the sprocket size stays pretty constant
    if (outerHigh-outerLow)<0.3*dy:
        searchCenter = (outerHigh+outerLow)//2
    else:
        searchCenter = dy//3

    # searching sprocket borders from the inside of the sprocket.
    # For this, the above found potential center of the sprocket
    # is used as a starting point to search for the sprocket edges 
    innerLow = searchCenter
    for y in range(searchCenter,outerLow,-1):
        if histogram[y]>innerThreshold:
            innerLow = y
            break
            
    innerHigh = searchCenter
    for y in range(searchCenter,outerHigh):
        if histogram[y]>innerThreshold:
            innerHigh = y
            break

    # a simple sanity check again. We make sure that the
    # sprocket is larger than maxSize and smaller than
    # the outer boundaries detected. If so, not correction
    # is applied to the image
    sprocketSize    = innerHigh-innerLow
    minSprocketSize = int(minSize*dy)
    if minSprocketSize<sprocketSize and sprocketSize<(outerHigh-outerLow) :
        sprocketCenter = (innerHigh+innerLow)//2
    else:
        sprocketCenter = dy//2
        sprocketSize   = 0
        
    # now try to find the sprocket edge on the right side
    # if requested. Only if a sprocket is detected at that point
    # Not optimized, quick hack...
    xShift = 0
    if horizontal and sprocketSize>0:
        # calculate the region-of-interest
        
        # we start from the left edge of our previous roi
        # and look two times the
        rx0 = x0
        rx1 = x0 + 2*(x1-x0)

        # we use only a part of the whole sprocket height
        ry = int(0.8*sprocketSize)
        ry0 = sprocketCenter-ry//2
        ry1 = sprocketCenter+ry//2

        # cutting out the roi
        horizontalStrip = img[ry0:ry1,rx0:rx1,:]

        # edge detection
        horizontalEdges = np.absolute(cv2.Sobel(horizontalStrip,cv2.CV_64F,1,0,ksize=3))

        # evidence accumulation
        histoHori       = np.mean(horizontalEdges,axis=(0,2))
        smoothedHori    = cv2.GaussianBlur(histoHori,(1,5),0)

        # normalizing things
        maxPeakValueH   = smoothedHori.max()
        thresholdHori   = thresholds[1]*maxPeakValueH
        
        # now searching for the border
        xShift = 0
        for x in range((x1-x0)//2,len(smoothedHori)):
            if smoothedHori[x]>thresholdHori:
                xShift = x                 
                break
            
        # readjust calculated shift
        xShift = x1 - xShift
        
    return (xShift,dy//2-sprocketCenter)


## simple image transformation
def shiftImg(img,xShift,yShift):
    
    # create transformation matrix
    M = np.float32([[1,0,xShift],[0,1,yShift]])

    # ... and warp the image accordingly
    img = cv2.copyMakeBorder(img, top=0, bottom=yShift, left=0, right=xShift, borderType=cv2.BORDER_CONSTANT)
    return cv2.warpAffine(img,M,(img.shape[1],img.shape[0]))

# crop whitespace from image
def cropImage(img):
    grey        = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grey        = 255*(grey < 128).astype(np.uint8) # To invert the text to white
    coords      = cv2.findNonZero(grey) # Find all non-zero points (text)
    x, y, w, h  = cv2.boundingRect(coords) # Find minimum spanning bounding box
    return img[y:y+h, x:x+w]

## test routine if called as script
## loops through all images in a folder of a specific type
## eg python3 detectSprocketPos.py tiff
if __name__ == '__main__':
    # create list of files
    fileExtension   = sys.argv[1]
    allFiles        = list()
    for fileName in os.listdir():
        if fileName.endswith(fileExtension):
            allFiles.append(fileName)

    maxWidth            = 0
    maxHeight           = 0

    # do transformation
    for files in allFiles:
        # get the input image
        inputImg       = cv2.imread(files)
        print(files)

        # time the processing
        tic            = time.time()

        # flip images if necessary
        if sys.argv[2] == 'flip':
            inputImg = cv2.flip(inputImg, 1)

        # crop whitespace 
        # save the file when debugging the sprocket locations
        inputImg        = cropImage(inputImg)
        #cv2.imwrite('crop_' + files,inputImg)
        
        # run sprocket detection routine
        shiftX, shiftY = detectSprocketPos(inputImg, horizontal=True, fileName=files, debugHist=False)

        # second attempt if failed with modified roi - sometimes happens with the header lettering
        if (shiftX + shiftY) == 0:
            print('Failed to detect sprockets, attempting second pass')
            shiftX, shiftY = detectSprocketPos(inputImg, horizontal=True, roi=[0.15,0.25,0.1,0.55], fileName=files, debugHist=True)

        # shift the image into its place
        outputImage    = shiftImg(inputImg,shiftX,shiftY)
        toc            = time.time()

        # now output some test information
        dy,dx,dz       = outputImage.shape
        print('Sprocket-Detection in %3.1f msec, img-Size %d x %d'%((toc-tic)*1000,dx,dy))
        print('Applied shifts: (%d,%d)'%(shiftX,shiftY))

        # store largest image dimensions
        if outputImage.shape[1] > maxWidth:
            maxWidth    = outputImage.shape[1]
        if outputImage.shape[0] > maxHeight:
            maxHeight   = outputImage.shape[0]

        # write out the result
        # if no shift has occured, flag these for investigation
        if (shiftX + shiftY) == 0: # no shift

            cv2.imwrite('NOSHIFT_' + files,outputImage)
        else:
            cv2.imwrite('out_' + files,outputImage)

    print('Max image height: ' + str(maxHeight))
    print('Max image width: ' + str(maxWidth))

    # resize all images to the same dimensions, fill space with black
    # later we can crop these to just the frame (when we know its size)
    savedFiles          = list()
    for fileName in os.listdir():
        if fileName.endswith(fileExtension):
            if fileName.startswith('out_'):
                savedFiles.append(fileName)

    for files in savedFiles:
        img             = cv2.imread(files)

        xPad            = maxWidth - img.shape[1]
        yPad            = maxHeight - img.shape[0]
        print('Maximum image dimensions: (' + str(maxWidth) + ', ' + str(maxHeight) + ')')
        print('Resizing ' + files + ' by: (' + str(xPad) + ', ' + str(yPad) + ')')

        img             = cv2.copyMakeBorder(img, top=0, bottom=yPad, left=0, right=xPad, borderType=cv2.BORDER_CONSTANT)
        cv2.imwrite(files,img)