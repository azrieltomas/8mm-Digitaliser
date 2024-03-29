# 8mm-Digitaliser
Hardware and software designs for the worlds worst 8mm film scanner

After finding a reel of 8mm film I set out to try to digitise it. A quick attempt with my Epson v850 showed this was not a viable option, and a stubborn refusal to look online at anyone else's attempt (for a while) led to this.

The basic design concept is to advance the film reel frame by frame, as close as possible to exactly, and photograph each frame with a digital camera.

This project consists of four parts:
* 3D printed parts for advancing the film
* Arduino microcontroller to control the stepper motor and camera
* Python script to align the images
* A few other shortcuts to turn it into a video

### Film Holder and Advancer
This is a series of 3D printed parts to hold the film in place and advance it past a lamp. To save time, I designed it without a base, and bolted each piece to a wooden board. Parts requiring a bit of accuracy were printed with a base. Partially inspired by the operation of a cassette, the film is advanced by a single sprocket, and rests on a series of rollers (or just plastic cylinders to aid alignment and tension).

The single driving sprocket was designed around the stepper motor used (a cheap-ish Jaycar YM2754 I've had sitting around for years), which steps 7.5 degrees with each movement. Given that 8mm film perforations are spaced 3.81 mm apart, the radius of the sprocket needs to be 29.106 mm. While the printer may not achieve this accuracy, the hope is any deviation causes a constant shift that can be countered later when cropping the photos.

For a lamp I used a battery powered LED lamp designed to be fitted to a camera horseshoe as kind of not-quite-ring lamp.

![3D Parts](images/001_FreeCAD_Items.png)\
*3D Parts in FreeCAD*

### Stepping and Photographing
The camera used is a Canon 200D MkII, fitted with a macro adaptor and 200 mm lens, but any camera with an external trigger and suitably powerful lens could be used.

The stepper control has four buttons: step forward, step backward, run continuously, halt. After stepping the motor, the system waits for a 250 ms for everything to settle, fires the shutter, waits 500 ms for the shutter to finish, and then another 500 ms for cooling. This last part is imperative when using 3D printed parts - the stepper motor when stopped (but enabled) dissipates 12W of heat which soon starts softening the driving sprocket and causing it to slip. Giving it half a second to cool by disabling it solves the heat problems, and keeps the noise of the bench power supply down.

The camera's trigger socket is only a 2.5 mm TRS connection:
* Tip: Shutter
* Ring: Focus
* Sleeve: Ground

By shorting T or R to S the camera will activate this function. With S connected to ground, T is "shorted" by enabling a 74HC126 tri-state buffer output. Otherwise the buffer is disabled and output in Hi-Z mode. Alternatively a 5V relay can be used.

![Circuit Design](images/002_KiCAD_Schematic.png)\
*Circuit Design in KiCAD*

![A mess](images/005_setup.jpg)\
*Physical setup, experiencing continuous modification & improvement*

### Aligning Photographs
Prior to alignment, the photographs need to be cropped appropriately. I've done this either in Lightroom very quickly or by using ImageMagick (choosing a rough image size and start position):
```
for f in *.tif; do convert -crop (resx)x(resy)+(xpos)+(ypos) +repage $f crop_$f; done
```

This scanning system has a lot of bounce and shift. In an attempt to smooth it out, I tried the following to align the images:
* Hugin image stitcher (didn't really work)
* ImageJ / Fiji (didn't really work)
* Photoshop auto-align (awful results)
* Vidstab (decent results, but frame tracking starts to shift like a bad VCR)

The problem with the image programs is they're attempting to align the images in the 8mm frame, not the frame itself. For a moving camera film this is obviously not what we want.

After trying these I sought a better solution and came upon [cpixip's Super-8 detector](https://github.com/cpixip/sprocket_detection). This was a fantastic program and I could not thank them enough for their hard work (check out [their profile on Kinograph.cc](https://forums.kinograph.cc/u/cpixip/summary)), but a couple differences between Super-8 and 8mm meant this required some modification:
* Super-8 perforations are aligned with the centre of the image, 8mm is aligned with the top and bottom, meaning there are two holes per image (or rather, two halves)
* The 8mm film I have has Kodak lettering along the edge, which throws the detector at times

![A nice frame](images/003_Nice_Frame.jpg)\
*An easy frame to analyse*

![An annoying frame](images/004_K_Frame.jpg)\
*A more difficult frame to analyse*

![Perforation detection and shifting](images/006_scaled_diagram.jpg)\
*Detecting the perforations and shifting*

I made the following changes to cpixip's code:
* Implemented a function to loop through all images in a folder of a defined type (eg jpg, tif, etc)
* Crop the additional whitespace around the image
* Flip the image if necessary (all my images were photographed backwards)
* Adjustments to the "region of interest" to align with 8mm film
* Removed the histogram smoothing (this tends to throw it off because of extra noise in the film header)
* Resizes the canvas before moving the image (the perforation offset meant the image was getting chopped off otherwise)
* Does multiple passes on images that have not been shifted (ie, no perforation detected)
* Loop through all output images and resize their canvases to match
* Debug outputs:
	* If additional passes fail to detect the perforation, it will save an image with the ROI rectangle drawn over it
	* If required, save the histogram plot (requires matplotlib)

#### Use
```
python detectSprockets.py [file format] [optional: flip]
```

eg. detect in tiffs, without flipping
```
python detectSprockets.py tiff
```

eg. detect in pngs, flip image
```
python detectSprockets.py png flip
```

### Outputting Video
Now the out_* files are created, its a trival task to combine them with ffmpeg. You can use any codec you prefer, but here's an example for a easy uncompressed x264 video at 16 fps (the standard framerate for amateur 8mm film):
```
ffmpeg -framerate 16 -pattern_type glob -i '*.tif' -c:v libx264 -qp 0 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -pix_fmt yuv420p output.16fps.mp4
```

Of course my video was reversed, so the output needs reversing too:
```
ffmpeg -i output.16fps.mp4 -vf reverse -c:v libx264 -qp 0 reversed.mp4
```

Additional smoothing can be done with vidstab but I found it not worth it. There are plenty of online resources available for using ffmpeg and vidstab.

![Example final output](images/007_output.gif)\
*A few seconds of the final output, scaled down and trimmed and converted to a gif*

It is not a perfect solution, but it is good enough for now.

### Issues
Aside from the obvious misalignment, the whole setup suffers as below:
* Stepper motor generates too much heat and warps / softens the parts (even PETG)
* Alignment jigs only align one dimension
* Take up spool does not take up
* Camera physical parts likely to wear out
* Breadboard connections failed repeatedly

### Better Solutions
While keeping costs down, the best overall option is to fix alignment issues in hardware rather than software
* Just use an 8mm projector and modify it
* Use a better stepper motor
* Use a regular motor (with a few gear shifts to keep it turning slow) and an IR sensor to halt movement when the perforation passes it
* Alternatively, the right shutter speeds and slow movement could keep the system turning continuously, with the sensor triggering the camera only

Additional hardware changes that could be made:
* Use a mirrorless camera, not a DSLR
* Solder the controller
* 3D print a better alignment jig
* Implement sound capture with magnetic tape head (where required)

### Future
With no more 8mm films to digitise, the better solutions are being implemented in the [16mm Digitialiser](https://github.com/azrieltomas/16mm-Digitaliser)