# KassonLib
up-to-date version of Kasson Tool - a Kasson Lab analysis semi-automated workflow

Requirements for work flow & processing imaging data:
  - Either Fiji or ImageJ (Fiji is preferred as this supports additional plugins that will not be available in ImageJ)
  - Licensed version of MATLAB
  - Python3 (>= version 3.8.0, <= version 3.10.0)
  - See below for details on these components...

Fiji/ImageJ Instructions:
  - Download for respective OS here: https://imagej.net/software/fiji/?Downloads and follow instructions for installation
  - Ideally place somewhere in UserProfile | user directory (either C:\Users\USERPROFILE\ on Windows or ~/user/ directory on Linux or /Applications/ on macOS)
  - Run the program, allow any updates & exit

MATLAB Instructions:
  - Ensure a working & licensed version of MATLAB (>= version 2017b) is installed on machine
  - Ensure the following toolboxes are also installed:
      - Simulink
      - Bioinformatics Toolbox
      - Computer Vision Toolbox
      - Curve Fitting Toolbox
      - Data Acquisition Toolbox
      - Database Toolbox
      - Image Processing Toolbox
      - Optimization Toolbox
      - Signal Processing Toolbox
      - Statistics and Machine Learning Toolbox
  - ***Note: it may be easier/faster to just install a new version of MATLAB & select these toolboxes, especially if several are missing...

Python Instructions:
  - Download Python3 for respective OS here: https://www.python.org/downloads/ and install (***version == 3.8.0)\
  - Necessary packages (not essential to manually download as install will take care of things if Python3 is installed)
      - imageio
      - Matplotlib
      - NumPy
      - Pandas
      - tqdm
      - fusion_review

***

INSTALLATION

- Download the KassonLib directory and place it somewhere accessible.
- Move/copy these files from the KassonLib/ directory into the ../Fiji.app/plugins/ subdirectory:
    - iText7-Core-7.1.2.zip
    - pdf_macroext-20130327.jar
- For WINDOWS:
    - Navigate to: "..\KassonLib-master\bin\bat\" & run install.bat
    - Go through the prompt messages & installation with Fiji/ImageJ
- For Linux (terminal commands delineated as $ ... ):
    - Navigate to: "../KassonLib-master/bin/sh/" & open a terminal instance in this path
    - $ chmod +x install.sh
    - $ "${PWD}"/install.sh
    - Follow the prompts that are printed on the terminal display
    - When prompted, paste/input ImageJ/Fiji path, for example: "/home/UserProfile/Desktop/Fiji.app/ImageJ-linux64"
    - Go through the prompt messages & installation with Fiji/ImageJ
- For macOS (terminal commands delineated as $ ... ):
    - pass
    - oof

***

WORKFLOW - QUICK GUIDE - [see UserGuide for more details]

- Feel free to use ../KassonLib-master/scripts/mat/misc/sneakPeek.m to test which parameters for each video to set
- Open an instance of ImageJ/Fiji
- If shortcut was created: for ImageJ [L] - for Fiji [F3]
- Alternatively, on the ImageJ/Fiji toolbar: Plugins >>> Tools >>> Kasson Tool
- Source Directory
  - Videos must be located in respective subdirectories (.tif files)
  - Must contain summary.txt file with appropriate formatting (see also, example template_summary.txt file in KassonLib directory)
  - Video filenames must contain "keyword" separated by underscores such as: "exampleVideoFile_keyword_Name.tif"
  - Keyword must be defined in summary.txt file in the HEADER section, ex: "vid: green"
- Destination Directory
  - Top-level directory where all analysis output will be sent
  - User can specify either empty directory or by default, a subdirectory will be created at: ../Fiji.app/KassonAnalysis_DataTemp
- Specify which analysis workflow to use:
   - [BobStyle - LipidMixingTraceAnalysis] will run a version of "Start Trace Analysis Program.m"
   - [LambdaStyle - ManualRescoring] will skip the above step and proceed directly to manual rescoring in Python3
- Input parameters
  - These should be determined beforehand, input text fields as they should appear in a MATLAB script
- Let it work
  - This is also a perfect opportunity for a tea/coffee break (You deserve it!)
- After completing, MATLAB console window should close and an instance of Python3 terminal should begin for manual rescoring process
- Follow the prompts, with 'h' flag input to display options
- To repeat the rescoring on multiple videos:
  - Windows: $ ptyhon -m fusion_review "C:\path\to\DestinationDirectory"
  - Linux/macOS: $ python3 -m fusion_review "/path/to/DestinationDirectory"
  - Use flag 'j' when rescoring all videos is complete to draw figure panels as .tif files
- Open "../KassonLib/scripts/mat/automation/postProcessing.m" with an instance of MATLAB
- Type into MATLAB command line interface:
  - $postProcessing("path/to/DestinationDirectory");
- Let it work
   - One could also say that this is another opportunity for a tea/coffee break (You still deserve it!)
 - { FIN }

***
TODO:
  - Add additional commentary & documentation!
