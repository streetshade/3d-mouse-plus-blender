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

## Viewport navigation (orbit / free fly)

Replaces Blender's default 3D mouse viewport navigation with a simpler, decoupled mapping.

Orbit mode (Blender's "Object" navigation mode):
- Push left/right: orbit left/right
- Push forward/back: orbit up/down
- Twist: roll the view clockwise/counter-clockwise (not around the object)
- Press down/lift up: zoom in/out
- Tilting the cap does nothing. By default only the strongest axis moves the view at a time.

Free fly mode is Blender's own "Fly" navigation mode.

Default buttons (rebind in Preferences > Keymap > 3D View, search "3DMousePlus"):
- Button 3: toggle orbit / free fly
- Button 4: center the selected object in the view
- Button 5 / 6: select next / previous object (by name, object mode)

On Blender 4.3+ with the 3Dconnexion driver, assign the "NDOF Button" command to each physical button in the driver settings first.
Speeds, axis inversion and options are in the addon preferences. If an axis moves the wrong way, enable "Show raw 3D mouse values" and use the invert options.

## Configuration

- All options are in the addon preferences panel in the settings.
- Moving objects relative to viewport axes can be disabled for individual axes (or entirely if all axes are unchecked)
![Settings](./settings.png)

## Known Issues
- Report issues [here](https://github.com/sjkillen/3d-mouse-plus-blender/issues)
- Addon Preferences for axis sensitivity and flipping are not used (but the NDOF settings should work)