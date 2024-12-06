# Floating Shelf

Provides a floating shelf for your general use

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

## Different Maya Versions
On Windows, Maya saves prefs in `D:\Documents\maya\VERSION\prefs` by default. You can copy/paste `floating_sheves.json` to other versions to share your shelves between versions. You can also delete this file to reset your settings.

## Changelog

### 1.0.0
* Initial Commit