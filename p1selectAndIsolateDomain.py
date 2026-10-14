'''
Program Purpose:
This program allows user to select region/domain. Program will preprocess the image and isolate it.

Input:
- A multi-stack tiff file of domain (best if there's only one event/scene)

Output:
- A tiff file of isolated domain
'''

import cv2
import numpy as np
import tifffile
import math
from skimage.measure import label, regionprops
import os
import glob

tracked_xy = None
tracked_pixels = None


def preprocessing(img):
    gb = cv2.GaussianBlur(img, (7, 7), 3)
    _, th = cv2.threshold(gb, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dl = cv2.dilate(th, None, iterations=1)
    return dl


def get_regions(binary_img):
    labeled = label(binary_img)  # Identifies and labels individual regions
    regions = []
    for r in regionprops(labeled):
        if r.area > 100:
            regions.append(r)
    return regions


def isolate_region(frame, region):
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    coords = region.coords
    # Mask utilizes [row, col] ordering from skimage
    mask[coords[:, 0], coords[:, 1]] = 255
    isolated = cv2.bitwise_and(frame, frame, mask=mask)
    return isolated

def mouse_event(event, mx, my, flags, param):
    global tracked_xy, canny_img, tracked_pixels

    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked Coordinates: ({mx}, {my})")

        white_pixels = np.argwhere(canny_img == 255)

        click_point = np.array([my, mx])
        min_distance = 100
        closest_pixel = None

        # Search for closest white edge pixel to the user's click
        for pixel in white_pixels:
            # print(pixel, 'pixels')
            d = math.dist(pixel, click_point)
            if d < min_distance:
                min_distance = d
                closest_pixel = pixel
                tracked_pixels = pixel

        closest_y, closest_x = closest_pixel
        print(f"Closest Edge Pixel: ({closest_x}, {closest_y}) -- Distance: {min_distance:.2f} px")

        # Explicitly assign to global variable
        tracked_xy = (closest_x, closest_y)
        # print(tracked_pixels, 'tracked pixels')

# For my reference
# path = 'Stripe-fluctuations-Image_08413.tif'
# path = '2026Mar30-Infasurf-22-5uL-1.tif'
# path = 'img_04-14-25-Experiment 2-(5)Liq-Liq2-1.tif'
# path = 'curvyLines_Substack_247_298.tif'

files = glob.glob("*.tif")

if files:
    print("Detected .tif Files in Directory...")
    for idx, file_name in enumerate(files, 1):
        print(f"[{idx}] {file_name}")
    choice = input("\nSelect .tif File: ")
    selected_index = int(choice) - 1
    path = files[selected_index]

stack = tifffile.imread(path)
num_frames = len(stack)

cv2.namedWindow("TIFF Stack")
cv2.namedWindow("ProcessedImg")
# cv2.namedWindow("canny")

cv2.setMouseCallback('ProcessedImg', mouse_event)

# playback initialization
frame_idx = 0
paused = False
fps = 100

print("""
Playback Controls:
------------------
[Spacebar] : Pause / Play
[d]        : Step Forward (1 frame)
[a]        : Step Backward (1 frame)
[w]        : Increase Speed (Faster)
[s]        : Decrease Speed (Slower)
[f]        : Save
[q]        : Quit
""")
saved_frame = []

# stack loop
while True:
    frame = stack[frame_idx]

    # normalize image frame data to 8-bit scale to fix low contrast
    display = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX).astype("uint8")

    # image preprocessing
    processedImg = preprocessing(display)

    # edge detection
    canny_img = cv2.Canny(processedImg, 40, 90)

    # gather segmented regions for the current frame
    regions = get_regions(processedImg) # can implement pandas in the future for datasheets/tables??

    found = False
    # clicked region tracker to track amongst multiple frames
    if tracked_xy is not None:
        closest_x, closest_y = tracked_xy
        clicked_region = None

        # Search regions to locate which connected component contains the tracker
        for region in regions:
            minr, minc, maxr, maxc = region.bbox
            if minr <= closest_y <= maxr and minc <= closest_x <= maxc:
                clicked_region = region
                break

        # once clicked region is set, process isolation, crop, and rotation
        if clicked_region is not None:
            found = True
            # draw a bounding box on the display to show which domain is being tracked
            minr, minc, maxr, maxc = clicked_region.bbox
            cv2.rectangle(display, (minc, minr), (maxc, maxr), (0, 255, 0), 1)

            # isolate
            isolated = isolate_region(processedImg, clicked_region)

            cv2.imshow("domain", isolated)
            saved_frame.append(isolated)

            # draw a active tracker dot in center of region
            cy, cx = clicked_region.centroid
            tracked_xy = (int(cx), int(cy))
            cv2.circle(display, (int(cx), int(cy)), 3, (0, 0, 255), -1)
        if tracked_xy is not None and not found:
            print('Obj is now out of frame. Closing Window..')
            cv2.destroyAllWindows()

            if saved_frame:
                run_tag = input("\nEnter a suffix name for this run (e.g. run1, expB): ").strip()
                output_file = f"{run_tag}_isolatedStripedomain.tif"
                saved_stack = np.array(saved_frame)
                tifffile.imwrite(output_file, saved_stack)
                print('File automatically saved as: ' + output_file)

                saved_frame = []

            tracked_xy = None

    cv2.imshow("TIFF Stack", display)
    cv2.imshow("ProcessedImg", processedImg)
    # cv2.imshow("canny", canny_img)

    # keyboard/playback control
    k = cv2.waitKey(fps) & 0xFF

    if k == ord('q'):
        break
    elif k == ord(' '):
        paused = not paused
        print("Paused" if paused else "Playing")
    elif k == ord('d'):
        frame_idx = (frame_idx + 1) % num_frames
    elif k == ord('a'):
        frame_idx = (frame_idx - 1) % num_frames
    elif k == ord('w'):
        fps = max(1, fps - 20)
        print(f"Speed increased. Delay: {fps}ms")
    elif k == ord('s'):
        fps = fps + 20
        print(f"Speed decreased. Delay: {fps}ms")
    elif k == ord('f'):
        run_tag = input("\nEnter a suffix name for this run (e.g. run1, expB): ").strip()
        output_file = f"{run_tag}_isolatedStripedomain.tif"
        saved_stack = np.array(saved_frame)
        tifffile.imwrite(output_file, saved_stack)
        print('File personally saved as: ' + output_file)
        saved_frame = []
    elif not paused:
        frame_idx = (frame_idx + 1) % num_frames




cv2.destroyAllWindows()


''' 
Limitations/Need to work on:
- Regionprops is not detecting some regions or mistakes a region for another
- Some images have the corner static possibly due to camera lens that can interfere
- Color changes affect which ones are domains
'''