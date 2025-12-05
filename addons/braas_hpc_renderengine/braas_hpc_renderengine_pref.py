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

import bpy

ADDON_NAME = 'braas_hpc_renderengine'

#######################BRaaSHPCRenderEnginePreferences#########################################

class BRaaSHPCRenderEnginePreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_NAME

    # braas_hpc_renderengine_port: bpy.props.IntProperty(
    #     name="Port",
    #     min=0,
    #     max=65565,
    #     default=7000
    # ) # type: ignore

    # braas_hpc_renderengine_server_name: bpy.props.StringProperty(
    #     name="Server",
    #     default="localhost"
    # ) # type: ignore

    braas_hpc_renderengine_use_gpujpeg: bpy.props.BoolProperty(
        name="Use GPUJPEG",
        default=False
    ) # type: ignore    

    def draw(self, context):
        layout = self.layout

        box = layout #.box()
        # box.label(text='TCP Server:')
        #col = box.column()
        box.prop(self, "braas_hpc_renderengine_use_gpujpeg", text="Use GPUJPEG")
        # col.prop(self, "braas_hpc_renderengine_server_name", text="Server")
        # col.prop(self, "braas_hpc_renderengine_port", text="Port")

def ctx_preferences():
    try:
        return bpy.context.preferences
    except AttributeError:
        return bpy.context.user_preferences

def preferences() -> BRaaSHPCRenderEnginePreferences:
    return ctx_preferences().addons[ADDON_NAME].preferences

def register():
    bpy.utils.register_class(BRaaSHPCRenderEnginePreferences)
    pass

def unregister():
    bpy.utils.unregister_class(BRaaSHPCRenderEnginePreferences)
    pass
