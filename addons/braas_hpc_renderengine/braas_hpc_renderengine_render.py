#####################################################################################################################
# Copyright(C) 2011-2025 IT4Innovations National Supercomputing Center, VSB - Technical University of Ostrava
#
# This program is free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#####################################################################################################################

#####################################################################################################################
# Based on https://github.com/GPUOpen-LibrariesAndSDKs/RadeonProRenderBlenderAddon.git
#####################################################################################################################

import bpy
import time

import textwrap
import weakref
import threading

import numpy as np
import math

import gpu

from dataclasses import dataclass

from mathutils import Matrix

from . import braas_hpc_renderengine_pref
import braas_hpc_renderengine_dll

#####################################################################################################################

class BRaaSHPCShowPopupErrorMessage(bpy.types.Operator):
    """Show Popup Error Message"""
    bl_idname = "braas_hpc_renderengine.error_message"
    bl_label = "Error Message"
    
    message: bpy.props.StringProperty(
        name="Message",
        description="The message to display",
        default='An error has occurred'
    ) # type: ignore

    def execute(self, context):
        self.report({'ERROR'}, self.message)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
#####################################################################################################################    
class BRaaSHPCServerSettings(bpy.types.PropertyGroup):

    braas_hpc_renderengine_port: bpy.props.IntProperty(
        name="Port",
        min=0,
        max=65565,
        default=7000
    ) # type: ignore

    braas_hpc_renderengine_server_name: bpy.props.StringProperty(
        name="Server",
        default="localhost"
    ) # type: ignore
        
    width: bpy.props.IntProperty(
        name="Width",
        default=0
    ) # type: ignore

    height: bpy.props.IntProperty(
        name="Height",
        default=0
    ) # type: ignore

    step_samples: bpy.props.IntProperty(
        name="Step Samples",
        min=0,
        max=100,
        default=1
    ) # type: ignore

    timesteps: bpy.props.IntProperty(
        name="Time Steps",
        min=1,
        max=100,
        default=1
    ) # type: ignore

    # mat_volume: bpy.props.PointerProperty(
    #     type=bpy.types.Material
    # ) # type: ignore

    command_script: bpy.props.PointerProperty(
        type=bpy.types.Text,
        name="Command Script"
    ) # type: ignore    

class BRaaSHPCRenderSettings(bpy.types.PropertyGroup):
    server_settings: bpy.props.PointerProperty(
        type=BRaaSHPCServerSettings
        ) # type: ignore

class BRaaSHPCData:
    def __init__(self):
        self.braas_hpc_renderengine_context = None
        self.braas_hpc_renderengine_process = None
        self.braas_hpc_renderengine_tunnel = None
        self.braas_hpc_renderengine_engine = None
        #self.is_rendered = False

#####################################################################################################################
# class BRaaSHPCDataRender:
#     def __init__(self):
#         self.colorMapCount = 128
#         self.colorMap = np.zeros((self.colorMapCount * 4), dtype=np.float32)
#         self.domain = np.zeros((2), dtype=np.float32)
#         self.baseDensity = np.zeros((1), dtype=np.float32)          

class BRaaSHPCContext:
    channels = 4
    send_cam_data_result = -1

    def __init__(self):
        self.server = None
        self.port = None
        #self.port_data = None
        self.width = None
        self.height = None
        self.step_samples = None
        #self.filename = None

        self.client_started = False

        #self.is_rendered = False
        #self.data = None
        # self.data_right = None

        self.braas_hpc_renderengine_data_previous = ""

    def init(self, context, server, port, width, height, step_samples):

        self.server = server
        self.port = port
        #self.port_data = port_data
        self.width = width
        self.height = height
        self.step_samples = step_samples
        #self.filename = filename

        #self.data = np.empty((height, width, self.channels), dtype=np.uint8)
        # self.data_right = np.empty((height, width, self.channels), dtype=np.uint8)

        print(self.server.encode(), self.port, self.width,
              self.height, self.step_samples)

    def client_init(self):
        braas_hpc_renderengine_dll.enable_gpujpeg(braas_hpc_renderengine_pref.preferences().braas_hpc_renderengine_use_gpujpeg)
        braas_hpc_renderengine_dll.set_pixsize(16) # 16 for half-float RGBA

        braas_hpc_renderengine_dll.client_init(self.server.encode(), self.port, #_cam, self.port_data,
                                      self.width, self.height) #, self.step_samples, self.filename.encode()

        self.g_width = self.width
        self.g_height = self.height
        self.client_started = True

        #check_gl_error()

    def client_close_connection(self):
        braas_hpc_renderengine_dll.reset()
        braas_hpc_renderengine_dll.client_close_connection()
        self.client_started = False

    def render(self, restart=False, tile=None):
        # cam
        if bpy.context.scene.braas_hpc_renderengine.server_settings.timesteps > 1:
            braas_hpc_renderengine_dll.set_timestep(bpy.context.scene.frame_current % bpy.context.scene.braas_hpc_renderengine.server_settings.timesteps)

        braas_hpc_renderengine_dll.send_cam_data()

        if braas_hpc_renderengine_dll.com_error() == 1:
            raise Exception("TCP error")

        # volume       
        #braas_hpc_renderengine_data = BRaaSHPCDataRender()
        #braas_hpc_renderengine_data_size = int(129 * 4 * 4)

        braas_hpc_renderengine_data = ""

        # material = bpy.context.scene.braas_hpc_renderengine.server_settings.mat_volume
        command_script = bpy.context.scene.braas_hpc_renderengine.server_settings.command_script

        if command_script:
            # try:
            #     from braas_hpc_xmlmaterial import braas_hpc_xmlmaterial_convert

            #     #material = bpy.data.materials["Material.001"]
            #     #active_node = material.node_tree.nodes.active
            #     #braas_hpc_renderengine_data = braas_hpc_xmlmaterial_convert.export_node(material, active_node)
            #     braas_hpc_renderengine_data = braas_hpc_xmlmaterial_convert.export_shader(material, material.node_tree)                
            # except:
            #     pass

            braas_hpc_renderengine_data = command_script.as_string()

            # node_color_ramp = None
            # node_float_curve = None

            # ############### Color Ramp ##############
            # if 'Color Ramp' in mat.node_tree.nodes:
            #     node_color_ramp = mat.node_tree.nodes['Color Ramp']

            # if 'Float Curve' in mat.node_tree.nodes:
            #     node_float_curve = mat.node_tree.nodes['Float Curve']
            #     curve_map = node_float_curve.mapping.curves[0]
            
            # for v in range(braas_hpc_renderengine_data.colorMapCount):
            #     color_rgba = (1.0,0.0,0.0,1.0)
            #     density = 1.0

            #     if node_color_ramp:
            #         color_rgba = node_color_ramp.color_ramp.evaluate(float(v) / float(braas_hpc_renderengine_data.colorMapCount))
            #         density = color_rgba[3]
                
            #     if node_float_curve:
            #         density = node_float_curve.mapping.evaluate(curve_map, float(v) / float(braas_hpc_renderengine_data.colorMapCount))

            #     braas_hpc_renderengine_data.colorMap[0 + v * 4] = color_rgba[0]
            #     braas_hpc_renderengine_data.colorMap[1 + v * 4] = color_rgba[1]
            #     braas_hpc_renderengine_data.colorMap[2 + v * 4] = color_rgba[2]
            #     braas_hpc_renderengine_data.colorMap[3 + v * 4] = density

            # ############### Min/Max ##############
            # domain = [float(0.0), float(1.0)]

            # if 'Map Range' in mat.node_tree.nodes:
            #     domain[0] = mat.node_tree.nodes["Map Range"].inputs[1].default_value
            #     domain[1] = mat.node_tree.nodes["Map Range"].inputs[2].default_value
            # else:            
            #     if 'DomainX' in mat.node_tree.nodes:
            #         domain[0] = mat.node_tree.nodes['DomainX'].outputs[0].default_value
            #     if 'DomainY' in mat.node_tree.nodes:
            #         domain[1] = mat.node_tree.nodes['DomainY'].outputs[0].default_value                
            
            # braas_hpc_renderengine_data.domain[0] = domain[0]
            # braas_hpc_renderengine_data.domain[1] = domain[1]

            # baseDensity = float(1.0)
            # if 'Base Density' in mat.node_tree.nodes:
            #     baseDensity = mat.node_tree.nodes['Base Density'].outputs[0].default_value
            # elif 'Math' in mat.node_tree.nodes:
            #     baseDensity = mat.node_tree.nodes["Math"].inputs[1].default_value

            # braas_hpc_renderengine_data.baseDensity[0] = baseDensity

            # # if bpy.context.scene.braas_hpc_renderengine.server_settings.save_to_file == True:
            # #     braas_hpc_renderengine_data[3 + 128 * 4] = 1
            # # else:
            # #     braas_hpc_renderengine_data[3 + 128 * 4] = 0
        
        #braas_hpc_renderengine_dll.send_braas_hpc_renderengine_data_render(braas_hpc_renderengine_data.colorMap.ctypes.data, braas_hpc_renderengine_data.colorMapCount, braas_hpc_renderengine_data.domain.ctypes.data, braas_hpc_renderengine_data.baseDensity.ctypes.data)
        if self.braas_hpc_renderengine_data_previous == braas_hpc_renderengine_data:
            bdata="".encode('utf-8')
        else:
            bdata=braas_hpc_renderengine_data.encode('utf-8')
            self.braas_hpc_renderengine_data_previous = braas_hpc_renderengine_data
            
        braas_hpc_renderengine_dll.send_braas_hpc_renderengine_data_render(bdata, len(bdata))

        # image
        braas_hpc_renderengine_dll.recv_pixels_data()

        if braas_hpc_renderengine_dll.com_error() == 1:
            raise Exception("TCP error")        

        return 1

    def set_camera(self, camera_data):
        transformL = np.array(camera_data.transform, dtype=np.float32)

        braas_hpc_renderengine_dll.set_camera(transformL.ctypes.data,
                                     camera_data.focal_length,
                                     camera_data.clip_plane[0],
                                     camera_data.clip_plane[1],
                                     camera_data.sensor_size[0],
                                     camera_data.sensor_size[1],
                                     camera_data.sensor_fit,
                                     camera_data.view_camera_zoom,
                                     camera_data.view_camera_offset[0],
                                     camera_data.view_camera_offset[1],
                                     camera_data.use_view_camera,
                                     camera_data.shift_x,
                                     camera_data.shift_y,
                                     camera_data.view_perspective)
        
    def set_frame(self, frame):
        braas_hpc_renderengine_dll.set_frame(frame)        
        

    # def get_image(self):
    #     braas_hpc_renderengine_dll.get_pixels(ctypes.c_void_p(self.data.ctypes.data))
    #     return self.data
    
    def draw_texture(self):
        braas_hpc_renderengine_dll.draw_texture()

    def get_current_samples(self):
        return braas_hpc_renderengine_dll.get_current_samples()
    
    def get_fps(self):
        return braas_hpc_renderengine_dll.get_remote_fps(), braas_hpc_renderengine_dll.get_local_fps()    
    
    def get_texture_id(self):
        return braas_hpc_renderengine_dll.get_texture_id()

    def resize(self, width, height):
        self.width = width
        self.height = height
        braas_hpc_renderengine_dll.resize(width, height)
        #braas_hpc_renderengine_dll.set_resolution(width, height)        

#####################################################################################################################
MAX_ORTHO_DEPTH = 200.0

@dataclass(init=False, eq=True)
class CameraData:
    """ Comparable dataclass which holds all camera settings """

    transform: tuple = None  # void *camera_object,
    focal_length: float = None  # float lens,
    clip_plane: (float, float) = None  # float nearclip, float farclip,
    # float sensor_width, float sensor_height,
    sensor_size: (float, float) = None
    sensor_fit: int = None  # int sensor_fit,
    view_camera_zoom: float = None  # float view_camera_zoom,
    # float view_camera_offset0, float view_camera_offset1,
    view_camera_offset: (float, float) = None
    use_view_camera: int = None  # int use_view_camera
    shift_x: float = None
    shift_y: float = None
    quat: tuple = None
    pos: tuple = None
    view_perspective: int = None

    @staticmethod
    def get_view_matrix(context):
        # R = Matrix.Rotation(context.scene.braas_hpc_renderengine.server_settings.cam_rotation_X, 4, 'X')
        # vmat = R @ context.region_data.view_matrix.inverted()
        # return vmat
        return context.region_data.view_matrix.inverted()

    @staticmethod
    def init_from_camera(camera: bpy.types.Camera, transform, ratio, border=((0, 0), (1, 1))):
        """ Returns CameraData from bpy.types.Camera """

        # pos, size = border

        data = CameraData()
        data.clip_plane = (camera.clip_start, camera.clip_end)
        data.transform = tuple(transform)
        data.use_view_camera = 1

        data.shift_x = camera.shift_x
        data.shift_y = camera.shift_y

        data.quat = tuple(transform.to_quaternion())
        data.pos = tuple(transform.to_translation())

        if camera.sensor_fit == 'VERTICAL':
            # data.lens_shift = (camera.shift_x / ratio, camera.shift_y)
            data.sensor_fit = 2
        elif camera.sensor_fit == 'HORIZONTAL':
            # data.lens_shift = (camera.shift_x, camera.shift_y * ratio)
            data.sensor_fit = 1
        elif camera.sensor_fit == 'AUTO':
            # data.lens_shift = (camera.shift_x, camera.shift_y * ratio) if ratio > 1.0 else \
            #     (camera.shift_x / ratio, camera.shift_y)
            data.sensor_fit = 0
        else:
            raise ValueError("Incorrect camera.sensor_fit value",
                             camera, camera.sensor_fit)

        # data.lens_shift = tuple(data.lens_shift[i] / size[i] + (pos[i] + size[i] * 0.5 - 0.5) / size[i] for i in (0, 1))

        if camera.type == 'PERSP':
            # data.mode = pyrpr.CAMERA_MODE_PERSPECTIVE
            # data.focal_length = camera.lens
            # data.sensor_fit = camera.sensor_fit
            data.sensor_size = (camera.sensor_width, camera.sensor_height)
            # if camera.sensor_fit == 'VERTICAL':
            #     data.sensor_size = (camera.sensor_height * ratio, camera.sensor_height)
            # elif camera.sensor_fit == 'HORIZONTAL':
            #     data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio)
            # else:
            #     data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio) if ratio > 1.0 else \
            #                        (camera.sensor_width * ratio, camera.sensor_width)

            # data.sensor_size = tuple(data.sensor_size[i] * size[i] for i in (0, 1))

            # data.fov = 2.0 * math.atan(0.5 * camera.sensor_width / camera.lens / ratio )
            # data.focal_length = math.degrees(2.0 * math.atan(0.5 * camera.sensor_width / camera.lens / ratio ))
            # fov = 2.0 * math.atan(0.5 * camera.sensor_width / camera.lens)
            # data.focal_length = math.degrees(fov)

            VIEWPORT_SENSOR_SIZE = 72.0
            fov = 2.0 * math.atan(0.5 * VIEWPORT_SENSOR_SIZE / camera.lens / ratio)
            #fov = 2 * math.atan(math.tan(math.radians(camera.angle / 2)) / ratio)
            data.focal_length = fov #math.degrees(fov)

            data.view_perspective = 0

        elif camera.type == 'ORTHO':
            data.sensor_size = (camera.sensor_width, camera.sensor_height)

            #data.mode = pyrpr.CAMERA_MODE_ORTHOGRAPHIC
            # if camera.sensor_fit == 'VERTICAL':
            #     data.ortho_size = (camera.ortho_scale * ratio, camera.ortho_scale)
            # elif camera.sensor_fit == 'HORIZONTAL':
            #     data.ortho_size = (camera.ortho_scale, camera.ortho_scale / ratio)
            # else:
            #     data.ortho_size = (camera.ortho_scale, camera.ortho_scale / ratio) if ratio > 1.0 else \
            #                       (camera.ortho_scale * ratio, camera.ortho_scale)

            # data.ortho_size = tuple(data.ortho_size[i] * size[i] for i in (0, 1))
            # data.clip_plane = (camera.clip_start, min(camera.clip_end, MAX_ORTHO_DEPTH + camera.clip_start))
            zoom = camera.data.ortho_scale
            data.focal_length = 2.0*zoom/ratio

            data.view_perspective = 1

        # elif camera.type == 'PANO':
        #     # TODO: Recheck parameters for PANO camera
        #     #data.mode = pyrpr.CAMERA_MODE_LATITUDE_LONGITUDE_360
        #     data.focal_length = camera.lens
        #     if camera.sensor_fit == 'VERTICAL':
        #         data.sensor_size = (camera.sensor_height * ratio, camera.sensor_height)
        #     elif camera.sensor_fit == 'HORIZONTAL':
        #         data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio)
        #     else:
        #         data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio) if ratio > 1.0 else \
        #                            (camera.sensor_width * ratio, camera.sensor_width)

        #     data.sensor_size = tuple(data.sensor_size[i] * size[i] for i in (0, 1))

        else:
            raise ValueError("Incorrect camera.type value",
                             camera, camera.type)

        return data

    @staticmethod
    def init_from_context(context: bpy.types.Context):
        """ Returns CameraData from bpy.types.Context """

        # this constant was found experimentally, didn't find such option in
        VIEWPORT_SENSOR_SIZE = 72.0
        # context.space_data or context.region_data

        if context.region.width < context.region.height:
            min_wh = context.region.width
        else:
            min_wh = context.region.height

        if context.region.width > context.region.height:
            max_wh = context.region.width
        else:
            max_wh = context.region.height

        ratio = max_wh / min_wh
        if context.region_data.view_perspective == 'PERSP':
            data = CameraData()
            # data.mode = pyrpr.CAMERA_MODE_PERSPECTIVE
            data.clip_plane = (context.space_data.clip_start,
                               context.space_data.clip_end)
            # data.lens_shift = (0.0, 0.0)
            # data.sensor_size = (VIEWPORT_SENSOR_SIZE, VIEWPORT_SENSOR_SIZE / ratio) if ratio > 1.0 else \
            #                    (VIEWPORT_SENSOR_SIZE * ratio, VIEWPORT_SENSOR_SIZE)
            # data.fov = 2.0 * math.atan(0.5 * VIEWPORT_SENSOR_SIZE / context.space_data.lens / ratio

            fov = 2.0 * math.atan(0.5 * VIEWPORT_SENSOR_SIZE / context.space_data.lens / ratio)
            #fov = 2 * math.atan(16 / context.space_data.lens / ratio)
            data.focal_length = fov #math.degrees(fov)

            # context.region_data.view_matrix.inverted()
            vmat = CameraData.get_view_matrix(context)
            data.transform = tuple(vmat)
            # data.focal_length = context.space_data.lens
            data.use_view_camera = 0
            data.sensor_size = (VIEWPORT_SENSOR_SIZE, VIEWPORT_SENSOR_SIZE)
            data.view_camera_offset = (0, 0)
            data.view_camera_zoom = 1.0
            data.sensor_fit = 0
            data.shift_x = 0
            data.shift_y = 0

            data.quat = tuple(vmat.to_quaternion())
            data.pos = tuple(vmat.to_translation())

            data.view_perspective = 0

        elif context.region_data.view_perspective == 'ORTHO':
            data = CameraData()
            #data.mode = pyrpr.CAMERA_MODE_ORTHOGRAPHIC
            #ortho_size = context.region_data.view_distance * VIEWPORT_SENSOR_SIZE / context.space_data.lens
            #data.lens_shift = (0.0, 0.0)
            ortho_depth = min(context.space_data.clip_end, MAX_ORTHO_DEPTH)
            data.clip_plane = (-ortho_depth * 0.5, ortho_depth * 0.5)
            #data.ortho_size = (ortho_size, ortho_size / ratio) if ratio > 1.0 else \
            #                  (ortho_size * ratio, ortho_size)

            #fov = 2.0 * math.atan(0.5 * VIEWPORT_SENSOR_SIZE / context.space_data.lens / ratio)
            #data.focal_length = context.region_data.view_distance * (46 / context.space_data.lens) / (math.pi / 2) #TODO - Why?
            #zoom = 1.0275 * context.region_data.view_distance * 35 / context.space_data.lens

            ortho_scale = 2.0 * 0.5 * VIEWPORT_SENSOR_SIZE * context.region_data.view_distance / context.space_data.lens / ratio
            #data.focal_length = fov #2.0*zoom/ratio
            #ortho_scale = context.region_data.view_distance * 0.5 * VIEWPORT_SENSOR_SIZE / context.space_data.lens
            data.focal_length = ortho_scale

            #data.transform = tuple(context.region_data.view_matrix.inverted())
            #vmat = context.region_data.view_matrix.inverted()
            vmat = CameraData.get_view_matrix(context)
            data.transform = tuple(vmat)
            # data.focal_length = context.space_data.lens
            data.use_view_camera = 0
            data.sensor_size = (VIEWPORT_SENSOR_SIZE, VIEWPORT_SENSOR_SIZE)
            data.view_camera_offset = (0, 0)
            data.view_camera_zoom = 1.0
            data.sensor_fit = 0
            data.shift_x = 0
            data.shift_y = 0

            data.quat = tuple(vmat.to_quaternion())
            data.pos = tuple(vmat.to_translation())


            data.view_perspective = 1

        elif context.region_data.view_perspective == 'CAMERA':
            camera_obj = context.space_data.camera
            data = CameraData.init_from_camera(
                camera_obj.data, CameraData.get_view_matrix(context), ratio)
            # data = CameraData()
            # data.clip_plane = (camera_obj.data.clip_start, camera_obj.data.clip_end)
            # data.transform = tuple(context.region_data.view_matrix.inverted())
            # data.fov = 2.0 * atan(0.5 * camera_obj.data.sensor_width / camera_obj.data.lens / ratio )
            # data.transform = tuple(camera_obj.matrix_world) #tuple(context.region_data.view_matrix.inverted())

            # # This formula was taken from previous plugin with corresponded comment
            # # See blender/intern/cycles/blender/blender_camera.cpp:blender_camera_from_view (look for 1.41421f)
            # zoom = 4.0 / (2.0 ** 0.5 + context.region_data.view_camera_zoom / 50.0) ** 2
            data.view_camera_zoom = context.region_data.view_camera_zoom

            # # Updating lens_shift due to viewport zoom and view_camera_offset
            # # view_camera_offset should be multiplied by 2
            # data.lens_shift = ((data.lens_shift[0] + context.region_data.view_camera_offset[0] * 2) / zoom,
            #                    (data.lens_shift[1] + context.region_data.view_camera_offset[1] * 2) / zoom)
            data.view_camera_offset = (
                context.region_data.view_camera_offset[0], context.region_data.view_camera_offset[1])
            # if data.mode == pyrpr.CAMERA_MODE_ORTHOGRAPHIC:
            #     data.ortho_size = (data.ortho_size[0] * zoom, data.ortho_size[1] * zoom)
            # else:
            #     data.sensor_size = (data.sensor_size[0] * zoom, data.sensor_size[1] * zoom)

        else:
            raise ValueError("Incorrect view_perspective value",
                             context.region_data.view_perspective)

        return data

#####################################################################################################################


@dataclass(init=False, eq=True)
class ViewportSettings:
    """
    Comparable dataclass which holds render settings for ViewportEngine:
    - camera viewport settings
    - render resolution
    - screen resolution
    - render border
    """

    camera_data: CameraData
    # camera_dataR: CameraData
    width: int
    height: int
    screen_width: int
    screen_height: int
    border: tuple

    def __init__(self, context: bpy.types.Context):
        """Initializes settings from Blender's context"""
        # if braas_hpc_renderengine_dll.get_renderengine_type() == 1:
        #     self.camera_data,self.camera_dataR = CameraData.init_from_context_openvr(context)
        #     self.screen_height = context.scene.openvr_user_prop.openVrGlRenderer.getHeight()
        #     self.screen_width = context.scene.openvr_user_prop.openVrGlRenderer.getWidth()
        # else:
        self.camera_data = CameraData.init_from_context(context)
        self.screen_width, self.screen_height = context.region.width, context.region.height

        scene = context.scene

        # getting render border
        x1, y1 = 0, 0
        x2, y2 = self.screen_width, self.screen_height

        # getting render resolution and render border
        self.width, self.height = x2 - x1, y2 - y1
        self.border = (x1, y1), (self.width, self.height)

#####################################################################################################################


class Engine:
    """ This is the basic Engine class """

    def __init__(self, braas_hpc_renderengine_engine):
        self.braas_hpc_renderengine_engine = weakref.proxy(braas_hpc_renderengine_engine)
        self.braas_hpc_renderengine_context = BRaaSHPCContext()
        bpy.context.scene.braas_hpc_renderengine_data.braas_hpc_renderengine_context = self.braas_hpc_renderengine_context
        bpy.context.scene.braas_hpc_renderengine_data.braas_hpc_renderengine_engine = self.braas_hpc_renderengine_engine

#####################################################################################################################


class ViewportEngine(Engine):
    """ Viewport render engine """

    def __init__(self, braas_hpc_renderengine_engine):
        super().__init__(braas_hpc_renderengine_engine)

        #self.gl_texture = None #GLTexture = None
        self.viewport_settings: ViewportSettings = None

        self.sync_render_thread: threading.Thread = None
        self.restart_render_event = threading.Event()
        self.render_lock = threading.Lock()
        self.render_event = threading.Event()
        #self.resolve_lock = threading.Lock()

        self.is_finished = True
        self.is_synced = False
        self.is_rendered = False
        # self.is_denoised = False
        self.is_resized = False

        # self.render_iterations = 0
        # self.render_time = 0

        # g_viewport_engine = self
        # self.render_callback = render_callback_type(self.render_callback)

    def start_render(self):
        print("start_render")
        self.is_finished = False

        #print('Start _do_sync_render')
        self.restart_render_event.clear()
        self.render_event.clear()
        self.sync_render_thread = threading.Thread(target=self._do_sync_render)
        self.sync_render_thread.start()
        #print('Finish sync')   

    def stop_render(self):
        print("stop_render")
        self.is_finished = True

        self.restart_render_event.set()
        self.sync_render_thread.join()        

        self.braas_hpc_renderengine_context.client_close_connection()

        #self.braas_hpc_renderengine_context = None
        #self.image_filter = None
        #pass

    def _do_sync_render(self):
        """
        Thread function for self.sync_render_thread. It always run during viewport render.
        If it doesn't render it waits for self.restart_render_event
        """

        def notify_status(info, status):
            """ Display export progress status """
            wrap_info = textwrap.fill(info, 120)
            self.braas_hpc_renderengine_engine.update_stats(status, wrap_info)
            # log(status, wrap_info)

            # requesting blender to call draw()
            self.braas_hpc_renderengine_engine.tag_redraw()

        class FinishRender(Exception):
            pass

        # print('Start _do_sync_render')
        # self.braas_hpc_renderengine_context.client_init()

        try:
            # SYNCING OBJECTS AND INSTANCES
            notify_status("Starting...", "Sync")
            time_begin = time.perf_counter()

            self.is_synced = True

            # RENDERING
            notify_status("Starting...", "Render")

            # Infinite cycle, which starts when scene has to be re-rendered.
            # It waits for restart_render_event be enabled.
            # Exit from this cycle is implemented through raising FinishRender
            # when self.is_finished be enabled from main thread.
            #self.restart_render_event.clear()
            self.restart_render_event.wait()

            while True:
                #self.restart_render_event.wait()

                if self.is_finished:
                    raise FinishRender

                # preparations to start rendering
                #iteration = 0
                time_begin = 0.0
                # if is_adaptive:
                #     all_pixels = active_pixels = self.braas_hpc_renderengine_context.width * self.braas_hpc_renderengine_context.height
                # is_last_iteration = False

                # this cycle renders each iteration
                #while True:
                    # if self.is_finished:
                    #     raise FinishRender

                    # with self.render_lock:
                    #     if self.restart_render_event.is_set():
                    #         # clears restart_render_event, prepares to start rendering
                    #         self.restart_render_event.clear()
                    #         #iteration = 0
                    #         break

                    #     time_begin = time.perf_counter()

                    # rendering
                    # with self.render_lock:
                if self.restart_render_event.is_set():
                    self.restart_render_event.clear()
                    #         break

                    #self.braas_hpc_renderengine_context.render(restart=(iteration == 0))
                    
                    # if self.is_resized:
                    #     self.is_resized = False                    

                    
                with self.render_lock:
                    #start_render_time = time.perf_counter()
                    self.braas_hpc_renderengine_context.render()
                    #end_render_time = time.perf_counter() - start_render_time
                    #render_fps = 1.0 / end_render_time
                
                self.is_rendered = True
                self.is_resized = False

                current_samples = self.braas_hpc_renderengine_context.get_current_samples()

                self.render_event.set()

                time_render = time.perf_counter() - time_begin
                rfps, lfps = self.braas_hpc_renderengine_context.get_fps() #current_samples / time_render
                info_str = f"Time: {time_render:.1f} sec"\
                        f" | Samples: {current_samples}" \
                        f" | FPS (r): {rfps:.1f}" \
                        f" | FPS: {lfps:.1f}"
                #f" | FPS (p): {render_fps:.1f}"

                notify_status(info_str, "Render")

        except FinishRender:
            #print("Finish by user")
            pass

        except Exception as e:
            print(e)
            
        self.is_finished = True

        # notifying viewport about error
        #notify_status(f"{e}.\nPlease see logs for more details.", "ERROR")

        #bpy.ops.braas_hpc_renderengine.stop_process()
        #print('Finish _do_sync_render')        

    def sync(self, context, depsgraph):
        
        # if context.scene.braas_hpc_renderengine_data.braas_hpc_renderengine_process is None:
        #     message = "BRaaSHPC process is not started"
        #     bpy.ops.braas_hpc_renderengine.error_message('INVOKE_DEFAULT', message=message)
        #     raise Exception(message)
    
        print('Start sync')
        #bpy.ops.braas_hpc_renderengine.start_process()

        scene = depsgraph.scene
        view_layer = depsgraph.view_layer

        #scene.view_settings.view_transform = 'Raw'

        # getting initial render resolution
        # if scene.braas_hpc_renderengine.server_settings.use_viewport == True:
        viewport_settings = ViewportSettings(context)
        width, height = viewport_settings.width, viewport_settings.height
        if width * height == 0:
            # if width, height == 0, 0, then we set it to 1, 1 to be able to set AOVs
            width, height = 1, 1

        scene.braas_hpc_renderengine.server_settings.width = width
        scene.braas_hpc_renderengine.server_settings.height = height

        #pref = braas_hpc_renderengine_pref.preferences()

        # client_init(const char *server, int port_cam, int port_data, int w, int h, int step_samples)
        self.braas_hpc_renderengine_context.init(context, scene.braas_hpc_renderengine.server_settings.braas_hpc_renderengine_server_name,
                                  scene.braas_hpc_renderengine.server_settings.braas_hpc_renderengine_port,
                                  #scene.braas_hpc_renderengine.server_settings.braas_hpc_renderengine_port_data,
                                  scene.braas_hpc_renderengine.server_settings.width,
                                  scene.braas_hpc_renderengine.server_settings.height,
                                  scene.braas_hpc_renderengine.server_settings.step_samples
                                  ) #scene.braas_hpc_renderengine.server_settings.filename
        # if not self.braas_hpc_renderengine_context.gl_interop:
        #self.gl_texture = GLTexture(width, height)
        self.braas_hpc_renderengine_context.client_init()     
        #################################

        # reset scene
        # braas_hpc_renderengine_dll.reset()

        #import array
        #pixels = width * height * array.array('f', [0.1, 0.2, 0.1, 1.0])
        #pixels = gpu.types.Buffer('FLOAT', width * height * 4)

        # Generate texture
        #self.texture = gpu.types.GPUTexture((width, height), format='RGBA16F', data=pixels)

        self.start_render()

    def draw_texture_2d_raw(self, texture, position, width, height):
        import gpu
        from gpu_extras.batch import batch_for_shader

        # Custom shader that doesn't transform colors
        vertex_shader = '''
        uniform mat4 ModelViewProjectionMatrix;
        in vec2 pos;
        in vec2 texCoord;
        out vec2 texCoord_interp;
        
        void main() {
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
            texCoord_interp = texCoord;
        }
        '''
        
        fragment_shader = '''
        uniform sampler2D image;
        in vec2 texCoord_interp;
        out vec4 fragColor;
        
        void main() {
            fragColor = texture(image, texCoord_interp);
        }
        '''
        
        coords = ((0, 0), (1, 0), (1, 1), (0, 1))
        shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {"pos": coords, "texCoord": coords},
        )

        with gpu.matrix.push_pop():
            gpu.matrix.translate(position)
            gpu.matrix.scale((width, height))

            shader.bind()
            self.braas_hpc_renderengine_context.draw_texture()
            shader.uniform_int("image", 0)
            batch.draw(shader) 
        
    def draw_texture_2d(self, texture, position, width, height):
        import gpu
        from gpu_extras.batch import batch_for_shader

        coords = ((0, 0), (1, 0), (1, 1), (0, 1))

        shader = gpu.shader.from_builtin('IMAGE')
        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {"pos": coords, "texCoord": coords},
        )

        with gpu.matrix.push_pop():
            gpu.matrix.translate(position)
            gpu.matrix.scale((width, height))

            shader = gpu.shader.from_builtin('IMAGE')

            # if isinstance(texture, int):
            #     # Call the legacy bgl to not break the existing API
            #     import bgl
            #     bgl.glActiveTexture(bgl.GL_TEXTURE0)
            #     bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture)
            #     shader.uniform_int("image", 0)
            # else:
            #     shader.uniform_sampler("image", texture)            

            self.braas_hpc_renderengine_context.draw_texture()
            shader.uniform_int("image", 0)

            batch.draw(shader)        

    def draw(self, context):
        # log("Draw")

        if not self.is_synced or self.is_finished:
            return

        scene = context.scene

        #with self.render_lock:
        viewport_settings = ViewportSettings(context)

        if viewport_settings.width * viewport_settings.height == 0:
            return

        # or viewport_settings.camera_dataR is None:
        if viewport_settings.camera_data is None:
            return

        self.braas_hpc_renderengine_context.set_frame(context.scene.frame_current)
        
        if self.viewport_settings != viewport_settings:
            # viewport_settings.export_camera(self.braas_hpc_renderengine_context.scene.camera)
            # , viewport_settings.camera_dataR)            
            self.braas_hpc_renderengine_context.set_camera(viewport_settings.camera_data)
            self.viewport_settings = viewport_settings

            if self.braas_hpc_renderengine_context.width != viewport_settings.width \
                    or self.braas_hpc_renderengine_context.height != viewport_settings.height:

                resolution = (viewport_settings.width,
                                viewport_settings.height)
                
                #self.stop_render()
                with self.render_lock:
                    self.braas_hpc_renderengine_context.resize(*resolution)
                #self.is_rendered = False

                #self.restart_render_event.set()
                #return

                # if self.gl_texture:
                #     self.gl_texture = GLTexture(*resolution)

                self.is_resized = True

            # if braas_hpc_renderengine_dll.get_renderengine_type() != 2:
            #else:
            #self.restart_render_event.set()
            #return
            #self.is_rendered = False

        # if not self.is_rendered:
        #     return

        self.restart_render_event.set()
        
        #self.render_event.wait()

        if self.is_resized or not self.is_rendered:
            return              

        #context.scene.braas_hpc_renderengine_data.is_rendered = True       

        texture_id = self.braas_hpc_renderengine_context.get_texture_id()
        
        # present
        if True:
            gpu.state.blend_set('ALPHA_PREMULT')
            self.braas_hpc_renderengine_engine.bind_display_space_shader(scene)
            self.draw_texture_2d(texture_id, self.viewport_settings.border[0], self.viewport_settings.border[1][0], self.viewport_settings.border[1][1])        
            self.braas_hpc_renderengine_engine.unbind_display_space_shader()
            gpu.state.blend_set('NONE')
        else:
            # Draw the texture without color management
            gpu.state.blend_set('ALPHA_PREMULT')
            # Skip display space shader binding to avoid color management
            self.draw_texture_2d_raw(texture_id, self.viewport_settings.border[0], 
                                self.viewport_settings.border[1][0], self.viewport_settings.border[1][1])
            gpu.state.blend_set('NONE')            


        #self.render_event.clear()

        # check_gl_error()

#####################################################################################################################


class BRaaSHPCRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "BRAAS_HPC"
    bl_label = "BRaaS-HPC"
    bl_use_preview = False
    bl_use_shading_nodes_custom=False

    engine: Engine = None

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    # def __init__(self):
    #     self.engine = None

    #     dummy = gpu.types.GPUFrameBuffer()
    #     dummy.bind()  

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        if isinstance(self.engine, ViewportEngine):
            self.engine.stop_render()
            self.engine = None
        pass

    # final render
    def update(self, data, depsgraph):
        """ Called for final render """
        pass

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        pass

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph):
        if self.engine:
            return

        self.engine = ViewportEngine(self)
        self.engine.sync(context, depsgraph)

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        self.engine.draw(context)

    def update_render_passes(self, render_scene=None, render_layer=None):
        pass


class RenderButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)


class RENDER_PT_braas_hpc_renderengine_server(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Server"
    COMPAT_ENGINES = {'BRAAS_HPC'}

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        scene = context.scene
        server_settings = scene.braas_hpc_renderengine.server_settings

        #pref = braas_hpc_renderengine_pref.preferences()
        box = layout.box()
        box.label(text='TCP Server:')
        col = box.column()
        col.prop(server_settings, "braas_hpc_renderengine_server_name", text="Server")
        col.prop(server_settings, "braas_hpc_renderengine_port", text="Port")
        #col.prop(server_settings, "braas_hpc_renderengine_port_data", text="Port Data")                              

        box = layout.box()
        col = box.column()
        col.enabled = False
        col.prop(server_settings, "width", text="Width")
        col.prop(server_settings, "height", text="Height")
        #col.prop(server_settings, "step_samples", text="Step samples")

        box = layout.box()
        col = box.column()
        #col.prop(server_settings, "mat_volume", text="Material")  
        col.prop(server_settings, "command_script", text="Command Script")

        if not context.scene.braas_hpc_renderengine_data.braas_hpc_renderengine_context is None and context.scene.braas_hpc_renderengine_data.braas_hpc_renderengine_context.client_started == True:
            box = layout.box()
            col = box.column()

            col.operator("braas_hpc_renderengine.create_bbox")
            #col.operator("braas_hpc_renderengine.stop_process")
        
###################################################################################

# RenderEngines also need to tell UI Panels that they are compatible with.
# We recommend to enable all panels marked as BLENDER_RENDER, and then
# exclude any panels that are replaced by custom panels registered by the
# render engine, or that are not supported.


def get_panels():
    exclude_panels = {
        'VIEWLAYER_PT_filter',
        'VIEWLAYER_PT_layer_passes',
        'RENDER_PT_eevee_ambient_occlusion',
        'RENDER_PT_eevee_motion_blur',
        'RENDER_PT_eevee_next_motion_blur',
        'RENDER_PT_motion_blur_curve',
        'RENDER_PT_eevee_depth_of_field',
        'RENDER_PT_eevee_next_depth_of_field',
        'RENDER_PT_eevee_bloom',
        'RENDER_PT_eevee_volumetric',
        'RENDER_PT_eevee_volumetric_lighting',
        'RENDER_PT_eevee_volumetric_shadows',
        'RENDER_PT_eevee_subsurface_scattering',
        'RENDER_PT_eevee_screen_space_reflections',
        'RENDER_PT_eevee_shadows',
        'RENDER_PT_eevee_next_shadows',
        'RENDER_PT_eevee_sampling',
        'RENDER_PT_eevee_indirect_lighting',
        'RENDER_PT_eevee_indirect_lighting_display',
        'RENDER_PT_eevee_film',
        'RENDER_PT_eevee_hair',
        'RENDER_PT_eevee_performance',

        'RENDER_PT_gpencil',
        'RENDER_PT_freestyle',
        'RENDER_PT_simplify',
    }    
    panels = []
    panels.append(RENDER_PT_braas_hpc_renderengine_server)

    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'COMPAT_ENGINES') and ('BLENDER_RENDER' in panel.COMPAT_ENGINES or 'BLENDER_EEVEE' in panel.COMPAT_ENGINES):
            if panel.__name__ not in exclude_panels:
                panels.append(panel)

    return panels


def register():
    # Register the RenderEngine
    bpy.utils.register_class(BRaaSHPCRenderEngine)
    bpy.utils.register_class(BRaaSHPCServerSettings)
    bpy.utils.register_class(BRaaSHPCRenderSettings)
    bpy.utils.register_class(RENDER_PT_braas_hpc_renderengine_server)
    bpy.utils.register_class(BRaaSHPCShowPopupErrorMessage)

    bpy.types.Scene.braas_hpc_renderengine = bpy.props.PointerProperty(
        name="Render Settings",
        description="Render settings",
        type=BRaaSHPCRenderSettings,
    )

    bpy.types.Scene.braas_hpc_renderengine_data = BRaaSHPCData()

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('BRAAS_HPC')


def unregister():
    bpy.utils.unregister_class(BRaaSHPCRenderEngine)
    bpy.utils.unregister_class(BRaaSHPCServerSettings)
    bpy.utils.unregister_class(BRaaSHPCRenderSettings)
    bpy.utils.unregister_class(RENDER_PT_braas_hpc_renderengine_server)
    bpy.utils.unregister_class(BRaaSHPCShowPopupErrorMessage)

    delattr(bpy.types.Scene, 'braas_hpc_renderengine')
    delattr(bpy.types.Scene, 'braas_hpc_renderengine_data')

    for panel in get_panels():
        if 'BRAAS_HPC' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('BRAAS_HPC')

