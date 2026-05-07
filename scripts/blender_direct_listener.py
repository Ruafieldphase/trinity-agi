"""
Blender Direct Listener for the AGI playground.

Run inside Blender with:
  blender.exe --python C:\\workspace\\agi\\scripts\\blender_direct_listener.py

It opens a local JSON-over-TCP bridge on 127.0.0.1:8008 and supports the
commands used by services.blender_bridge_service.BlenderBridgeService.
"""

from __future__ import annotations

import json
import math
import queue
import socket
import threading
import traceback
from pathlib import Path
from typing import Any

import bpy


HOST = "127.0.0.1"
PORT = 8008
TASKS: "queue.Queue[dict[str, Any]]" = queue.Queue()


def _ok(**extra: Any) -> dict[str, Any]:
    out = {"status": "success"}
    out.update(extra)
    return out


def _err(message: str, **extra: Any) -> dict[str, Any]:
    out = {"status": "error", "message": message}
    out.update(extra)
    return out


def _material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def _look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    dx = target[0] - obj.location.x
    dy = target[1] - obj.location.y
    dz = target[2] - obj.location.z
    direction = mathutils.Vector((dx, dy, dz))
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _clean_scene() -> dict[str, Any]:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    return _ok(message="Scene cleaned")


def _add_box(params: dict[str, Any]) -> dict[str, Any]:
    name = str(params.get("name") or "AGI_Box")
    size = tuple(params.get("size") or (1, 1, 1))
    location = tuple(params.get("location") or (0, 0, 0))
    rotation = tuple(params.get("rotation") or (0, 0, 0))

    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mat_name = params.get("material")
    if mat_name:
        obj.data.materials.append(_material(str(mat_name), (0.35, 0.55, 0.95, 1.0)))

    return _ok(message="Box added", object=name)


def _create_object(params: dict[str, Any]) -> dict[str, Any]:
    object_type = str(params.get("object_type") or params.get("type") or "cube").lower()
    name = str(params.get("name") or f"AGI_{object_type}")
    location = tuple(params.get("location") or (0, 0, 0))
    scale = tuple(params.get("scale") or (1, 1, 1))

    if object_type in {"sphere", "uv_sphere"}:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=location)
    elif object_type in {"plane"}:
        bpy.ops.mesh.primitive_plane_add(size=1, location=location)
    elif object_type in {"cylinder"}:
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=location)
    else:
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)

    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    return _ok(message="Object created", object=name)


def _scene_info() -> dict[str, Any]:
    return _ok(
        message="Scene info",
        objects=len(bpy.data.objects),
        meshes=len(bpy.data.meshes),
        materials=len(bpy.data.materials),
        object_names=[obj.name for obj in bpy.context.scene.objects][:80],
    )


def _set_atmospheric_mood(params: dict[str, Any]) -> dict[str, Any]:
    valence = float(params.get("valence", 0.5))
    arousal = float(params.get("arousal", 0.5))
    resonance = float(params.get("resonance", 0.5))
    world = bpy.context.scene.world or bpy.data.worlds.new("AGI_World")
    bpy.context.scene.world = world
    world.color = (
        max(0.02, min(1.0, 0.05 + valence * 0.20)),
        max(0.02, min(1.0, 0.05 + resonance * 0.22)),
        max(0.02, min(1.0, 0.08 + arousal * 0.25)),
    )
    return _ok(message="Mood updated", valence=valence, arousal=arousal, resonance=resonance)


def _move_agent(params: dict[str, Any]) -> dict[str, Any]:
    name = str(params.get("name") or "Rhythm_Agent")
    delta_location = tuple(params.get("delta_location") or (0, 0, 0))
    delta_rotation = tuple(params.get("delta_rotation") or (0, 0, 0))
    obj = bpy.data.objects.get(name)
    if obj is None:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(0, 0, 0.4))
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(_material("Rhythm_Agent_Mat", (0.1, 0.8, 0.7, 1.0)))
    obj.location.x += float(delta_location[0])
    obj.location.y += float(delta_location[1])
    obj.location.z += float(delta_location[2])
    obj.rotation_euler.x += float(delta_rotation[0])
    obj.rotation_euler.y += float(delta_rotation[1])
    obj.rotation_euler.z += float(delta_rotation[2])
    return _ok(message="Agent moved", location=list(obj.location), rotation=list(obj.rotation_euler))


def _create_world(params: dict[str, Any]) -> dict[str, Any]:
    complexity = max(3, min(120, int(params.get("complexity", 25))))
    seed = str(params.get("seed") or "field")
    _clean_scene()
    floor_mat = _material("Playground_Floor", (0.08, 0.09, 0.11, 1.0))
    node_mat = _material("Latent_Node", (0.28, 0.52, 1.0, 1.0))
    active_mat = _material("Active_Node", (1.0, 0.72, 0.22, 1.0))

    bpy.ops.mesh.primitive_plane_add(size=18, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "AGI_Playground_Field"
    floor.data.materials.append(floor_mat)

    for i in range(complexity):
        angle = i * 2.399963229728653
        radius = 0.35 + 0.13 * i
        z = 0.25 + (i % 7) * 0.08
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12 + (i % 5) * 0.02, location=(math.cos(angle) * radius, math.sin(angle) * radius, z))
        obj = bpy.context.object
        obj.name = f"{seed}_node_{i:03d}"
        obj.data.materials.append(active_mat if i % 8 == 0 else node_mat)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(0, 0, 0.4))
    agent = bpy.context.object
    agent.name = "Rhythm_Agent"
    agent.data.materials.append(_material("Rhythm_Agent_Mat", (0.1, 0.8, 0.7, 1.0)))
    return _ok(message="World created", complexity=complexity, seed=seed)


def _render(params: dict[str, Any]) -> dict[str, Any]:
    filepath = str(params.get("filepath") or "C:/workspace/agi/outputs/renders/blender_listener_render.png")
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    camera_location = tuple(params.get("camera_location") or (8, -8, 6))
    camera_look_at = tuple(params.get("camera_look_at") or (0, 0, 0))

    cam = bpy.data.objects.get("AGI_Camera")
    if cam is None:
        bpy.ops.object.camera_add(location=camera_location)
        cam = bpy.context.object
        cam.name = "AGI_Camera"
    cam.location = camera_location
    direction = mathutils.Vector(camera_look_at) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    return _ok(message="Rendered", filepath=filepath)


def _execute_python(params: dict[str, Any]) -> dict[str, Any]:
    code = str(params.get("code") or "")
    namespace = {"bpy": bpy, "math": math}
    exec(code, namespace, namespace)
    return _ok(message="Python executed")


def _handle(payload: dict[str, Any]) -> dict[str, Any]:
    command = str(payload.get("command") or payload.get("type") or "").strip()
    params = payload.get("params") if isinstance(payload.get("params"), dict) else payload

    if command == "ping":
        return _ok(message="Blender listener alive", port=PORT)
    if command == "clean_scene":
        return _clean_scene()
    if command == "add_box":
        return _add_box(params)
    if command == "create_object":
        return _create_object(params)
    if command == "get_scene_info":
        return _scene_info()
    if command == "set_atmospheric_mood":
        return _set_atmospheric_mood(params)
    if command == "move_agent":
        return _move_agent(params)
    if command == "create_world":
        return _create_world(params)
    if command in {"render_scene", "render_viewport"}:
        return _render(params)
    if command == "execute_python":
        return _execute_python(params)
    return _err(f"Unknown command: {command}")


def _pump_tasks() -> float:
    while True:
        try:
            task = TASKS.get_nowait()
        except queue.Empty:
            break

        try:
            task["response"] = _handle(task["payload"])
        except Exception as exc:
            task["response"] = _err(str(exc), traceback=traceback.format_exc())
        finally:
            task["event"].set()
    return 0.05


def _serve() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(8)
        print(f"[AGI_BLENDER_LISTENER] listening on {HOST}:{PORT}", flush=True)

        while True:
            conn, addr = server.accept()
            with conn:
                try:
                    raw = conn.recv(1024 * 1024)
                    payload = json.loads(raw.decode("utf-8"))
                    event = threading.Event()
                    task: dict[str, Any] = {"payload": payload, "event": event, "response": None}
                    TASKS.put(task)
                    if not event.wait(timeout=10.0):
                        response = _err("Timed out waiting for Blender main thread")
                    else:
                        response = task["response"]
                except Exception as exc:
                    response = _err(str(exc), traceback=traceback.format_exc())
                conn.sendall(json.dumps(response, ensure_ascii=False).encode("utf-8"))


def main() -> None:
    # mathutils is only available in Blender's Python runtime.
    global mathutils
    import mathutils  # type: ignore

    bpy.app.timers.register(_pump_tasks, persistent=True)
    thread = threading.Thread(target=_serve, name="AGIBlenderListener", daemon=True)
    thread.start()
    print("[AGI_BLENDER_LISTENER] ready", flush=True)


main()
