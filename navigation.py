# 3DMousePlus: A Blender Addon for transforming objects with a 3DConnexion mouse
# Copyright (C) 2021  Spencer Killen
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
Viewport navigation for a 3D mouse with a fixed, decoupled axis mapping.

Two modes, switched with a button on the device:

- Orbit (Blender's "Object" navigation mode): handled here.
    push left/right  -> orbit left/right around the view pivot
    lift/press       -> orbit up/down around the view pivot
    twist            -> roll the view clockwise/counter-clockwise (not around the object)
    push/pull        -> zoom in/out
  Tilting the cap is ignored.
- Free fly (Blender's "Fly" navigation mode): the event is passed through to
  Blender's own fly navigation.

The mode is stored in Preferences > Input > NDOF > Navigation Mode, so the
stock NDOF menu and this add-on always agree.
"""

import math

import bpy
from bpy.types import Context, Event, Operator
from mathutils import Quaternion, Vector

from .preferences import get_prefs

ORBIT_MODE = "OBJECT"
FLY_MODE = "FLY"

# Longest time step used for one motion event, so a stalled event queue
# can't produce a huge jump.
MAX_TIME_DELTA = 0.1


def _in_orbit_mode(context: Context) -> bool:
    return context.preferences.inputs.ndof_navigation_mode == ORBIT_MODE


def _dominant_only(values: list[float]) -> list[float]:
    "Keep only the strongest channel so crosstalk can't move other axes."
    strongest = max(range(len(values)), key=lambda i: abs(values[i]))
    return [v if i == strongest else 0.0 for i, v in enumerate(values)]


def orbit_step(rotation: Quaternion, yaw: float, pitch: float, roll: float, turntable: bool):
    """
    Rotate a view orientation (camera-to-world, as `RegionView3D.view_rotation`)
    around its pivot. Angles are in radians.
    """
    if yaw:
        if turntable:
            # Turn around the world Z axis, flipped when the view is upside down
            upside_down = (rotation @ Vector((0.0, 1.0, 0.0))).z < 0.0
            sign = -1.0 if upside_down else 1.0
            rotation = Quaternion((0.0, 0.0, 1.0), -yaw * sign) @ rotation
        else:
            rotation = rotation @ Quaternion((0.0, 1.0, 0.0), -yaw)
    if pitch:
        rotation = rotation @ Quaternion((1.0, 0.0, 0.0), pitch)
    if roll:
        rotation = rotation @ Quaternion((0.0, 0.0, 1.0), roll)
    return rotation.normalized()


class NDOFNavigate(Operator):
    "Orbit, roll and zoom the 3D viewport with the 3D mouse"
    bl_idname = "view3d.ndof_custom_navigate"
    bl_label = "3DMousePlus: Navigate"

    @classmethod
    def poll(cls, context: Context):
        return context.area is not None and context.area.type == "VIEW_3D" and context.region_data is not None

    def invoke(self, context: Context, event: Event):
        if event.type != "NDOF_MOTION":
            return {"CANCELLED"}
        if not _in_orbit_mode(context):
            return {"PASS_THROUGH"}

        rv3d = context.region_data
        # Leave camera views and axis-locked views to Blender's own handling
        if rv3d.view_perspective == "CAMERA" or rv3d.lock_rotation:
            return {"PASS_THROUGH"}

        prefs = get_prefs()
        motion = event.ndof_motion
        dt = min(motion.time_delta, MAX_TIME_DELTA)
        translation, rotation = motion.translation, motion.rotation

        side, lift, push = translation[0], translation[1], translation[2]
        twist = rotation[1]
        channels = [side, lift, push, twist]
        if prefs.nav_dominant_only:
            channels = _dominant_only(channels)
        side, lift, push, twist = channels

        if prefs.nav_debug:
            self.show_debug(context, translation, rotation, channels)

        sign = lambda inverted: -1.0 if inverted else 1.0
        yaw = side * sign(prefs.nav_invert_orbit_h) * prefs.nav_orbit_speed * dt
        pitch = lift * sign(prefs.nav_invert_orbit_v) * prefs.nav_orbit_speed * dt
        roll = -twist * sign(prefs.nav_invert_roll) * prefs.nav_roll_speed * dt
        zoom = push * sign(prefs.nav_invert_zoom) * prefs.nav_zoom_speed * dt

        if yaw or pitch or roll:
            rv3d.view_rotation = orbit_step(rv3d.view_rotation, yaw, pitch, roll, prefs.nav_turntable)
        if zoom:
            # Positive push zooms in, matching Blender's own Object mode
            rv3d.view_distance = max(1e-4, rv3d.view_distance * math.exp(-zoom))

        context.area.tag_redraw()
        return {"FINISHED"}

    @staticmethod
    def show_debug(context: Context, translation, rotation, used):
        text = "NDOF  t=({:+.2f} {:+.2f} {:+.2f})  r=({:+.2f} {:+.2f} {:+.2f})  used: side {:+.2f} lift {:+.2f} push {:+.2f} twist {:+.2f}".format(
            *translation, *rotation, *used
        )
        context.workspace.status_text_set(text)


class NDOFToggleMode(Operator):
    "Switch the 3D mouse between orbit and free fly navigation"
    bl_idname = "view3d.ndof_custom_toggle_mode"
    bl_label = "3DMousePlus: Toggle Orbit / Free Fly"

    @classmethod
    def poll(cls, context: Context):
        return context.area is not None and context.area.type == "VIEW_3D"

    def execute(self, context: Context):
        inputs = context.preferences.inputs
        if _in_orbit_mode(context):
            inputs.ndof_navigation_mode = FLY_MODE
            self.report({"INFO"}, "3D mouse: free fly")
        else:
            inputs.ndof_navigation_mode = ORBIT_MODE
            self.report({"INFO"}, "3D mouse: orbit object")
            if get_prefs().nav_center_on_orbit and context.selected_objects:
                bpy.ops.view3d.view_selected(use_all_regions=False)
        return {"FINISHED"}


class NDOFCenterObject(Operator):
    "Center the selected object in the view"
    bl_idname = "view3d.ndof_custom_center"
    bl_label = "3DMousePlus: Center Object in View"

    @classmethod
    def poll(cls, context: Context):
        return context.area is not None and context.area.type == "VIEW_3D"

    def execute(self, context: Context):
        if not context.selected_objects:
            self.report({"WARNING"}, "No object selected")
            return {"CANCELLED"}
        return bpy.ops.view3d.view_selected(use_all_regions=False)


class NDOFCycleObject(Operator):
    "Select the next or previous object (by name)"
    bl_idname = "view3d.ndof_custom_cycle_object"
    bl_label = "3DMousePlus: Cycle Objects"

    step: bpy.props.IntProperty(name="Step", default=1, options={"SKIP_SAVE"})

    @classmethod
    def poll(cls, context: Context):
        return context.area is not None and context.area.type == "VIEW_3D" and context.mode == "OBJECT"

    def execute(self, context: Context):
        view_layer = context.view_layer
        objects = sorted(
            (o for o in view_layer.objects if o.visible_get() and not o.hide_select),
            key=lambda o: o.name.lower(),
        )
        if not objects:
            self.report({"WARNING"}, "No selectable objects")
            return {"CANCELLED"}

        active = view_layer.objects.active
        if active in objects:
            target = objects[(objects.index(active) + self.step) % len(objects)]
        else:
            target = objects[0 if self.step > 0 else -1]

        for obj in context.selected_objects:
            obj.select_set(False)
        target.select_set(True)
        view_layer.objects.active = target
        self.report({"INFO"}, f"Selected: {target.name}")

        if get_prefs().nav_frame_on_cycle:
            bpy.ops.view3d.view_selected(use_all_regions=False)
        return {"FINISHED"}


# Default buttons. Rebind in Preferences > Keymap > 3D View (search "3DMousePlus").
# On Blender 4.3+ with 3DxWare, each physical button must first be assigned the
# "NDOF Button" command in the 3Dconnexion driver settings.
addon_keymaps = []


def register():
    addon_kc = bpy.context.window_manager.keyconfigs.addon
    if addon_kc is None:
        return
    km = addon_kc.keymaps.new(name="3D View", space_type="VIEW_3D")

    items = [
        km.keymap_items.new(NDOFNavigate.bl_idname, type="NDOF_MOTION", value="ANY"),
        km.keymap_items.new(NDOFToggleMode.bl_idname, type="NDOF_BUTTON_3", value="PRESS"),
        km.keymap_items.new(NDOFCenterObject.bl_idname, type="NDOF_BUTTON_4", value="PRESS"),
    ]
    for button, step in (("NDOF_BUTTON_5", 1), ("NDOF_BUTTON_6", -1)):
        kmi = km.keymap_items.new(NDOFCycleObject.bl_idname, type=button, value="PRESS")
        kmi.properties.step = step
        items.append(kmi)
    addon_keymaps.append((km, items))


def unregister():
    for km, items in addon_keymaps:
        for kmi in items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()
