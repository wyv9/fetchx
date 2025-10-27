# <img src="docs/images/icon-32.png" width="60" alt="Icon"> FetchX

**A simple open source auto image processing tool for you :3**

Download the [Latest FetchX Release](https://wyv9.github.io/fetchx)

<img src="docs/images/h.png" width="500" hight="300" alt="Icon">


## Features
-  **Multi-format Support**: PNG, JPG, WebP, BMP, TIFF
-  **Custom Resolution Output**: *For example:* Stretch 800x600 to 1366x768
-  **Real-time Processing**: Watch folders and process instantly
-  **Concurrent Tasks**: Run multiple watchers simultaneously
-  **Modern UI**: Beautiful, transparent PyQt6 interface
-  **Startup Automation**: Run automatically on Windows startup
-  **Live Logging**: See everything happening in real-time
-  **Configs**: Export and save your configs
-  **Low Resources Usage**: Wont fry your CPU

## How To Use

### For Users
1. Download the [latest release](https://github.com/wyv9/fetchx/releases)
2. Enjoy!

> [!TIP]
> Set it to always run as administrator if it ever stop working while you're playing a game or something.
> 
> The .exe will create a config so put both in a folder and make a shortcut for the app if you want.

### Build It Yourself
1. Use: ```https://github.com/wyv9/fetchx.git``` to clone this repo
2. Install requirements: ```pip install -r requirements.txt```
3. Run it or use ```pyinstaller```
- **Used pyinstaller command for the latest release**:
```
pyinstaller --onefile --noconsole --add-data "assets;assets" FetchX_1.0.py --version-file v.txt --icon "src\assets\icon.ico"
```
 
## License
MIT License
 
<div align="center">


  
Made with love by wyv <3
</div>
