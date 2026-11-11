import os
import cv2                      # slides write `import cv2 as cv`; same library, we keep the name cv2
import numpy as np              # Exercise 5 (images are NumPy arrays)
import matplotlib.pyplot as plt # Exercise 5 (side-by-side plot)
from scipy.signal import convolve2d as conv2      # Exercise 5 (apply the blur)
from skimage import color, data, restoration      # Exercise 5 (scikit-image)

# ==========================================
# PHASE 4: Introduction to Computer Vision (OpenCV)
# ==========================================
# Needs once:  pip install -r requirements.txt   (from the repo root; "Computer Vision" section)
#   = the slide's  pip install opencv-python scikit-image matplotlib  (+ scipy, numpy)
# Run:  python exercises.py   (or via menu.py -> Phase 4 -> Computer Vision)
#
# An image in OpenCV = a NumPy array of numbers (pixels):
#   colour    -> shape (height, width, 3)   3 numbers per pixel: Blue, Green, Red  (BGR, NOT RGB!)
#   grayscale -> shape (height, width)      1 number per pixel: 0 = black ... 255 = white

# ==========================================
# SHARED STUFF
# ==========================================
# Slide uses os.getcwd() + "data". getcwd() = the folder you RAN python from, so it breaks
# if you run from another folder. The folder of THIS file always works.
# Slide's image is data/Astronaut.png; ours sits right next to this file as Astronaut.jpg.
DATA_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(DATA_PATH, "Astronaut.jpg")

# Exercises 3-4 start the same way on the slides: check the file exists, then imread.
# Returns the colour image, or None (with a message) so the exercise can stop early.
def load_image():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found ({IMAGE_PATH})")
        return None
    img = cv2.imread(IMAGE_PATH)  # no mode given = IMREAD_COLOR (3 channels, BGR)
    if img is None:
        print(f"Error: unable to read the image ({IMAGE_PATH})")
    return img

# Shows windows until a key is pressed (click an image window first, then press a key)
#
# Why not just cv2.imshow like the slides? By default imshow opens an AUTOSIZE window:
# 1 image pixel = 1 screen pixel, and you can't resize it. Our Astronaut.jpg is
# 2406 x 3000 pixels, taller than a 1080p screen, so you'd only see the top part.
# WINDOW_NORMAL = a resizable window; we then shrink the WINDOW (not the image) to fit.
#
# Position: if we don't say WHERE, Windows cascades each new window further down-right,
# so with several windows some land off-screen. moveWindow puts them side by side
# from the top-left corner instead.
MAX_WINDOW_HEIGHT = 700  # pixels; change this if your screen is bigger/smaller
WINDOW_GAP = 10          # pixels between windows

def show_and_wait(windows: dict):
    x = 0  # left edge of the next window
    for title, image in windows.items():
        height, width = image.shape[:2]
        scale = min(1.0, MAX_WINDOW_HEIGHT / height)  # only shrink, never enlarge
        win_w, win_h = int(width * scale), int(height * scale)
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, win_w, win_h)
        cv2.moveWindow(title, x, 0)  # (x, y) of the window's top-left corner on screen
        cv2.imshow(title, image)
        x += win_w + WINDOW_GAP
    # Image windows open BEHIND this terminal sometimes: check the taskbar if you don't see them

    print("Press any key on an image window to close them...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# ==========================================
# Exercise 1: Reading Images File  (slide: 01_reading.py)
# ==========================================
#region
def run_exercise_1():
    # Decode in three different modes
    image1 = cv2.imread(IMAGE_PATH, cv2.IMREAD_COLOR)      # always 3 channels (BGR)
    image2 = cv2.imread(IMAGE_PATH, cv2.IMREAD_GRAYSCALE)  # 1 channel, black & white
    image3 = cv2.imread(IMAGE_PATH, cv2.IMREAD_UNCHANGED)  # exactly as the file is:
    # a PNG with transparency gives 4 channels (BGRA). A JPG has no transparency,
    # so here UNCHANGED looks the same as COLOR.

    # Check if each image loaded. imread does NOT raise an error on a wrong path,
    # it silently returns None, so we must check ourselves.
    for name, image in [("Color", image1), ("Grayscale", image2), ("Unchanged", image3)]:
        if image is None:
            print(f"Error: Image not found or unable to read. ({IMAGE_PATH})")
            return  # imshow(None) would crash, so stop here (the slide carries on)
        # Not on the slide: .shape shows the difference between the 3 modes
        print(f"{name} image loaded successfully! shape = {image.shape}")

    # Display all three images (each in its own window), then wait for a key press.
    # Slide: cv2.imshow(...) x3 + cv2.waitKey(0) + cv2.destroyAllWindows().
    # show_and_wait does the same, but sizes the windows to fit the screen (see SHARED STUFF).
    # The 3 windows open on top of each other: drag one aside to compare.
    show_and_wait({"Color Image": image1, "Grayscale Image": image2, "Unchanged Image": image3})
#endregion

# ==========================================
# Exercise 2: Writing Image File  (slide: 02_write.py)
# ==========================================
#region
OUTPUT_PATH = os.path.join(DATA_PATH, "Astronaut_gray.png")

def run_exercise_2():
    # Read as grayscale
    image = cv2.imread(IMAGE_PATH, cv2.IMREAD_GRAYSCALE)

    # Check if the image was loaded successfully
    if image is not None:
        # Save the grayscale image. The file EXTENSION picks the format (.png, .jpg, ...).
        # imwrite returns True/False instead of raising an error, so check it too.
        if cv2.imwrite(OUTPUT_PATH, image):
            print(f"Grayscale image saved successfully! -> {OUTPUT_PATH}")
        else:
            print("Error: could not save the image.")
    else:
        print(f"Error: Image not found or unable to read. ({IMAGE_PATH})")
#endregion

# ==========================================
# Exercise 3: Scaling Images  (slide: 03_scaling.py)
# ==========================================
#region
def run_exercise_3():
    img = load_image()
    if img is None:
        return

    # Extract dimensions. shape returns (height, width, channels) -> [:2] keeps the first two.
    # Careful: shape is (HEIGHT, width) but resize() wants (WIDTH, height)!
    height, width = img.shape[:2]

    # Enlarging the image to 2x. Making an image bigger means INVENTING new pixels;
    # `interpolation` = how to guess them:
    #   cv2.INTER_CUBIC  uses a 4x4 pixel neighbourhood -> smooth, good for enlarging (slower)
    #   cv2.INTER_LINEAR uses 2x2 (the default) -> faster, a bit softer
    #   cv2.INTER_AREA   best for SHRINKING
    res = cv2.resize(img, (2 * width, 2 * height), interpolation=cv2.INTER_CUBIC)
    print(f"Original: {width}x{height}  ->  Resized: {res.shape[1]}x{res.shape[0]}")
    # (If the big window doesn't fit your screen, that's just the window, the image is fine.)

    # Display the original and resized images
    show_and_wait({"Original Image": img, "Resized Image": res})
#endregion

# ==========================================
# Exercise 4: Rotating Images  (slide: 04_rotate.py)
# ==========================================
#region
def run_exercise_4():
    img = load_image()
    if img is None:
        return

    # Rotate the image by 45 degrees. Get the dimensions of the image
    height, width = img.shape[:2]

    # Calculate the center of the image (// = whole-number division)
    center = (width // 2, height // 2)

    # Get the rotation matrix for rotating the image by 45 degrees
    angle = 45  # positive = anti-clockwise

    # cv2.getRotationMatrix2D(center, angle, scale) returns a 2x3 affine transformation matrix
    # that can be used to rotate the image around the specified center point by the given angle.
    # scale 1.0 = keep the same size (0.7 would also shrink it so the corners fit)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    print(f"Rotation matrix (2x3):\n{rotation_matrix}")

    # Apply the rotation to the image. warpAffine moves every pixel using the matrix.
    # Output size stays (width, height), so the rotated CORNERS get cut off
    # and the empty areas are filled black.
    rotated_img = cv2.warpAffine(img, rotation_matrix, (width, height))

    # Display the original and rotated images
    show_and_wait({"Original Image": img, "Rotated Image": rotated_img})
#endregion

# ==========================================
# Exercise 5: Image Restoration  (slide: 05_image_restoration.py)
# ==========================================
#region
# Idea: damage a clean photo on purpose (blur + noise), then try to undo it.
# Uses scikit-image's built-in astronaut photo (data.astronaut()), not our Astronaut.jpg,
# exactly like the slide. Shown with matplotlib instead of cv2 windows: close the window to finish.
def run_exercise_5():
    # Setup a random number generator for adding 'noise' later
    rng = np.random.default_rng()

    # Prepare the image: load the astronaut and convert it to Grayscale (Black & White).
    # Restoration math is easier to learn on one colour channel rather than three (RGB).
    # rgb2gray also turns pixels into decimals 0.0 ... 1.0 (instead of 0 ... 255).
    astro = color.rgb2gray(data.astronaut())

    # Create a "Blur" filter (Point Spread Function - PSF).
    # This is a 5x5 matrix where every value is 1/25. It averages pixels together.
    psf = np.ones((5, 5)) / 25

    # Apply the blur to the image using 'convolution':
    # slide the 5x5 filter over every pixel, each new pixel = average of its 25 neighbours.
    # This simulates a camera being out of focus. 'same' = keep the original size.
    astro = conv2(astro, psf, 'same')

    # Add "Grain" or "Static" (Random Noise).
    # We multiply a standard normal distribution by the image's intensity (std = spread of values).
    astro += 0.1 * astro.std() * rng.standard_normal(astro.shape)

    # The Magic Step: Wiener Deconvolution.
    # This algorithm tries to reverse the blur while ignoring the random noise.
    # 'unsupervised' means it automatically guesses how much noise is in the image.
    # It returns 2 things; `_` = "I don't need the second one" (extra info about the estimate).
    print("Restoring the image (takes a few seconds)...")
    deconvolved, _ = restoration.unsupervised_wiener(astro, psf)

    # Visualization: Create a side-by-side comparison (1 row, 2 columns).
    # sharex/sharey = zooming into one picture zooms the other too.
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(8, 5), sharex=True, sharey=True)

    plt.gray()  # Tell matplotlib to show images in grayscale

    # Display the Blurry/Noisy version (same brightness range as the restored one, fair comparison)
    ax[0].imshow(astro, vmin=deconvolved.min(), vmax=deconvolved.max())
    ax[0].axis('off')
    ax[0].set_title('Blurred & Noisy')

    # Display the Cleaned version
    ax[1].imshow(deconvolved)
    ax[1].axis('off')
    ax[1].set_title('Restored (Wiener)')

    fig.tight_layout()
    plt.show()  # blocks until you close the window
#endregion

# ==========================================
# Computer Vision Menu
# ==========================================
# HOW TO ADD A NEW EXERCISE: write def run_exercise_N() above, add a line below.
EXERCISES = {
    "1": ("Exercise 1 : Reading Images File", run_exercise_1),
    "2": ("Exercise 2 : Writing Image File", run_exercise_2),
    "3": ("Exercise 3 : Scaling Images", run_exercise_3),
    "4": ("Exercise 4 : Rotating Images", run_exercise_4),
    "5": ("Exercise 5 : Image Restoration (Wiener)", run_exercise_5),
}

if __name__ == "__main__":
    print("Introduction to Computer Vision. Which code do you want to run?")
    for key, (description, _) in EXERCISES.items():
        print(f"{key}. {description}")

    valid_choices = ", ".join(EXERCISES.keys())
    choice = input(f"Enter choice ({valid_choices}): ").strip()

    if choice in EXERCISES:
        EXERCISES[choice][1]()
    else:
        print(f"Invalid choice. Please run the script again and select one of: {valid_choices}")
