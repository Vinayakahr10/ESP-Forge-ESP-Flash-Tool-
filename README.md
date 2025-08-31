
<h1 align="center">ESP-Forge</h1>

> **ESP-Forge** – A modern, powerful GUI for flashing and monitoring Espressif chips.  
> Built with Python, designed for **ESP32, ESP8266**, and more.  

ESP-Forge is a standalone, cross-platform utility that simplifies the process of flashing firmware to Espressif devices. Acting as a graphical front-end for the popular `esptool.py`, it makes flashing and monitoring devices seamless for **developers, hobbyists, and professionals**.  

---

### ✨ Features

- **Multi-File Flashing** – Flash multiple `.bin` files to specific memory addresses simultaneously.  
- **Broad Chip Support** – ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP8266, and more.  
- **Save & Load Profiles** – Store flashing configs (files, addresses, chip type) as JSON for one-click reuse.  
- **Advanced Device Control**  
  - Erase flash with one click.  
  - Get chip info (MAC, type, etc.).  
- **Integrated Serial Monitor**  
  - Real-time logs with timestamps.  
  - Auto-scroll toggle.  
  - Save logs to file.  
- **Modern, Intuitive UI** – Clean dark theme, easy navigation.  

---

### 📥 Installation

#### Download Prebuilt Executable (Windows)
Simply grab the latest release from GitHub:

👉 [**Download ESP-Forge.exe**](https://github.com/Vinayakahr10/ESP-Forge/releases)

Run it directly — no installation required.

#### Run from Source (Developers)

```bash
# Clone the repository
git clone https://github.com/Vinayakahr10/ESP-Forge.git
cd ESP-Forge
```


# Install dependencies

```
pip install pyserial esptool
```

# Run the tool

```
python ESP-Forge.v1.py
```


---

### 📦 Build Your Own Executable

You can package ESP-Forge into a standalone `.exe` using **PyInstaller**.

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --name "ESP-Forge" ESP-Forge.v1.py
```

The binary will be created inside the  `/dist/` folder.
`dist` folder will be created inside  the `ESP-Forge` folder.


---


### ❓ Troubleshooting

**Empty results / failed connection?**

- Ensure the correct COM port is selected.
    
- Verify USB drivers are installed for your device.
    
- Try pressing the device **BOOT** button while flashing.
    

**Executable not running?**

- Ensure Python dependencies are installed if running from source.
    
- On Linux/Mac, run with `python3 esp32_uploader.py`.
    

---



