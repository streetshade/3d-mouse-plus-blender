Update: Blender 4.5 gives access to event data for 3D mouse. Additional drivers are no longer needed and this addon should work on any platform that supports a 3D mouse (E.g. Windows, Linux, MacOS)


# 3DMousePlus Blender Addon
![A demo](./demo.gif)

A Blender Addon for transforming objects with a 3D mouse.

Requires Blender 4.5 or newer.

Any 3D mouse that works in Blender should work with this addon.

## Installation
![How to install](./install.gif)

## Use
- Tool is activated by selecting an object an pushing a button on the 3D mouse
- Transforms occur in global space transformed by the view matrix (Moving your viewport will affect how objects are transformed)
- Use object transform locks to limit to just rotations or translations
- Pressing the space bar while using the tool will toggle "bend mode" (useful for armatures)
- Use ESC, Enter, and left/right mouse buttons to exit transform mode
- Tested only in object and pose mode.

## Configuration

- All options are in the addon preferences panel in the settings.
- Moving objects relative to viewport axes can be disabled for individual axes (or entirely if all axes are unchecked)
![Settings](./settings.png)

## Known Issues
- Report issues [here](https://github.com/sjkillen/3d-mouse-plus-blender/issues)
- Addon Preferences for axis sensitivity and flipping are not used (but the NDOF settings should work)