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
bl_info = {
    "name": "BRaaS-HPC-RenderEngine",
    "author": "Milan Jaros, Petr Strakos, Lubomir Riha",
    "description": "",
    "blender": (4, 0, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Render"
}
#####################################################################################################################

def register():
    from . import braas_hpc_renderengine_pref
    from . import braas_hpc_renderengine_render
    from . import braas_hpc_renderengine_scene

    braas_hpc_renderengine_pref.register()
    braas_hpc_renderengine_render.register()
    braas_hpc_renderengine_scene.register()
    

def unregister():
    from . import braas_hpc_renderengine_pref
    from . import braas_hpc_renderengine_render
    from . import braas_hpc_renderengine_scene
    
    try:        
        braas_hpc_renderengine_pref.unregister()
        braas_hpc_renderengine_render.unregister()
        braas_hpc_renderengine_scene.unregister()

    except RuntimeError:
        pass 