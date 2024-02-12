# 8mm-Digitaliser
Hardware and software designs for the worlds worst 8mm film scanner

The basic concept is the film is advanced frame by frame, as close as possible to exactly, and the frame is photographed by a digital camera.

This project consists of four parts:
* 3D printed parts for advancing the film
* Arduino microcontroller to control the stepper motor and camera
* Python script to align the images
* A few other shortcuts to turn it into a video

#### Film Holder and Advancer
This is a series of 3D printed parts to hold the film in place and advance it past a lamp. To save time, I designed it without a base, and bolted each piece to a wooden board. Parts requiring a bit of accuracy were printed with a base. Partially inspired by the operation of a cassette, the film is advanced by a single sprocket, and rests on a series of rollers (or just plastic cylinders to aid alignment).

The single driving sprocket was designed around the stepper motor used, which steps 7.5 degrees with each movement. Given that 8mm film sprocket holes are spaced 3.81 mm apart, the radius of the sprocket needs to be 29.106 mm. While the printer may not achieve this accuracy, the hope is any deviation causes a constant shift that can be countered later when cropping the photos.

For a lamp I used a battery powered LED lamp designed to be fitted to a camera horseshoe as kind of not-quite-ring lamp.

#### Stepping and Photographing
The camera used is a Canon 200D MkII, fitted with a macro adaptor and 200 mm lens, but any camera with an external trigger and suitably powerful lens could be used.

The stepper control has four buttons: step forward, step backward, run continuously, halt. After stepping the motor, the system waits for a 250 ms for everything to settle, fires the shutter, waits 500 ms for the shutter to finish, and then another 500 ms for cooling. This last part is imperative when using 3D printed parts - the motor when stopped (but enabled) dissipates 12W of heat which pretty soon starts softening the driving sprocket and causing it to misfire. Giving it half a second to cool by disabling it solves the heat problems.

The camera's trigger socket is only a 2.5 mm TRS connection:
* Tip: Shutter
* Ring: Focus
* Sleeve: Ground

By shorting T or R to S the camera will activate this function. With S connected to ground, T is "shorted" by enabling a 74HC126 tri-state buffer output. Otherwise the buffer is disabled and output in Hi-Z mode.

#### Aligning Photographs
