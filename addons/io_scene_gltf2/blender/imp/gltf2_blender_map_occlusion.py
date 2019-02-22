# Copyright 2018 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from .gltf2_blender_texture import BlenderTextureInfo


class BlenderOcclusionMap():
    """Blender Occlusion map."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def create(gltf, material_idx, vertex_color):
        """Occlusion map creation."""
        engine = bpy.context.scene.render.engine
        if engine in ['CYCLES', 'BLENDER_EEVEE']:
            BlenderOcclusionMap.create_nodetree(gltf, material_idx, vertex_color)

    def create_nodetree(gltf, material_idx, vertex_color):
        """Nodetree creation."""
        pymaterial = gltf.data.materials[material_idx]

        BlenderTextureInfo.create(gltf, pymaterial.occlusion_texture.index)

        # Pack texture, but doesn't use it for now. Occlusion is calculated from Cycles.
        if gltf.data.images[gltf.data.textures[
            pymaterial.occlusion_texture.index
        ].source].blender_image_name is not None:
            bpy.data.images[gltf.data.images[gltf.data.textures[
                pymaterial.occlusion_texture.index
            ].source].blender_image_name].use_fake_user = True



        # Put this definition somewhere common, it will likely change to "glTF Settings" or similar.
        gltf_node_group_name = 'glTF Metallic Roughness'

        # The following code runs per-material for materials with occlusion.

        # Check if the custom node group already exists
        if gltf_node_group_name in bpy.data.node_groups:
            gltf_node_group = bpy.data.node_groups[gltf_node_group_name]
        else:
            # Create a new node grouping
            gltf_node_group = bpy.data.node_groups.new(gltf_node_group_name, 'ShaderNodeTree')
            gltf_node_group.inputs.new("NodeSocketFloat", "Occlusion")
            gltf_node_group.nodes.new('NodeGroupOutput')
            gltf_group_input = gltf_node_group.nodes.new('NodeGroupInput')
            gltf_group_input.location = -200, 0

        # Place a new node grouping in the current material
        gltf_settings_node = bpy.data.materials[material_idx].node_tree.nodes.new('ShaderNodeGroup')

        # Set the newly placed node grouping to be the glTF grouping
        gltf_settings_node.node_tree = gltf_node_group
        gltf_settings_node.width = 220

