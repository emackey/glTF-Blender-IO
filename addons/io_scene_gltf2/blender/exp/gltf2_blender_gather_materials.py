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

from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.blender.exp import gltf2_blender_gather_texture_info, gltf2_blender_export_keys
from io_scene_gltf2.blender.exp import gltf2_blender_gather_material_normal_texture_info_class
from io_scene_gltf2.blender.exp import gltf2_blender_gather_material_occlusion_texture_info_class

from io_scene_gltf2.blender.exp import gltf2_blender_gather_materials_pbr_metallic_roughness
from io_scene_gltf2.blender.exp import gltf2_blender_generate_extras
from io_scene_gltf2.blender.exp import gltf2_blender_get


@cached
def gather_material(blender_material, mesh_double_sided, export_settings):
    """
    Gather the material used by the blender primitive.

    :param blender_material: the blender material used in the glTF primitive
    :param export_settings:
    :return: a glTF material
    """
    if not __filter_material(blender_material, export_settings):
        return None

    # glTF can share the Occlusion image (red) with rough/metal (green/blue).  We'll check for
    # the possibility of that optimization first, and if not applicable we'll process separately.
    #occlusion_roughness_metallic = __gather_orm_texture(blender_material, export_settings)

    material = gltf2_io.Material(
        alpha_cutoff=__gather_alpha_cutoff(blender_material, export_settings),
        alpha_mode=__gather_alpha_mode(blender_material, export_settings),
        double_sided=__gather_double_sided(blender_material, mesh_double_sided, export_settings),
        emissive_factor=__gather_emissive_factor(blender_material, export_settings),
        emissive_texture=__gather_emissive_texture(blender_material, export_settings),
        extensions=__gather_extensions(blender_material, export_settings),
        extras=__gather_extras(blender_material, export_settings),
        name=__gather_name(blender_material, export_settings),
        normal_texture=__gather_normal_texture(blender_material, export_settings),
        # TODO: Pass in occlusion_roughness_metallic as a paramter to both of the following two:
        occlusion_texture=__gather_occlusion_texture(blender_material, export_settings),
        pbr_metallic_roughness=__gather_pbr_metallic_roughness(blender_material, export_settings)
    )

    return material
    # material = blender_primitive['material']
    #
    #     if get_material_requires_texcoords(glTF, material) and not export_settings['gltf_texcoords']:
    #         material = -1
    #
    #     if get_material_requires_normals(glTF, material) and not export_settings['gltf_normals']:
    #         material = -1
    #
    #     # Meshes/primitives without material are allowed.
    #     if material >= 0:
    #         primitive.material = material
    #     else:
    #         print_console('WARNING', 'Material ' + internal_primitive[
    #             'material'] + ' not found. Please assign glTF 2.0 material or enable Blinn-Phong material in export.')


def __filter_material(blender_material, export_settings):
    return export_settings[gltf2_blender_export_keys.MATERIALS]


def __gather_alpha_cutoff(blender_material, export_settings):
    if bpy.app.version < (2, 80, 0):
        return None
    else:
        if blender_material.blend_method == 'CLIP':
            return blender_material.alpha_threshold
    return None


def __gather_alpha_mode(blender_material, export_settings):
    if bpy.app.version < (2, 80, 0):
        return None
    else:
        if blender_material.blend_method == 'CLIP':
            return 'MASK'
        elif blender_material.blend_method == 'BLEND':
            return 'BLEND'
    return None


def __gather_double_sided(blender_material, mesh_double_sided, export_settings):
    if mesh_double_sided:
        return True

    old_double_sided_socket = gltf2_blender_get.get_socket_or_texture_slot_old(blender_material, "DoubleSided")
    if old_double_sided_socket is not None and\
            not old_double_sided_socket.is_linked and\
            old_double_sided_socket.default_value > 0.5:
        return True
    return None


def __gather_emissive_factor(blender_material, export_settings):
    emissive_socket = gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Emissive")
    if emissive_socket is None:
        emissive_socket = gltf2_blender_get.get_socket_or_texture_slot_old(blender_material, "EmissiveFactor")
    if isinstance(emissive_socket, bpy.types.NodeSocket):
        if emissive_socket.is_linked:
            # In glTF, the default emissiveFactor is all zeros, so if an emission texture is connected,
            # we have to manually set it to all ones.
            return [1.0, 1.0, 1.0]
        else:
            return list(emissive_socket.default_value)[0:3]
    return None


def __gather_emissive_texture(blender_material, export_settings):
    emissive = gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Emissive")
    if emissive is None:
        emissive = gltf2_blender_get.get_socket_or_texture_slot_old(blender_material, "Emissive")
    return gltf2_blender_gather_texture_info.gather_texture_info((emissive,), export_settings)


def __gather_extensions(blender_material, export_settings):
    extensions = {}

    if bpy.app.version < (2, 80, 0):
        if blender_material.use_shadeless:
            extensions["KHR_materials_unlit"] = Extension("KHR_materials_unlit", {}, False)
    else:
        if gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Background") is not None:
            extensions["KHR_materials_unlit"] = Extension("KHR_materials_unlit", {}, False)

    # TODO specular glossiness extension

    return extensions if extensions else None


def __gather_extras(blender_material, export_settings):
    if export_settings['gltf_extras']:
        return gltf2_blender_generate_extras.generate_extras(blender_material)
    return None


def __gather_name(blender_material, export_settings):
    return blender_material.name


def __gather_normal_texture(blender_material, export_settings):
    normal = gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Normal")
    if normal is None:
        normal = gltf2_blender_get.get_socket_or_texture_slot_old(blender_material, "Normal")
    return gltf2_blender_gather_material_normal_texture_info_class.gather_material_normal_texture_info_class(
        (normal,),
        export_settings)


def __gather_orm_texture(blender_material, export_settings):
    # Check for the presence of Occlusion, Roughness, Metallic sharing a single image.
    # If not fully shared, return None, so the images will be cached and processed separately.

    occlusion = gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Occlusion")
    if occlusion is None:
        occlusion = gltf2_blender_get.get_socket_or_texture_slot_old(blender_material, "Occlusion")
        if occlusion is None:
            return None

    occlusion_image_node = __get_image_node_from_socket(occlusion)
    if occlusion_image_node is None:
        return None

    # Occlusion:  index=__gather_index(blender_shader_sockets_or_texture_slots, export_settings)
    # Occlusion:  index=__gather_index((occlusion,), export_settings)

    metallic_socket = gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Metallic")
    roughness_socket = gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Roughness")

    if metallic_socket is None and roughness_socket is None:
        metallic_roughness = gltf2_blender_get.get_socket_or_texture_slot_old(blender_material, "MetallicRoughness")
        metal_rough_image_node = __get_image_node_from_socket(metallic_roughness)
        if metal_rough_image_node is not occlusion_image_node:
            return None
    else:
        metal_image_node = __get_image_node_from_socket(metallic_socket)
        if metal_image_node is not occlusion_image_node:
            return None
        rough_image_node = __get_image_node_from_socket(roughness_socket)
        if rough_image_node is not occlusion_image_node:
            return None

    return (occlusion,)

def __gather_occlusion_texture(blender_material, export_settings):
    occlusion = gltf2_blender_get.get_socket_or_texture_slot(blender_material, "Occlusion")
    if occlusion is None:
        occlusion = gltf2_blender_get.get_socket_or_texture_slot_old(blender_material, "Occlusion")
    return gltf2_blender_gather_material_occlusion_texture_info_class.gather_material_occlusion_texture_info_class(
        (occlusion,),
        export_settings)


def __gather_pbr_metallic_roughness(blender_material, export_settings):
    return gltf2_blender_gather_materials_pbr_metallic_roughness.gather_material_pbr_metallic_roughness(
        blender_material,
        export_settings)


def __get_image_node_from_socket(socket):
    result = gltf2_blender_search_node_tree.from_socket(
        socket,
        gltf2_blender_search_node_tree.FilterByType(bpy.types.ShaderNodeTexImage))
    if not result:
        return None
    return result[0].shader_node
