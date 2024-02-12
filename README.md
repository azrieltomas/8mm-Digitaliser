# 8mm-Digitaliser
Hardware and software designs for the worlds worst 8mm film scanner

After finding a reel of 8mm film I set out to try to digitise it. A quick attempt with my Epson v850 showed this was not a viable option, and a stubborn refusal to look online at anyone else's attempt led to this.

The basic concept is the film is advanced frame by frame, as close as possible to exactly, and the frame is photographed by a digital camera.

This project consists of four parts:
* 3D printed parts for advancing the film
* Arduino microcontroller to control the stepper motor and camera
* Python script to align the images
* A few other shortcuts to turn it into a video

### Film Holder and Advancer
This is a series of 3D printed parts to hold the film in place and advance it past a lamp. To save time, I designed it without a base, and bolted each piece to a wooden board. Parts requiring a bit of accuracy were printed with a base. Partially inspired by the operation of a cassette, the film is advanced by a single sprocket, and rests on a series of rollers (or just plastic cylinders to aid alignment).

The single driving sprocket was designed around the stepper motor used, which steps 7.5 degrees with each movement. Given that 8mm film sprocket holes are spaced 3.81 mm apart, the radius of the sprocket needs to be 29.106 mm. While the printer may not achieve this accuracy, the hope is any deviation causes a constant shift that can be countered later when cropping the photos.

For a lamp I used a battery powered LED lamp designed to be fitted to a camera horseshoe as kind of not-quite-ring lamp.

### Stepping and Photographing
The camera used is a Canon 200D MkII, fitted with a macro adaptor and 200 mm lens, but any camera with an external trigger and suitably powerful lens could be used.

The stepper control has four buttons: step forward, step backward, run continuously, halt. After stepping the motor, the system waits for a 250 ms for everything to settle, fires the shutter, waits 500 ms for the shutter to finish, and then another 500 ms for cooling. This last part is imperative when using 3D printed parts - the motor when stopped (but enabled) dissipates 12W of heat which pretty soon starts softening the driving sprocket and causing it to misfire. Giving it half a second to cool by disabling it solves the heat problems.

The camera's trigger socket is only a 2.5 mm TRS connection:
* Tip: Shutter
* Ring: Focus
* Sleeve: Ground

By shorting T or R to S the camera will activate this function. With S connected to ground, T is "shorted" by enabling a 74HC126 tri-state buffer output. Otherwise the buffer is disabled and output in Hi-Z mode.

### Aligning Photographs
Prior to alignment, the photographs need to be cropped appropriately. I've done this either in Lightroom very quickly or by using ImageMagick:
```
MAGICK COMMAND EXAMPLE HERE
```

A lot of trial and error led me to finding someone else who had attempted similar. The scanning system simply has too much bounce and shift to allow for a smooth output. I tried the following:
* Hugin image stitcher to align the images (didn't work)
* Photoshop auto-align (awful results)
* Vidstab (decent results, but frame tracking starts to shift like a bad VCR)

After these I came upon [cpixip's Super-8 detector](https://github.com/cpixip/sprocket_detection). This was a fantastic program and I could not thank them enough for their work (check out [their work on Kinograph.cc](https://forums.kinograph.cc/u/cpixip/summary)), but a couple differences between Super-8 and 8mm meant this required some modification:
* Super-8 sprocket holes are aligned with the centre of the image, 8mm is aligned with the top and bottom, meaning there are two holes per image (or rather, two halves)
* The 8mm film I have has Kodak lettering along the edge, which throws the detector at times

I made the following changes to cpixip's code:
* Implemented a function to loop through all images in a folder of a defined type (eg jpg, tif, etc)
* Crop the additional whitespace around the image
* Flip the image if necessary (all my images were photographed backwards)
* Adjustments to the "region of interest" to align with 8mm film
* Removed the histogram smoothing (this tends to throw it off because of extra noise in the film header)
* Resizes the canvas before moving the image (the sprocket hole offset meant the image was getting chopped off otherwise)
* Does a second pass on images that have not been shifted (ie, no sprocket hole detected)
* Loop through all output images and resize their canvases to match
* Debug outputs:
	* If second pass fails to detect the sprocket hole, it will save an image with the ROI rectangle drawn over it
	* If required, save the histogram plot (requires matplotlib)


### Outputting Video
Now the out_* files are created, its a trival task to combine them with ffmpeg. You can use any codec you prefer, but here's an example for a easy uncompressed x264 video at 16 fps:
```
FFMPEG EXAMPLE HERE
```

Of course my video was reversed, so the output needs reversing too:
```
FFMPEG EXAMPLE HERE
```

For additional smoothing with vidstab:
```
FFMPEG EXAMPLE HERE
```

### Examples


### Better Solutions
If I were to continue with other reels, I'd like to eventually have the alignment issues solved by hardware instead of software. Possible solutions:
* Just use an 8mm projector and modify it
* Use a better stepper motor
* Use a regular motor (with a few gear shifts to keep it turning slow) and an IR sensor to halt movement when the sprocket hole passes it

Additionally, I recommend using a mirrorless camera over the DSLR.
