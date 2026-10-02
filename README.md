Introduction:
Batch Material Helper is a Blender add-on designed to streamline material editing for selected objects. It allows users to quickly adjust a wide range of Principled BSDF shader parameters and material settings in bulk, making it ideal for managing large numbers of shaders imported from XPS and FBX formats.

Short Tutorial:
1. Select objects (e.g., imported XPS or FBX models) in the 3D Viewport.
2. Open the sidebar (N key), find the "Material" tab, and locate the "Batch Material Helper" panel.
3. Check the boxes next to the properties you want to edit (e.g., Base Color, Metallic, Roughness).
4. Adjust the values as needed and click "Apply to Selected" to update all selected materials instantly.

Subsurface Scattering:
Subsurface controls are part of the "BSDF Properties" section and include Weight, Method, Scale, Radius, IOR and Anisotropy. Radius, IOR and Anisotropy are supported by Blender's Principled BSDF from version 4.0 onward.

---

简介：
批量材质助手是一个 Blender 插件，旨在简化选定物体的材质编辑。它允许用户快速批量调整 Principled BSDF 着色器的多种参数和材质设置，非常适合处理从 XPS 和 FBX 格式导入的大量着色器。

简短教程：
1. 在 3D 视口中选择物体（例如导入的 XPS 或 FBX 模型）。
2. 打开侧边栏（N 键），找到 "Material" 选项卡，定位 "批量材质助手" 面板。
3. 勾选你想编辑的属性旁边的复选框（例如基础颜色、金属度、糙度）。
4. 根据需要调整值，然后点击 "应用到选中"，即可立即更新所有选定材质。

次表面散射：
次表面相关控制已并入 "BSDF 属性" 分区，包括权重、方法、缩放、半径、IOR 和各向异性。半径、IOR 和各向异性需要 Blender 4.0 及以上的 Principled BSDF 支持。

---

Blender 5.2 compatibility (this fork):
- Requires Blender 5.2+ (`blender_version_min = "5.2.0"`).
- Principled BSDF sockets are resolved by name instead of hardcoded index. Blender 5.2 inserted a new "Thin Wall" socket, which previously shifted every later socket and caused "IOR Level" to overwrite "Subsurface Anisotropy".
- Fixed the subsurface method enum: "Random Walk (Legacy)" now uses the correct identifier `RANDOM_WALK_LEGACY` (`RANDOM_WALK_TRADITIONAL` no longer exists).
- Extended subsurface controls: Radius, IOR and Anisotropy, alongside Weight, Method and Scale, merged into the BSDF Properties section.
- Added Specular Tint, Anisotropic, Anisotropic Rotation, Coat Roughness/IOR/Tint and Sheen Roughness/Tint.
- Updated Simplified/Traditional Chinese translations for the new options.