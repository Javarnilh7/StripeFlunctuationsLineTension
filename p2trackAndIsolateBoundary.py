'''
Program Purpose:
This program allows user to manually track and select stripe edge to analyze.

Input:
- An isolated domain (white) tiff file from selectAndIsolateDomain.py

Outputs:
- A tiff file isolated & rotated tiff file of tracked stripe
- A csv file of saved coordinates where you anchored for manual tracking (for visual purposes the next time)
- An excel (xlsx) file of all white pixel coordinates in each frame
'''

import cv2
import numpy as np
import tifffile
import math
import os
import csv
import glob
import pandas as pd


# Global variables for the interactive phase
click_registered = False
current_clicked_pixel = None
canny_active_frame = None


def manual_click_callback(event, mx, my, flags, param):
    """
    Captures manual clicks and automatically snaps them to the closest edge pixel.

    Outputs: click_registered, current_clicked_pixel
    """
    global click_registered, current_clicked_pixel, canny_active_frame

    if event == cv2.EVENT_LBUTTONDOWN and canny_active_frame is not None:
        white_pixels = np.argwhere(canny_active_frame == 255)
        click_point = np.array([my, mx])
        min_distance = 100
        closest_pixel = None

        for pixel in white_pixels:
            d = math.dist(pixel, click_point)
            if d < min_distance:
                min_distance = d
                closest_pixel = pixel

        if closest_pixel is not None:
            closest_y, closest_x = closest_pixel
            current_clicked_pixel = (closest_x, closest_y)
            click_registered = True
            print(f"-> Snapped to edge at: {current_clicked_pixel}")
        else:
            current_clicked_pixel = (mx, my)
            click_registered = True
            print(f"-> No edge close. Using raw click: {current_clicked_pixel}")


def get_connected_pixels(canny_frame, sh, sw, closest_x, closest_y):
    """
    Floodfills the active frame from the seed point to find connected components.

    Output: clean_mask - numpy array with floodfill, filled_pixels - all white pixels in clean_mask
    """
    selectedEdge = np.zeros((sh + 2, sw + 2), np.uint8)
    flags = 8 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)

    cv2.floodFill(
        image=canny_frame,
        mask=selectedEdge,
        seedPoint=(closest_x, closest_y),
        newVal=0,
        loDiff=0,
        upDiff=0,
        flags=flags
    )

    floodfill_mask = selectedEdge[1:-1, 1:-1]
    filled_pixels = np.argwhere(floodfill_mask == 255)

    return floodfill_mask, filled_pixels


def find_initial_anchors(filled_pixels, tracked_xy):
    """Finds neighboring pixels within local radius of tracked position."""
    neighbors = []
    filled_pixels_xy = filled_pixels[:, [1, 0]]

    for pixels in filled_pixels_xy:
        d = math.dist(pixels, tracked_xy)
        px, py = pixels
        if d < 100 and (px, py) != tracked_xy:
            neighbors.append((px, py))

    min_dist = 100
    sec_min_dist = 100
    first_closest_pixel = None
    second_closest_pixel = None

    for pixels in neighbors:
        d = math.dist(pixels, tracked_xy)
        if d < min_dist:
            sec_min_dist = min_dist
            second_closest_pixel = first_closest_pixel
            min_dist = d
            first_closest_pixel = pixels
        elif d < sec_min_dist:
            sec_min_dist = d
            second_closest_pixel = pixels

    return neighbors, first_closest_pixel, second_closest_pixel


def trace_branch(start_pixel, neighbors, left_exclusion, max_steps=100, is_left_branch=True):
    """Traces a single side of the line branch up to max_steps."""
    branch = []
    if start_pixel is not None:
        current_pixel = start_pixel
        branch.append(current_pixel)

        for _ in range(max_steps):
            filterNeighbors = []
            for p in neighbors:
                if is_left_branch:
                    if p not in branch:
                        filterNeighbors.append(p)
                else:
                    if p not in left_exclusion and p not in branch:
                        filterNeighbors.append(p)

            if not filterNeighbors:
                break

            distances = []
            for p in filterNeighbors:
                distances.append(math.dist(p, current_pixel))

            closest_idx = np.argmin(distances)
            step_dist = distances[closest_idx]

            if step_dist < 2.0:
                current_pixel = filterNeighbors[closest_idx]
                branch.append(current_pixel)
            else:
                break

    return branch


def main():
    global canny_active_frame, click_registered, current_clicked_pixel

    files = glob.glob("*_isolatedStripeDomain.tif")

    if files:
        print("Detected .tif Files in Directory...")
        for idx, file_name in enumerate(files, 1):
            print(f"[{idx}] {file_name}")
        choice = input("\nSelect .tif File: ")
        selected_index = int(choice) - 1
        path = files[selected_index]
    else:
        print("Error: No '*_isolatedStripeDomain.tif' files found in current directory.")
        return

    if not os.path.exists(path):
        print(f"Error: Could not find image file '{path}' in current folder.")
        return

    stack = tifffile.imread(path)
    num_frames = len(stack)
    sh, sw = stack[0].shape[:2]

    # Storage structures
    valid_annotations = []
    calculated_frame_visualizations = []
    stabilized_crop_visualizations = []
    excel_export_list = []
    rotated_points_main = []
    manual_warp_visualizations = []

    # -------- MULTI-FILE SCANNING & PROMPT ------------
    csv_files = glob.glob("*.csv")
    imported_successfully = False

    if csv_files:
        print("\nDetected Saved Tracking Sheets in Directory:")
        for idx, file_name in enumerate(csv_files, 1):
            print(f"[{idx}] {file_name}")
        print("[M] Manual Tracking Mode (Start Fresh)")

        choice = input("Select a sheet number to import, or 'M' for manual mode: ").strip()

        if choice.lower() != 'm':
            try:
                selected_idx = int(choice) - 1
                if 0 <= selected_idx < len(csv_files):
                    chosen_csv = csv_files[selected_idx]
                    print(f"-> Extracting tracking points from: {chosen_csv}")

                    with open(chosen_csv, mode='r', newline='') as f:
                        reader = csv.reader(f)
                        header = next(reader)

                        for row in reader:
                            if row:
                                valid_annotations.append({
                                    "frame_idx": int(row[0]),
                                    "coords": (int(row[1]), int(row[2]))
                                })
                    imported_successfully = True
                else:
                    print("Invalid selection number. Defaulting to Manual Mode.")
            except (ValueError, IndexError):
                print("Invalid input format. Defaulting to Manual Mode.")

    # ----------- MANUAL ANNOTATION MODE -------------------------
    if not imported_successfully:
        window_name_1 = "Click Line on Each Frame"
        cv2.namedWindow(window_name_1)
        cv2.setMouseCallback(window_name_1, manual_click_callback)

        print("\n--- Starting Visual Manual Tracking Phase ---")

        for frame_idx in range(num_frames):
            current_frame = stack[frame_idx]
            canny_active_frame = cv2.Canny(current_frame, 40, 90)

            click_registered = False
            current_clicked_pixel = None
            user_finished_early = False
            skip_frame = False

            while not click_registered:
                display_img = cv2.cvtColor(canny_active_frame, cv2.COLOR_GRAY2BGR)
                cv2.putText(display_img, f"Frame {frame_idx + 1}/{num_frames}", (15, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                cv2.putText(display_img, "Click to track | [Space] to Skip | [r] if Done", (15, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                cv2.imshow(window_name_1, display_img)

                key = cv2.waitKey(30) & 0xFF
                if key == ord(" "):
                    skip_frame = True
                    break
                elif key == ord("r"):
                    user_finished_early = True
                    break
                elif key == ord("q"):
                    print("Program quitting...")
                    cv2.destroyAllWindows()
                    return

            if user_finished_early:
                break
            if skip_frame:
                print(f"-> Frame {frame_idx + 1} skipped from movie timeline.")
            else:
                valid_annotations.append({
                    "frame_idx": frame_idx,
                    "coords": current_clicked_pixel
                })

        cv2.destroyWindow(window_name_1)

    if len(valid_annotations) == 0:
        print("No frames processed. Exiting.")
        return

    print(f"--- Running Branch Calculations on {len(valid_annotations)} Frames... ---")

    # --------------- CALCULATIONS RUNNING PHASE ---------------------
    for loop_count, item in enumerate(valid_annotations):
        orig_idx = item["frame_idx"]
        tracked_xy = item["coords"]

        current_frame = stack[orig_idx]
        canny_frame = cv2.Canny(current_frame, 40, 90)

        limited_mask = np.zeros((sh, sw), np.uint8)
        color_visualization = limited_mask.copy()

        crop_size = 200
        crop_visualization = np.zeros((crop_size, crop_size), np.uint8)

        closest_x, closest_y = tracked_xy[0], tracked_xy[1]

        floodfill_mask, filled_pixels = get_connected_pixels(canny_frame, sh, sw, closest_x, closest_y)

        if filled_pixels.size > 0:
            neighbors, first_closest, second_closest = find_initial_anchors(filled_pixels, tracked_xy)

            if first_closest is not None and second_closest is not None:
                fx, fy = int(first_closest[0]), int(first_closest[1])
                sx, sy = int(second_closest[0]), int(second_closest[1])

                if (fx, fy) in neighbors and (sx, sy) in neighbors:
                    neighbors.remove(first_closest)
                    neighbors.remove(second_closest)

                left_branch = trace_branch(first_closest, neighbors, None, max_steps=100, is_left_branch=True)
                right_branch = trace_branch(second_closest, neighbors, left_branch, max_steps=100, is_left_branch=False)

                valid_neighbors = [tracked_xy] + left_branch + right_branch

                for pixel in valid_neighbors:
                    cx, cy = pixel[0], pixel[1]
                    if 0 <= cx < sw and 0 <= cy < sh:
                        color_visualization[cy, cx] = 255

            if 0 <= closest_x < sw and 0 <= closest_y < sh:
                color_visualization[closest_y, closest_x] = 255

        white_pixels_to_fit = np.argwhere(color_visualization == 255)

        # ---------- POLYFIT LINE & ROTATION -----------
        rotated_white_pixels = []

        if len(white_pixels_to_fit) > 20:
            y_coords = white_pixels_to_fit[:, 0]
            x_coords = white_pixels_to_fit[:, 1]

            m, b = np.polyfit(x_coords, y_coords, 1)
            angle = np.degrees(np.arctan(m))

            center = (int(closest_x), int(closest_y))
            M_opencv = cv2.getRotationMatrix2D(center, angle, 1.0)
            M_manual = cv2.getRotationMatrix2D(center, -angle, 1.0)

            alpha = M_manual[0, 0]
            beta = M_manual[0, 1]
            tx = M_manual[0, 2]
            ty = M_manual[1, 2]

            rows, cols = color_visualization.shape[:2]
            dst_img = np.zeros_like(color_visualization)

            for new_y in range(rows):
                for new_x in range(cols):
                    old_x = (alpha * new_x) + (beta * new_y) + tx
                    old_y = (-beta * new_x) + (alpha * new_y) + ty

                    src_x = int(round(old_x))
                    src_y = int(round(old_y))

                    if 0 <= src_x < cols and 0 <= src_y < rows:
                        dst_img[new_y, new_x] = color_visualization[src_y, src_x]

            full_rotated = cv2.warpAffine(color_visualization, M_opencv, (sw, sh))

            # --- Rotate individual pixel coordinates ---
            ones = np.ones(shape=(len(white_pixels_to_fit), 1))
            points_homogeneous = np.hstack([white_pixels_to_fit[:, [1, 0]], ones])

            rotated_points = np.matmul(M_opencv, points_homogeneous.T).T
            rotated_white_pixels = rotated_points
            rotated_points_main.append(rotated_white_pixels)

            # ------- CROPPING ----------
            x_start = closest_x - (crop_size // 2)
            x_end = closest_x + (crop_size // 2)
            y_start = closest_y - (crop_size // 2)
            y_end = closest_y + (crop_size // 2)

            if x_start >= 0 and x_end <= sw and y_start >= 0 and y_end <= sh:
                crop_visualization = full_rotated[y_start:y_end, x_start:x_end].copy()
            else:
                padded = cv2.copyMakeBorder(full_rotated, crop_size, crop_size, crop_size, crop_size,
                                            cv2.BORDER_CONSTANT, value=[0, 0, 0])
                px_start = (closest_x + crop_size) - (crop_size // 2)
                py_start = (closest_y + crop_size) - (crop_size // 2)
                crop_visualization = padded[py_start:py_start + crop_size, px_start:px_start + crop_size].copy()

        calculated_frame_visualizations.append(color_visualization)
        manual_warp_visualizations.append(dst_img)
        stabilized_crop_visualizations.append(crop_visualization)

        # ------- PANDAS PREPARATION --------------------
        if len(rotated_white_pixels) > 0:
            df_white = pd.DataFrame({
                "white x": rotated_white_pixels[:, 0],
                "white y": rotated_white_pixels[:, 1]
            })

            max_rows = len(df_white)
            df_frame_num = pd.DataFrame({"frame num": [orig_idx + 1] * max_rows})

            df_frame_combined = pd.concat([df_frame_num, df_white], axis=1)
            excel_export_list.append(df_frame_combined)

    # --------------- PLAYBACK PHASE (OPENCV ONLY) -----------------------
    #window_name_warp = "Warp Affine Playback"
    window_name_2 = "Final Movie Output"
    window_name_3 = "Live Stabilization (Close-up & Centered)"

    print("\n--- Initializing Displays ---")
    total_calc_frames = len(manual_warp_visualizations)

    print("\n--- Launching Movie Control Loop ---")
    print("Press [f] in any video window to save all outputs (TIFF, CSV, and Excel Sheets).")
    print("Press [q] in any video window to terminate.")

    current_frame_idx = 0

    while True:
        # Prepare frame views with overlay titles
        #warp_disp = cv2.cvtColor(manual_warp_visualizations[current_frame_idx], cv2.COLOR_GRAY2BGR)
        #cv2.putText(warp_disp, f"Warp Affine Playback - Frame {current_frame_idx + 1}/{total_calc_frames}",
                    #(15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

        #cv2.imshow(window_name_warp, warp_disp)
        cv2.imshow(window_name_2, calculated_frame_visualizations[current_frame_idx])
        cv2.imshow(window_name_3, stabilized_crop_visualizations[current_frame_idx])

        # Step to next frame
        current_frame_idx = (current_frame_idx + 1) % total_calc_frames

        # Listen for key press during frame playback interval (~120ms)
        key = cv2.waitKey(120) & 0xFF

        if key == ord("f"):
            run_tag = input("\nEnter a suffix name for this run (e.g. run1, expB): ").strip()

            output_tiff = f"{run_tag}_stabilized_crop.tif"
            output_csv = f"{run_tag}_tracked_coordinates.csv"
            excel_output_path = f"{run_tag}_pixel_coordinates_analysis.xlsx"

            # Export TIFF Stack
            rgb_export_list = [cv2.cvtColor(f, cv2.COLOR_GRAY2RGB) for f in stabilized_crop_visualizations]
            export_volume = np.stack(rgb_export_list, axis=0)
            tifffile.imwrite(output_tiff, export_volume, photometric='rgb')
            print(f"-> Saved Movie Stack: {output_tiff}")

            # Export Tracking Anchors CSV
            with open(output_csv, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Frame_Index", "X_Coord", "Y_Coord"])
                for item in valid_annotations:
                    writer.writerow([item["frame_idx"], item["coords"][0], item["coords"][1]])
            print(f"-> Saved Data Sheet: {output_csv}")

            # Export Excel White Pixel Coordinate Log
            if excel_export_list:
                with pd.ExcelWriter(excel_output_path, engine='openpyxl') as writer:
                    for df_frame in excel_export_list:
                        if not df_frame.empty:
                            frame_number = df_frame["frame num"].iloc[0]
                            sheet_name = f"Frame_{frame_number}"
                            df_frame.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"-> SUCCESS: Multi-sheet Excel log saved to: '{excel_output_path}'\n")
            else:
                print("-> Warning: No structural white pixel records found to build Excel sheet.")

            print("[RESUMING PLAYBACK] Focus back on OpenCV image windows.")

        elif key == ord("q"):
            print("Playback terminated cleanly.")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()