# Floating Shelf

Provides a floating shelf that you can customize to your liking, similar to a Maya shelf

![image](https://github.com/user-attachments/assets/6597afff-1aa5-4d86-854e-d422ff4e1747)
![image](https://github.com/user-attachments/assets/59e0a9ee-7303-4bb3-93e9-f4b7514d66c1)

## Installation
On Windows, this goes in your `My Documents\maya\scripts\` folder

Create a folder named FloatingShelf and clone this repo into it, or download the repo and extract the files into it.

## Running the Script
Run this from the Maya script editor, or add it to a shelf as a python command, or a hotkey (recommended):
```py
from FloatingShelf import FloatingShelf
FloatingShelf.FloatingShelfUI()
```

### Hotkey
I bind it to F1, previously the 'Help' hotkey:
![image](https://github.com/user-attachments/assets/2edd10a8-35b5-42e7-93fe-4f86595dafa9)

> [!TIP]
> Every time I use the hotkey it toggles the menu

## Different Maya Versions
On Windows, Maya saves prefs in `D:\Documents\maya\VERSION\prefs` by default. You can copy/paste `floating_sheves.json` to other versions to share your shelves between versions. You can also delete this file to reset your settings.

## Changelog

### 1.0.0
* Initial Commit
