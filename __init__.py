bl_info = {
    "name": "Batch Material Helper",
    "author": "maylog",
    "version": (1, 0, 8),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Material",
    "description": "Batch adjust material and BSDF properties for selected objects",
    "category": "Material",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import FloatProperty, FloatVectorProperty, BoolProperty, EnumProperty
from .translations import translations_dict
from bpy.app.translations import pgettext_iface

def get_color_space_items(self, context):
    # Dynamic fetch of available color spaces
    items = []
    try:
        rna_enum = bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items
        for i, item in enumerate(rna_enum):
            items.append((item.identifier, item.name, item.description, i))
    except:
        items = [('sRGB', "sRGB", ""), ('Non-Color', "Non-Color", "")]
    return items

class BatchMaterialProperties(PropertyGroup):
    # --- BSDF Properties ---
    batch_base_color: FloatVectorProperty(name="Base Color", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4)
    use_base_color: BoolProperty(name="Use Base Color", default=False)
    batch_metallic: FloatProperty(name="Metallic", default=0.0, min=0.0, max=1.0)
    use_metallic: BoolProperty(name="Use Metallic", default=False)
    batch_roughness: FloatProperty(name="Roughness", default=0.5, min=0.0, max=1.0)
    use_roughness: BoolProperty(name="Use Roughness", default=False)
    batch_ior: FloatProperty(name="IOR", default=1.45, min=1.0, max=1000.0)
    use_ior: BoolProperty(name="Use IOR", default=False)
    batch_alpha: FloatProperty(name="Alpha", default=1.0, min=0.0, max=1.0)
    use_alpha: BoolProperty(name="Use Alpha", default=False)
    batch_ior_level: FloatProperty(name="IOR Level", default=0.5, min=0.0, max=1.0)
    use_ior_level: BoolProperty(name="Use IOR Level", default=False)
    batch_emission_color: FloatVectorProperty(name="Emission Color", subtype='COLOR', default=(1.0, 1.0, 1.0, 1.0), size=4)
    use_emission_color: BoolProperty(name="Use Emission Color", default=False)
    batch_emission_strength: FloatProperty(name="Emission Strength", default=0.0, min=0.0)
    use_emission_strength: BoolProperty(name="Use Emission Strength", default=False)
    batch_coat_weight: FloatProperty(name="Coat Weight", default=0.0, min=0.0, max=1.0)
    use_coat_weight: BoolProperty(name="Use Coat Weight", default=False)
    batch_sheen_weight: FloatProperty(name="Sheen Weight", default=0.0, min=0.0, max=1.0)
    use_sheen_weight: BoolProperty(name="Use Sheen Weight", default=False)
    batch_transmission_weight: FloatProperty(name="Transmission Weight", default=0.0, min=0.0, max=1.0)
    use_transmission_weight: BoolProperty(name="Use Transmission Weight", default=False)
    batch_subsurface_weight: FloatProperty(name="Subsurface Weight", default=0.0, min=0.0, max=1.0)
    use_subsurface_weight: BoolProperty(name="Use Subsurface Weight", default=False)
    batch_subsurface_method: EnumProperty(
        name="Subsurface Method",
        items=[('BURLEY', "Christensen-Burley", ""), ('RANDOM_WALK', "Random Walk", ""), ('RANDOM_WALK_SKIN', "Random Walk (Skin)", ""), ('RANDOM_WALK_TRADITIONAL', "Random Walk (Legacy)", "")],
        default='RANDOM_WALK'
    )
    use_subsurface_method: BoolProperty(name="Use Subsurface Method", default=False)
    batch_subsurface_scale: FloatProperty(name="Subsurface Scale", default=0.05, min=0.0, unit='LENGTH')
    use_subsurface_scale: BoolProperty(name="Use Subsurface Scale", default=False)

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
                except: pass
            
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat: continue
                
                if props.use_render_method: mat.surface_render_method = props.batch_render_method
                if props.use_displacement_method: mat.displacement_method = props.batch_displacement_method
                if props.use_backface_culling: mat.use_backface_culling = props.batch_backface_culling
                if props.use_backface_culling_shadow: mat.use_backface_culling_shadow = props.batch_backface_culling_shadow
                if props.use_backface_culling_lightprobe: mat.use_backface_culling_lightprobe_volume = props.batch_backface_culling_lightprobe
                if props.use_transparent_shadow: mat.use_transparent_shadow = props.batch_transparent_shadow
                if props.use_diffuse_color: mat.diffuse_color = props.batch_diffuse_color
                if props.use_display_metallic: mat.metallic = props.batch_display_metallic
                if props.use_display_roughness: mat.roughness = props.batch_display_roughness
                
                if mat.use_nodes:
                    nodes = mat.node_tree.nodes
                    if props.use_alpha_mode or props.use_color_space:
                        for n in nodes:
                            if n.type == 'TEX_IMAGE' and n.image:
                                if props.use_alpha_mode: n.image.alpha_mode = props.batch_alpha_mode
                                if props.use_color_space:
                                    try: n.image.colorspace_settings.name = props.batch_color_space
                                    except: pass

                    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
                    if principled:
                        mapping = [
                            ("base_color", "Base Color", 0), ("metallic", "Metallic", 1), 
                            ("roughness", "Roughness", 2), ("ior", "IOR", 3), 
                            ("alpha", "Alpha", 4), ("ior_level", "IOR Level", 13),
                            ("emission_color", "Emission Color", 27), ("emission_strength", "Emission Strength", 28),
                            ("coat_weight", "Coat Weight", 19), ("sheen_weight", "Sheen Weight", 24),
                            ("transmission_weight", "Transmission Weight", 18), ("subsurface_weight", "Subsurface Weight", 8),
                            ("subsurface_scale", "Subsurface Scale", 10)
                        ]
                        for suffix, node_in, idx in mapping:
                            if getattr(props, f"use_{suffix}"):
                                try:
                                    target = principled.inputs.get(node_in) or principled.inputs[idx]
                                    target.default_value = getattr(props, f"batch_{suffix}")
                                except: pass
                        if props.use_subsurface_method: principled.subsurface_method = props.batch_subsurface_method

                    if props.use_normal_convention:
                        for n in nodes:
                            if n.type == 'NORMAL_MAP':
                                try: n.convention = props.batch_normal_convention
                                except: pass
        return {'FINISHED'}

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
            row.prop(props, p_val, text=label)

        # 2. Collapsible Sections
        # --- BSDF ---
        box = layout.box()
        row = box.row()
        row.prop(props, "show_bsdf", icon='TRIA_DOWN' if props.show_bsdf else 'TRIA_RIGHT', icon_only=True, emboss=False)
        row.label(text="BSDF Properties", icon='MATERIAL')
        if props.show_bsdf:
            col = box.column(align=True)
            items = [
                ("use_base_color", "batch_base_color", "Base Color"), ("use_metallic", "batch_metallic", "Metallic"), 
                ("use_roughness", "batch_roughness", "Roughness"), ("use_ior", "batch_ior", "IOR"), 
                ("use_alpha", "batch_alpha", "Alpha"), ("use_ior_level", "batch_ior_level", "IOR Level"), 
                ("use_emission_color", "batch_emission_color", "Emission Color"), ("use_emission_strength", "batch_emission_strength", "Emission Strength"), 
                ("use_coat_weight", "batch_coat_weight", "Coat Weight"), ("use_sheen_weight", "batch_sheen_weight", "Sheen Weight"), 
                ("use_transmission_weight", "batch_transmission_weight", "Transmission Weight"), ("use_subsurface_weight", "batch_subsurface_weight", "Subsurface Weight"), 
                ("use_subsurface_method", "batch_subsurface_method", "Subsurface Method"), ("use_subsurface_scale", "batch_subsurface_scale", "Subsurface Scale")
            ]
            for item in items:
                draw_row(col, *item)

        # --- Material Settings ---
        box = layout.box()
        row = box.row()
        row.prop(props, "show_mat_settings", icon='TRIA_DOWN' if props.show_mat_settings else 'TRIA_RIGHT', icon_only=True, emboss=False)
        row.label(text="Material Settings", icon='MATERIAL')
        if props.show_mat_settings:
            col = box.column(align=True)
            items = [
                ("use_render_method", "batch_render_method", "Render Method"), ("use_displacement_method", "batch_displacement_method", "Displacement Method"), 
                ("use_backface_culling", "batch_backface_culling", "Backface Culling (Camera)"), ("use_backface_culling_shadow", "batch_backface_culling_shadow", "Backface Culling (Shadow)"), 
                ("use_backface_culling_lightprobe", "batch_backface_culling_lightprobe", "Backface Culling (Lightprobe)"), ("use_transparent_shadow", "batch_transparent_shadow", "Raytrace Transmission")
            ]
            for item in items:
                draw_row(col, *item)

        # --- Viewport ---
        box = layout.box()
        row = box.row()
        row.prop(props, "show_viewport", icon='TRIA_DOWN' if props.show_viewport else 'TRIA_RIGHT', icon_only=True, emboss=False)
        row.label(text="Viewport", icon='MATERIAL')
        if props.show_viewport:
            col = box.column(align=True)
            items = [
                ("use_diffuse_color", "batch_diffuse_color", "Diffuse Color"), ("use_display_metallic", "batch_display_metallic", "Metallic"), 
                ("use_display_roughness", "batch_display_roughness", "Roughness")
            ]
            for item in items:
                draw_row(col, *item)

        # --- Node Properties ---
        box = layout.box()
        row = box.row()
        row.prop(props, "show_nodes", icon='TRIA_DOWN' if props.show_nodes else 'TRIA_RIGHT', icon_only=True, emboss=False)
        row.label(text="Node Properties", icon='NODETREE')
        if props.show_nodes:
            col = box.column(align=True)
            draw_row(col, "use_normal_convention", "batch_normal_convention", "Normal Y")
            sub = col.column(align=True)
            sub.active = props.use_normal_convention
            sub.label(text="Requires Blender 5.1+", icon='ERROR')

        # --- Image Settings ---
        box = layout.box()
        row = box.row()
        row.prop(props, "show_images", icon='TRIA_DOWN' if props.show_images else 'TRIA_RIGHT', icon_only=True, emboss=False)
        row.label(text="Image Texture Settings", icon='IMAGE_DATA')
        if props.show_images:
            col = box.column(align=True)
            draw_row(col, "use_alpha_mode", "batch_alpha_mode", "Alpha Mode")
            draw_row(col, "use_color_space", "batch_color_space", "Color Space")

        # --- Mesh Properties ---
        box = layout.box()
        row = box.row()
        row.prop(props, "show_mesh", icon='TRIA_DOWN' if props.show_mesh else 'TRIA_RIGHT', icon_only=True, emboss=False)
        row.label(text="Mesh Properties", icon='MESH_DATA')
        if props.show_mesh:
            box.prop(props, "use_clear_custom_split_normals", text="Clear Custom Split Normals")

def register():
    bpy.app.translations.register(__name__, translations_dict)
    bpy.utils.register_class(BatchMaterialProperties)
    bpy.utils.register_class(MATERIAL_OT_batch_material_helper)
    bpy.utils.register_class(VIEW3D_PT_batch_material_helper)
    bpy.types.Scene.batch_material_props = bpy.props.PointerProperty(type=BatchMaterialProperties)

def unregister():
    bpy.app.translations.unregister(__name__)
    if hasattr(bpy.types.Scene, 'batch_material_props'): del bpy.types.Scene.batch_material_props
    bpy.utils.unregister_class(VIEW3D_PT_batch_material_helper)
    bpy.utils.unregister_class(MATERIAL_OT_batch_material_helper)
    bpy.utils.unregister_class(BatchMaterialProperties)

if __name__ == "__main__":
    register()