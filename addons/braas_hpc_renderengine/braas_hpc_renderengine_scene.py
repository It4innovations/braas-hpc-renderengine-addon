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

import os
import bpy
import numpy as np

from . import braas_hpc_renderengine_pref

try:
    from . import braas_hpc_renderengine_dll
except:
    import braas_hpc_renderengine_dll

class BRaaSHPCCreateBBoxOperator(bpy.types.Operator):
    bl_idname = "braas_hpc_renderengine.create_bbox"
    bl_label = "Load BBox"

    def execute(self, context):
        context.scene.braas_hpc_renderengine_scene.create_bbox(context)
        return {'FINISHED'}

class BRaaSHPCDataInit:
    def __init__(self):
        self.world_bounds_spatial_lower = np.zeros((3), dtype=np.float32)
        self.world_bounds_spatial_upper = np.zeros((3), dtype=np.float32)
        self.scalars_range = np.zeros((2), dtype=np.float32)

class BRaaSHPCScene:
    def __init__(self):
        self.braas_hpc_renderengine_bbox = None

    def get_bbox_name(self):
        return "BRaaS-HPC BBOX"

    def create_bbox(self, context):

        # set env
        #pref = braas_hpc_renderengine_pref.preferences()
                
        braas_hpc_renderengineDataInit = BRaaSHPCDataInit()
        braas_hpc_renderengine_dll.get_braas_hpc_renderengine_range(braas_hpc_renderengineDataInit.world_bounds_spatial_lower.ctypes.data, 
                                                              braas_hpc_renderengineDataInit.world_bounds_spatial_upper.ctypes.data, 
                                                              braas_hpc_renderengineDataInit.scalars_range.ctypes.data)

        # Lower and upper vertex coordinates
        lower_vertex = (braas_hpc_renderengineDataInit.world_bounds_spatial_lower[0], braas_hpc_renderengineDataInit.world_bounds_spatial_lower[1], braas_hpc_renderengineDataInit.world_bounds_spatial_lower[2])
        upper_vertex = (braas_hpc_renderengineDataInit.world_bounds_spatial_upper[0], braas_hpc_renderengineDataInit.world_bounds_spatial_upper[1], braas_hpc_renderengineDataInit.world_bounds_spatial_upper[2])

        # Calculate size and center position
        #size = tuple(upper - lower for upper, lower in zip(upper_vertex, lower_vertex))

        if self.get_bbox_name() in bpy.data.objects:
            obj = bpy.data.objects[self.get_bbox_name()]

            # If the object is linked to a collection, unlink it first
            for collection in obj.users_collection:
                collection.objects.unlink(obj)

            # Delete the object
            bpy.data.objects.remove(obj)

        # vertices = [
        #     (0.0,       0.0,        0.0),
        #     (size[0],   0.0,        0.0),
        #     (size[0],   size[1],    0.0),
        #     (0.0,       size[1],    0.0),
        #     (0.0,       0.0,        size[2]),
        #     (size[0],   0.0,        size[2]),
        #     (size[0],   size[1],    size[2]),
        #     (0.0,       size[1],    size[2])
        # ]    

        vertices = [
            (lower_vertex[0], lower_vertex[1], lower_vertex[2]),                         # (0.0, 0.0, 0.0) --> lower_vertex
            (upper_vertex[0], lower_vertex[1], lower_vertex[2]),                         # (size[0], 0.0, 0.0) --> upper_vertex[0], lower_vertex[1], lower_vertex[2]
            (upper_vertex[0], upper_vertex[1], lower_vertex[2]),                         # (size[0], size[1], 0.0) --> upper_vertex[0], upper_vertex[1], lower_vertex[2]
            (lower_vertex[0], upper_vertex[1], lower_vertex[2]),                         # (0.0, size[1], 0.0) --> lower_vertex[0], upper_vertex[1], lower_vertex[2]
            (lower_vertex[0], lower_vertex[1], upper_vertex[2]),                         # (0.0, 0.0, size[2]) --> lower_vertex[0], lower_vertex[1], upper_vertex[2]
            (upper_vertex[0], lower_vertex[1], upper_vertex[2]),                         # (size[0], 0.0, size[2]) --> upper_vertex[0], lower_vertex[1], upper_vertex[2]
            (upper_vertex[0], upper_vertex[1], upper_vertex[2]),                         # (size[0], size[1], size[2]) --> upper_vertex
            (lower_vertex[0], upper_vertex[1], upper_vertex[2])                          # (0.0, size[1], size[2]) --> lower_vertex[0], upper_vertex[1], upper_vertex[2]
        ]         
               
            

        # Define the edges for the cube
        #edges = []
        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            (4, 5),
            (5, 6),
            (6, 7),
            (7, 4),
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7)
        ]
        faces = []

        # Create the new mesh and object
        mesh = bpy.data.meshes.new(self.get_bbox_name())
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()

        self.braas_hpc_renderengine_bbox = bpy.data.objects.new(self.get_bbox_name(), mesh)

        # Add the object into the scene
        #scene = context.scene
        #scene.collection.objects.link(self.braas_hpc_renderengine_bbox)
        # Get the active collection
        active_collection = context.view_layer.active_layer_collection.collection

        # Add the object into the active collection
        active_collection.objects.link(self.braas_hpc_renderengine_bbox)            

        # Optionally set the object as active and select it
        context.view_layer.objects.active = self.braas_hpc_renderengine_bbox
        #self.braas_hpc_renderengine_bbox.location=-center #TODO

        # set material
        # try:
        #     mat = context.scene.braas_hpc_renderengine.server_settings.mat_volume
        #     mat.node_tree.nodes['DomainX'].outputs[0].default_value = braas_hpc_renderengineDataInit.scalars_range[0]
        #     mat.node_tree.nodes['DomainY'].outputs[0].default_value = braas_hpc_renderengineDataInit.scalars_range[1]
        # except:
        #     pass

        # Ensure the scale is applied correctly
        #bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)        

def register():
    bpy.utils.register_class(BRaaSHPCCreateBBoxOperator)

    bpy.types.Scene.braas_hpc_renderengine_scene = BRaaSHPCScene()
    

def unregister():
    bpy.utils.unregister_class(BRaaSHPCCreateBBoxOperator)

    del bpy.types.Scene.braas_hpc_renderengine_scene