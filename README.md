# **ESP-Forge**

**A powerful, modern GUI for flashing and monitoring Espressif chips, built with Python.**

ESP-Forge is a standalone, cross-platform tool designed to simplify the process of flashing firmware to ESP32, ESP8266, and other Espressif devices. It acts as a user-friendly graphical front-end for the powerful esptool.py command-line utility, providing a robust interface for developers, hobbyists, and professionals.

*(**Note:** You should replace the URL above with a real screenshot of your application's main window.)*

## **📥 Downloads**

The easiest way to use ESP-Forge is to download the latest pre-compiled executable for Windows. No installation is required.

[**➡️ Download the latest release from the GitHub Releases page**](https://www.google.com/search?q=https://github.com/your-username/ESP-Forge/releases)

Simply download the ESP-Forge.exe from the latest release and run it.

## **✨ Key Features**

* **Multi-File Flashing:** Flash multiple binary files (.bin) to specific memory addresses simultaneously.  
* **Broad Chip Support:** Works with a wide range of chips, including ESP32, ESP32-S2, ESP32-S3, ESP32-C3, and ESP8266.  
* **Save & Load Profiles:** Save your complete flashing configuration (files, addresses, chip type) to a JSON file and load it later for one-click flashing.  
* **Advanced Device Control:**  
  * **Erase Flash:** Securely wipe the entire flash memory of the device with a single click.  
  * **Get Chip Info:** Quickly retrieve device details like MAC address and chip type to verify your connection.  
* **Integrated Serial Monitor:** A full-featured serial monitor to view device output, including:  
  * Real-time timestamps for precise debugging.  
  * Auto-scroll control.  
  * The ability to save logs to a file.  
* **Modern, Intuitive UI:** A clean, dark-themed interface that's easy to navigate.

## **🛠️ Running from Source (For Developers)**

If you prefer to run the application directly from the Python source code, follow these steps.

### **Prerequisites**

* **Python 3.6+** installed on your system.  
* **pip** (Python's package installer).

### **Steps**

1. **Clone the Repository:**  
   git clone \[https://github.com/your-username/ESP-Forge.git\](https://github.com/your-username/ESP-Forge.git)  
   cd ESP-Forge

2. Install Dependencies:  
   Run the following command in your terminal to install the necessary libraries:  
   pip install pyserial esptool

3. **Run the Application:**  
   python esp32\_uploader.py

## **📦 Building the Executable from Source**

You can package ESP-Forge into a single .exe file yourself using **PyInstaller**.

### **Install PyInstaller**

pip install pyinstaller

### **Build the Executable**

Run the following command from the project directory:

pyinstaller \--onefile \--windowed \--name "ESP-Forge" esp32\_uploader.py

The final ESP-Forge.exe will be located in the newly created dist folder.

## **📄 License**

This project is licensed under the MIT License. See the LICENSE file for details.
