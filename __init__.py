bl_info = {
    "name": "Batch Material Helper",
    "author": "maylog",
    "version": (1, 1, 0),
    "blender": (5, 2, 0),
    "location": "View3D > Sidebar > Material",
    "description": "Batch adjust material and BSDF properties for selected objects",
    "category": "Material",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import FloatProperty, FloatVectorProperty, BoolProperty, EnumProperty
from .translations import translations_dict
from bpy.app.translations import pgettext_iface

# Blender version as a comparable tuple, e.g. (5, 2, 0).
BLENDER_VERSION = bpy.app.version


def get_color_space_items(self, context):
    # Dynamic fetch of the color spaces available in this build.
    # In Blender 5.2 the enum moved off the 'name' property, so try several
    # RNA paths and fall back to the datablock enum query as a last resort.
    items = []
    try:
        rna_enum = bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items
        for i, item in enumerate(rna_enum):
            items.append((item.identifier, item.name, item.description, i))
    except Exception:
        pass

    if not items:
        try:
            rna_enum = bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['colorspace'].enum_items
            for i, item in enumerate(rna_enum):
                items.append((item.identifier, item.name, item.description, i))
        except Exception:
            pass

    if not items:
        try:
            rna_enum = bpy.types.Image.bl_rna.properties['colorspace_settings'].fixed_type.properties['name'].enum_items
            for i, item in enumerate(rna_enum):
                items.append((item.identifier, item.name, item.description, i))
        except Exception:
            pass

    if not items:
        items = [
            ('sRGB', "sRGB", "", 0),
            ('Non-Color', "Non-Color", "", 1),
            ('Linear Rec.709', "Linear Rec.709", "", 2),
        ]
    return items


# --- Compatibility helpers -------------------------------------------------
#
# Blender 5.2 renamed/split several Principled BSDF inputs.  Socket string
# lookups are unreliable across versions (and 'Subsurface IOR' / 'Weight' are
# not reachable via inputs[name] at all), so every socket is resolved by
# iterating the collection and comparing names.  Each logical property lists
# candidate names in priority order.

def _find_input(node, names):
    if node is None:
        return None
    for name in names:
        for sock in node.inputs:
            if sock.name == name:
                return sock
    return None


PRINCIPLED_INPUTS = {
    # property suffix -> candidate socket names (first match wins)
    "base_color": ("Base Color",),
    "metallic": ("Metallic",),
    "roughness": ("Roughness",),
    "ior": ("IOR",),
    "alpha": ("Alpha",),
    "ior_level": ("IOR Level", "Specular IOR Level"),
    "specular_tint": ("Specular Tint",),
    "anisotropic": ("Anisotropic",),
    "anisotropic_rotation": ("Anisotropic Rotation",),
    "emission_color": ("Emission Color",),
    "emission_strength": ("Emission Strength",),
    "coat_weight": ("Coat Weight",),
    "coat_roughness": ("Coat Roughness",),
    "coat_ior": ("Coat IOR",),
    "coat_tint": ("Coat Tint",),
    "sheen_weight": ("Sheen Weight",),
    "sheen_roughness": ("Sheen Roughness",),
    "sheen_tint": ("Sheen Tint",),
    "transmission_weight": ("Transmission Weight",),
    "subsurface_weight": ("Subsurface Weight",),
    "subsurface_radius": ("Subsurface Radius",),
    "subsurface_scale": ("Subsurface Scale",),
    "subsurface_ior": ("Subsurface IOR",),
    "subsurface_anisotropy": ("Subsurface Anisotropy",),
}

# Subsurface methods exposed by the UI.  The scripted value is applied by
# name first and index as a fallback.
SUBSURFACE_METHOD_INDEX = {
    'BURLEY': 0,
    'RANDOM_WALK': 1,
    'RANDOM_WALK_SKIN': 2,
    'RANDOM_WALK_LEGACY': 3,
}


def _iter_principled_nodes(nodes):
    # Only the material's own (top-level) nodes are modified, so reusable node
    # groups shared across materials are never changed as a side effect.
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            yield node


def _set_subsurface_method(principled, value):
    try:
        principled.subsurface_method = value
        return
    except Exception:
        pass
    idx = SUBSURFACE_METHOD_INDEX.get(value)
    enum_items = principled.bl_rna.properties['subsurface_method'].enum_items
    if idx is not None and idx < len(enum_items):
        try:
            principled.subsurface_method = enum_items[idx].identifier
        except Exception:
            pass


def _set_color_space(tex_node, requested):
    """Apply a color space to the texture node's image."""
    try:
        tex_node.image.colorspace_settings.name = requested
        return True
    except Exception:
        return False


class BatchMaterialProperties(PropertyGroup):
    # --- BSDF Properties ---
    batch_base_color: FloatVectorProperty(name="Base Color", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4)
    use_base_color: BoolProperty(name="Use Base Color", default=False)
    batch_metallic: FloatProperty(name="Metallic", default=0.0, min=0.0, max=1.0)
    use_metallic: BoolProperty(name="Use Metallic", default=False)
    batch_roughness: FloatProperty(name="Roughness", default=0.5, min=0.0, max=1.0)
    use_roughness: BoolProperty(name="Use Roughness", default=False)
    batch_ior: FloatProperty(name="IOR", default=1.45, min=0.0, max=1000.0)
    use_ior: BoolProperty(name="Use IOR", default=False)
    batch_alpha: FloatProperty(name="Alpha", default=1.0, min=0.0, max=1.0)
    use_alpha: BoolProperty(name="Use Alpha", default=False)
    batch_ior_level: FloatProperty(name="IOR Level", default=0.5, min=0.0, max=1.0)
    use_ior_level: BoolProperty(name="Use IOR Level", default=False)
    batch_specular_tint: FloatVectorProperty(name="Specular Tint", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4)
    use_specular_tint: BoolProperty(name="Use Specular Tint", default=False)
    batch_anisotropic: FloatProperty(name="Anisotropic", default=0.0, min=0.0, max=1.0)
    use_anisotropic: BoolProperty(name="Use Anisotropic", default=False)
    batch_anisotropic_rotation: FloatProperty(name="Anisotropic Rotation", default=0.0, min=0.0, max=1.0)
    use_anisotropic_rotation: BoolProperty(name="Use Anisotropic Rotation", default=False)
    batch_emission_color: FloatVectorProperty(name="Emission Color", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4)
    use_emission_color: BoolProperty(name="Use Emission Color", default=False)
    batch_emission_strength: FloatProperty(name="Emission Strength", default=0.0, min=0.0)
    use_emission_strength: BoolProperty(name="Use Emission Strength", default=False)
    batch_coat_weight: FloatProperty(name="Coat Weight", default=0.0, min=0.0, max=1.0)
    use_coat_weight: BoolProperty(name="Use Coat Weight", default=False)
    batch_coat_roughness: FloatProperty(name="Coat Roughness", default=0.03, min=0.0, max=1.0)
    use_coat_roughness: BoolProperty(name="Use Coat Roughness", default=False)
    batch_coat_ior: FloatProperty(name="Coat IOR", default=1.5, min=0.0, max=1000.0)
    use_coat_ior: BoolProperty(name="Use Coat IOR", default=False)
    batch_coat_tint: FloatVectorProperty(name="Coat Tint", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4)
    use_coat_tint: BoolProperty(name="Use Coat Tint", default=False)
    batch_sheen_weight: FloatProperty(name="Sheen Weight", default=0.0, min=0.0, max=1.0)
    use_sheen_weight: BoolProperty(name="Use Sheen Weight", default=False)
    batch_sheen_roughness: FloatProperty(name="Sheen Roughness", default=0.5, min=0.0, max=1.0)
    use_sheen_roughness: BoolProperty(name="Use Sheen Roughness", default=False)
    batch_sheen_tint: FloatVectorProperty(name="Sheen Tint", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4)
    use_sheen_tint: BoolProperty(name="Use Sheen Tint", default=False)
    batch_transmission_weight: FloatProperty(name="Transmission Weight", default=0.0, min=0.0, max=1.0)
    use_transmission_weight: BoolProperty(name="Use Transmission Weight", default=False)
    batch_subsurface_weight: FloatProperty(name="Subsurface Weight", default=0.0, min=0.0, max=1.0)
    use_subsurface_weight: BoolProperty(name="Use Subsurface Weight", default=False)
    batch_subsurface_method: EnumProperty(
        name="Subsurface Method",
        items=[
            ('BURLEY', "Christensen-Burley", "Approximation to physically based volume scattering"),
            ('RANDOM_WALK', "Random Walk", "Volumetric approximation to physically based volume scattering, using the scattering radius as specified"),
            ('RANDOM_WALK_SKIN', "Random Walk (Skin)", "Volumetric approximation to physically based volume scattering, with scattering radius automatically adjusted to match color textures. Designed for skin shading."),
            ('RANDOM_WALK_LEGACY', "Random Walk (Legacy)", "Volumetric approximation to physically based volume scattering, using the scattering radius as specified"),
        ],
        default='RANDOM_WALK'
    )
    use_subsurface_method: BoolProperty(name="Use Subsurface Method", default=False)
    batch_subsurface_scale: FloatProperty(name="Subsurface Scale", default=0.05, min=0.0, unit='LENGTH')
    use_subsurface_scale: BoolProperty(name="Use Subsurface Scale", default=False)
    batch_subsurface_radius: FloatVectorProperty(name="Subsurface Radius", default=(1.0, 0.2, 0.1), min=0.0, size=3)
    use_subsurface_radius: BoolProperty(name="Use Subsurface Radius", default=False)
    batch_subsurface_ior: FloatProperty(name="Subsurface IOR", default=1.4, min=0.0, max=1000.0)
    use_subsurface_ior: BoolProperty(name="Use Subsurface IOR", default=False)
    batch_subsurface_anisotropy: FloatProperty(name="Subsurface Anisotropy", default=0.0, min=-1.0, max=1.0)
    use_subsurface_anisotropy: BoolProperty(name="Use Subsurface Anisotropy", default=False)

    # --- Node Settings ---
    batch_normal_convention: EnumProperty(
        name="Normal Convention",
        items=[('OPENGL', "OpenGL", "Y+"), ('DIRECTX', "DirectX", "Y-")],
        default='OPENGL'
    )
    use_normal_convention: BoolProperty(name="Use Normal Convention", default=False)

    # --- Image Settings ---
    batch_alpha_mode: EnumProperty(
        name="Alpha Mode",
        items=[('STRAIGHT', "Straight", ""), ('PREMUL', "Premultiplied", ""), ('CHANNEL_PACKED', "Channel Packed", ""), ('NONE', "None", "")],
        default='STRAIGHT'
    )
    use_alpha_mode: BoolProperty(name="Use Alpha Mode", default=False)
    batch_color_space: EnumProperty(name="Color Space", items=get_color_space_items)
    use_color_space: BoolProperty(name="Use Color Space", default=False)

    # --- Material Settings ---
    batch_render_method: EnumProperty(name="Render Method", items=[('DITHERED', "Dithered", ""), ('BLENDED', "Blended", "")], default='DITHERED')
    use_render_method: BoolProperty(name="Use Render Method", default=False)
    batch_displacement_method: EnumProperty(name="Displacement Method", items=[('BUMP', "Bump", ""), ('DISPLACEMENT', "Displacement", ""), ('BOTH', "Both", "")], default='BUMP')
    use_displacement_method: BoolProperty(name="Use Displacement Method", default=False)
    batch_backface_culling: BoolProperty(name="Backface Culling (Camera)", default=False)
    use_backface_culling: BoolProperty(name="Use Backface Culling (Camera)", default=False)
    batch_backface_culling_shadow: BoolProperty(name="Backface Culling (Shadow)", default=False)
    use_backface_culling_shadow: BoolProperty(name="Use Backface Culling (Shadow)", default=False)
    batch_backface_culling_lightprobe: BoolProperty(name="Backface Culling (Lightprobe)", default=False)
    use_backface_culling_lightprobe: BoolProperty(name="Use Backface Culling (Lightprobe)", default=False)
    batch_transparent_shadow: BoolProperty(name="Raytrace Transmission", default=False)
    use_transparent_shadow: BoolProperty(name="Use Raytrace Transmission", default=False)

    # --- Viewport ---
    batch_diffuse_color: FloatVectorProperty(name="Diffuse Color", subtype='COLOR', default=(0.8, 0.8, 0.8, 1.0), size=4)
    use_diffuse_color: BoolProperty(name="Use Diffuse Color", default=False)
    batch_display_metallic: FloatProperty(name="Display Metallic", default=0.0, min=0.0, max=1.0)
    use_display_metallic: BoolProperty(name="Use Display Metallic", default=False)
    batch_display_roughness: FloatProperty(name="Display Roughness", default=0.5, min=0.0, max=1.0)
    use_display_roughness: BoolProperty(name="Use Display Roughness", default=False)
    use_clear_custom_split_normals: BoolProperty(name="Clear Custom Split Normals Data", default=False)

    # --- UI Foldout States ---
    show_bsdf: BoolProperty(name="BSDF Properties", default=False)
    show_mat_settings: BoolProperty(name="Material Settings", default=False)
    show_viewport: BoolProperty(name="Viewport", default=False)
    show_nodes: BoolProperty(name="Node Properties", default=False)
    show_images: BoolProperty(name="Image Texture Settings", default=False)
    show_mesh: BoolProperty(name="Mesh Properties", default=False)


class MATERIAL_OT_batch_material_helper(Operator):
    bl_idname = "material.batch_material_helper"
    bl_label = "Batch Material Helper"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.batch_material_props
        selected_objects = [obj for obj in context.selected_objects if hasattr(obj, "material_slots")]

        for obj in selected_objects:
            if props.use_clear_custom_split_normals and obj.type == 'MESH':
                try:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
                except Exception:
                    pass

            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat:
                    continue
                self._apply_material(props, mat)

        return {'FINISHED'}

    # -- internal ---------------------------------------------------------
    def _apply_material(self, props, mat):
        # Material-level settings (guarded so unsupported props are skipped).
        material_settings = (
            ("use_render_method", "surface_render_method", "batch_render_method"),
            ("use_displacement_method", "displacement_method", "batch_displacement_method"),
            ("use_backface_culling", "use_backface_culling", "batch_backface_culling"),
            ("use_backface_culling_shadow", "use_backface_culling_shadow", "batch_backface_culling_shadow"),
            ("use_backface_culling_lightprobe", "use_backface_culling_lightprobe_volume", "batch_backface_culling_lightprobe"),
            ("use_transparent_shadow", "use_transparent_shadow", "batch_transparent_shadow"),
            ("use_diffuse_color", "diffuse_color", "batch_diffuse_color"),
            ("use_display_metallic", "metallic", "batch_display_metallic"),
            ("use_display_roughness", "roughness", "batch_display_roughness"),
        )
        for flag, attr, value in material_settings:
            if not getattr(props, flag):
                continue
            if not hasattr(mat, attr):
                continue
            try:
                setattr(mat, attr, getattr(props, value))
            except Exception:
                pass

        # Materials can exist without a node tree; only touch nodes when present.
        if not getattr(mat, "node_tree", None):
            return
        nodes = mat.node_tree.nodes

        if props.use_alpha_mode or props.use_color_space:
            for node in nodes:
                if node.type != 'TEX_IMAGE' or not node.image:
                    continue
                if props.use_alpha_mode:
                    try:
                        node.image.alpha_mode = props.batch_alpha_mode
                    except Exception:
                        pass
                if props.use_color_space:
                    _set_color_space(node, props.batch_color_space)

        for principled in _iter_principled_nodes(nodes):
            for suffix, socket_names in PRINCIPLED_INPUTS.items():
                if not getattr(props, f"use_{suffix}"):
                    continue
                sock = _find_input(principled, socket_names)
                if sock is None:
                    continue
                try:
                    sock.default_value = getattr(props, f"batch_{suffix}")
                except Exception:
                    pass

            if props.use_subsurface_method:
                _set_subsurface_method(principled, props.batch_subsurface_method)

        if props.use_normal_convention:
            for node in nodes:
                if node.type == 'NORMAL_MAP':
                    try:
                        node.convention = props.batch_normal_convention
                    except Exception:
                        pass


class VIEW3D_PT_batch_material_helper(Panel):
    bl_label = "Batch Material Helper"
    bl_idname = "VIEW3D_PT_batch_material_helper"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Material"

    def draw(self, context):
        layout = self.layout
        props = context.scene.batch_material_props

        # 1. Apply Button at the Top (Double Height)
        col = layout.column(align=True)
        col.scale_y = 2.0
        col.operator("material.batch_material_helper", text=pgettext_iface("Apply to Selected"), icon='CHECKMARK')
        layout.separator()

        def draw_row(target_layout, p_use, p_val, label):
            row = target_layout.row(align=True)
            row.prop(props, p_use, text="")
            sub = row.row(align=True)
            sub.active = getattr(props, p_use)
            sub.prop(props, p_val, text=label)

        def draw_section(prop_name, icon, title, items):
            box = layout.box()
            row = box.row()
            row.prop(props, prop_name, icon='TRIA_DOWN' if getattr(props, prop_name) else 'TRIA_RIGHT', icon_only=True, emboss=False)
            row.label(text=title, icon=icon)
            if getattr(props, prop_name):
                col = box.column(align=True)
                for item in items:
                    draw_row(col, *item)
                return col
            return None

        # 2. Collapsible Sections
        # --- BSDF ---
        draw_section("show_bsdf", 'MATERIAL', "BSDF Properties", [
            ("use_base_color", "batch_base_color", "Base Color"),
            ("use_metallic", "batch_metallic", "Metallic"),
            ("use_roughness", "batch_roughness", "Roughness"),
            ("use_ior", "batch_ior", "IOR"),
            ("use_alpha", "batch_alpha", "Alpha"),
            ("use_ior_level", "batch_ior_level", "IOR Level"),
            ("use_specular_tint", "batch_specular_tint", "Specular Tint"),
            ("use_anisotropic", "batch_anisotropic", "Anisotropic"),
            ("use_anisotropic_rotation", "batch_anisotropic_rotation", "Anisotropic Rotation"),
            ("use_emission_color", "batch_emission_color", "Emission Color"),
            ("use_emission_strength", "batch_emission_strength", "Emission Strength"),
            ("use_coat_weight", "batch_coat_weight", "Coat Weight"),
            ("use_coat_roughness", "batch_coat_roughness", "Coat Roughness"),
            ("use_coat_ior", "batch_coat_ior", "Coat IOR"),
            ("use_coat_tint", "batch_coat_tint", "Coat Tint"),
            ("use_sheen_weight", "batch_sheen_weight", "Sheen Weight"),
            ("use_sheen_roughness", "batch_sheen_roughness", "Sheen Roughness"),
            ("use_sheen_tint", "batch_sheen_tint", "Sheen Tint"),
            ("use_transmission_weight", "batch_transmission_weight", "Transmission Weight"),
            ("use_subsurface_weight", "batch_subsurface_weight", "Subsurface Weight"),
            ("use_subsurface_method", "batch_subsurface_method", "Subsurface Method"),
            ("use_subsurface_scale", "batch_subsurface_scale", "Subsurface Scale"),
            ("use_subsurface_radius", "batch_subsurface_radius", "Subsurface Radius"),
            ("use_subsurface_ior", "batch_subsurface_ior", "Subsurface IOR"),
            ("use_subsurface_anisotropy", "batch_subsurface_anisotropy", "Subsurface Anisotropy"),
        ])

        # --- Material Settings ---
        draw_section("show_mat_settings", 'MATERIAL', "Material Settings", [
            ("use_render_method", "batch_render_method", "Render Method"),
            ("use_displacement_method", "batch_displacement_method", "Displacement Method"),
            ("use_backface_culling", "batch_backface_culling", "Backface Culling (Camera)"),
            ("use_backface_culling_shadow", "batch_backface_culling_shadow", "Backface Culling (Shadow)"),
            ("use_backface_culling_lightprobe", "batch_backface_culling_lightprobe", "Backface Culling (Lightprobe)"),
            ("use_transparent_shadow", "batch_transparent_shadow", "Raytrace Transmission"),
        ])

        # --- Viewport ---
        draw_section("show_viewport", 'MATERIAL', "Viewport", [
            ("use_diffuse_color", "batch_diffuse_color", "Diffuse Color"),
            ("use_display_metallic", "batch_display_metallic", "Metallic"),
            ("use_display_roughness", "batch_display_roughness", "Roughness"),
        ])

        # --- Node Properties ---
        sub = draw_section("show_nodes", 'NODETREE', "Node Properties", [
            ("use_normal_convention", "batch_normal_convention", "Normal Y"),
        ])
        if sub is not None and props.use_normal_convention and BLENDER_VERSION < (5, 1, 0):
            note = sub.column(align=True)
            note.label(text="Available in Blender 5.1+", icon='ERROR')

        # --- Image Settings ---
        draw_section("show_images", 'IMAGE_DATA', "Image Texture Settings", [
            ("use_alpha_mode", "batch_alpha_mode", "Alpha Mode"),
            ("use_color_space", "batch_color_space", "Color Space"),
        ])

        # --- Mesh Properties ---
        box = layout.box()
        row = box.row()
        row.prop(props, "show_mesh", icon='TRIA_DOWN' if props.show_mesh else 'TRIA_RIGHT', icon_only=True, emboss=False)
        row.label(text="Mesh Properties", icon='MESH_DATA')
        if props.show_mesh:
            box.prop(props, "use_clear_custom_split_normals", text="Clear Custom Split Normals")


classes = (
    BatchMaterialProperties,
    MATERIAL_OT_batch_material_helper,
    VIEW3D_PT_batch_material_helper,
)


def register():
    bpy.app.translations.register(__name__, translations_dict)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.batch_material_props = bpy.props.PointerProperty(type=BatchMaterialProperties)


def unregister():
    bpy.app.translations.unregister(__name__)
    if hasattr(bpy.types.Scene, 'batch_material_props'):
        del bpy.types.Scene.batch_material_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()