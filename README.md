# Blender-SRP-Helper
平滑法线用于描边以及cycles烘培ao+自动生成不同层级LOD模型

（图左：无法线平滑/烘培ao  图右：有）

因为我的描边逻辑是受光照影响根据dot结果背光线条粗反之细所以效果是这样但还是看出来右边更加连续

<img width="655" height="361" alt="屏幕截图 2026-03-05 153606" src="https://github.com/user-attachments/assets/084f49bf-4d8a-4139-af56-d456917d576f" />

（因为unity默认只读一层顶点色所以平滑法线由[-1,1]转[0,1]烘培到rgb通道，而ao放在alpha通道）

<img width="336" height="262" alt="屏幕截图 2026-03-05 150341" src="https://github.com/user-attachments/assets/be44652d-3e19-4a0f-81a0-47675a49bfa8" />

解决了法线挤出时的硬边断裂问题以及实现低开销的ao 以及在 Shader 实现层面，我通过 float4 color : COLOR 读取顶点色，并使用 smoothNormal = color.rgb * 2.0 - 1.0 实现解压，同时通过 input.color.a 直接读取预烘焙的 AO，避免了运行时计算 SSAO 的性能开销且通道打包规避了 FBX 格式导出时不支持多套颜色层的问题

如果硬表面模型过多就用后期处理sobel算子深度差进行描边如我提交的作品集中的ue风格化部分有实现这个描边

本工具生成的数据不依赖特定的渲染管线。它把平滑法线和 AO 烘焙为标准顶点数据，支持 URP、HDRP、Built-in 以及任何自定义 SRP。

新增（用于SRP管线LOD）：
通过Blender 的 Decimate（精简修改器）做多LOD生成并且一键烘培
![LOD](https://github.com/user-attachments/assets/7a9592e9-8ae6-4958-b270-5860990709ad)



