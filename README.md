# **Project stripeDomainFFT**

Lisa Vang | 10/14/2026

Purpose: To analyze stripe-phase domain boundary fluctuations using Fourier transform to find the best range of frequency waves that best mimics the fluctuations of domain boundary.

Installation   
This project uses Python 3.14.3.

Download the project folder as a zipped file and unzip.

Dependencies/Libraries  
To run stripeDomainFFT, follow the following steps to install the following libraries in a virtual environment:

Windows

1) Locate the folder of the project.  
2) Open Anaconda Prompt and run the following to create a venv:

   conda create \--name stripeenv

3) Activate virtual environment

   conda activate stripeenv

4) Install pip in virtual environment

   conda install pip

5) Install dependencies

   pip install \-r requirements.txt

6) Install Spyder Kernels (if prompted and needed)  
   pip install spyder-kernels==3.1.\*

Now you have a virtual environment specifically for this project. Anytime you want to activate it, you can just use/select:  
conda activate stripeenv

Setup

\*\* Make sure you have a tiff file already moved to the StripeFlunctuationLineTension folder before running any program.

If you want to run/use the project with IDEs:

Spyder:

1) Open Anaconda (if not already)  
2) Launch Spyder   
3) Open program/project  
4) Plot setup: Go to Tools \> Preferences \> IPython Console \> Plotting \> Graphics backend \> Set backend to Automatic \> Apply \> Ok  
5) Environment setup: Go to Tools \> Preferences \> Python interpreter \>  Select “Selected interpreter” \> Hover above the arrow and choose stripeenv environment \> Apply \> Ok  
6) Console setup: Go to Consoles \> New Console in environment \> select stripeenv environment

Pycharm:

1) Open StripeFlunctuationLineTension project  
2) At the bottom right corner where it says “interpreter”, change the virtual environment to stripenv.  
3) Select the program you want to run and hit the run button at the top\!

Visual Studio:

1) Open VS  
2) Select “Open a folder” and select StripeFlunctuationsLineTension  
3) Select file you want to run  
4) Near the top middle bar next to a package icon, change virtual env to stripeenv.  
5) Hit the run button to execute\!

Visual Studio Code:

1) Open VS Code  
2) At the top left corner, click on “file”.  
3) Select “Open folder” and select the StripeFlunctuationsLineTension folder  
4) Select a program file  
   1) If you do not yet have the Python extension, install that, an automatic prompt should appear at bottom right.  
5) On the bottom right corner, click on the python version/interpretor and select stripeenv environment.  
6) Hit the run button to execute\!

If you want to run on a terminal:

Anaconda Prompt:

1) Open Anaconda Prompt  
2) Navigate to StripeFlunctuationsLineTension folder  
3) Activate stripeenv environment with:  
   conda activate stripeenv  
4) Run program of choice with:

   python \<insert name of program \>

5) The program executes immediately\!

---

**\<p1selectAndIsolateDomain.py\>**

Purpose: Select a stripe/domain you want to follow and the program will isolate it.

Before running the program:

- Have your stripe domain in a multistack .tif file format and in your directory.

How to run the program:

1) Run \<p1selectAndIsolateDomain.py\>  
2) Enter the number that corresponds with the desired file you intend to use.  
3) In the ProcessedImg window, click on a domain you want to isolate.  
4) Use playback controls to your intent.

   Playback Controls:

   \------------------

   \[Spacebar\] : Pause / Play

   \[d\]        : Step Forward (1 frame)

   \[a\]        : Step Backward (1 frame)

   \[w\]        : Increase Speed (Faster)

   \[s\]        : Decrease Speed (Slower)

   \[f\]        : Save

   \[q\]        : Quit

	

If ‘f’ is entered, the program will save a tif file of the isolated domain/stripe in your directory, which can be used for the second program \<trackAndIsolateBoundary.py\>.

---

**\<p2trackAndIsolateBoundary.py\>**

Purpose: Manual tracking of stripe boundary, rotates tracked boundary based on best fit line (polyfit)’s angle. Then, gets all rotated boundary pixel coordinates and saves them into an excel file.

Before running the program:

- Have a binary multistack .tif file of your isolated stripe domain in directory (can be obtained from \<p1selectAndIsolateDomain.py\>.

How to run the program:

1) Run \<p2trackAndIsolateStripe.py\>  
2) Enter into the console the number that corresponds to the .tif file containing the isolated domain you intend to track.  
3) Tracking section:

If this is your first run and no csv files are detected…

4) The program will automatically begin a manual tracking software if no csv file is in the directory. Click on the boundary you want to track. Once clicked, the program will automatically move to the next frame.   
   1) If you would like to skip a frame, press \[Space\].  
   2) If you would like to finish tracking early, press \[r\].

If you have ran the program before…

4) If the program detects a csv file in the directory and you would like to use the same points of tracking as previous runs, enter a number that corresponds to your tracking sheet.  
4) If a csv file is detected, but you would like to start the manual tracking software, enter “M” into the console.  
5) The program is now calculating…give it a few seconds.  
6) Once calculations have finished, you should see two windows, a movie of the isolated boundary in original placement and a movie of the isolated, rotated, and centered boundary. It’s good to note that these are for display only.  
7) Use the following keys to do as intended.  
     
   \[f\] \---\> to save all outputs (TIFF, CSV, and Excel Sheets).  
   \[q\] \---\> to terminate.

   If ‘f’ is pressed, enter into the console a tag you want the following files saved as. The program will save three things: a multistack .tif file of isolated/rotated/centered boundary (display only), a csv file of tracked coordinates used, and an excel sheet of raw rotated coordinates that will be used in \<p3computeFFT.py\>.

---

**\<p3computeFFT.py\> or \<p3computeFFTMicrons.py\>**

\*\*\* FFT programs in progress  
\*\*\* Select \<p3computeFFTMicrons\> for FFT computation in microns.

Purpose: Plots rotated coordinates of boundary on matplotlib, uses interpolation, Fast Fourier Transform to compute Fourier coefficients of boundary.

Before running the program:

- Have an excel file containing rotated coordinates of a boundary in the directory (can be obtained from \<p2trackAndIsolateBoundary.py\>.

How to run the program:

\*\*\* In the default program, the individual frame’s FFT graph is commented. If you want to see each frame’s graph, uncomment lines 113 \- 185 (or 112-186 for microns program) in an IDE, then save and rerun.

1) Run \<p3computeFFT\> or \<p3computeFFTMicrons\>  
2) Enter into the console the number that corresponds with the excel file you intend to use.  
3) The program will compute…  
   1) If you chose to see the individual graphs: The program will calculate FFT and generate 5 graphs: original plotting of rotated boundary, interpolated boundary, two FFT graphs (indices and frequency), and a squared coefficient graph.  
4) Enter a tag name and the program will save the mode, squared mode, and real squared coefficients to an excel file for next use in \<p4fitline\> or \<p4fitlineMicrons\>.

---

**\<p4fitline.py\> or \<p4fitlineMicrons.py\>**

\*\*\* Linear Line of Best Fit programs (in progress)  
\*\*\* Select \<p3computeFFTMicrons\> for FFT computation in microns.

Purpose: To find a linear line of best fit amongst FFT squared coefficients. 

\*\*\* Because this program is still in testing. There are two methods in this program: 1\) average best fit line amongst all the frames’s best fit line and 2\) best fit line after averaging coefficients at each mode.   
\*\*\* You are also able to select the range of the modes (ex. 2-6, 1-10, etc.). It will be prompted in the console.

Before running the program:

- Have an excel file containing the mode, squared mode, and squared fft coefficients in the directory (can be obtained from \<p3computeFFT.py\> or \<p3computeFFTMicrons.py\>.

How to run the program:

1) Run \<p4fitline.py\> or \<p4fitlineMicrons.py\>.  
2) The console will now prompt you, select (by typing its corresponding number) into the console.  
3) Then enter your range (low and high ends of the range) as according to the prompt.  
4) A graph should pop up after completing its calculations. It contains both methods of averaging best fit lines.  
5) Save the graph.

