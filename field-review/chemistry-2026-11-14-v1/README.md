# 55 化学楼：第一轮照片细化

本轮按用户照片要求修改轮廓、屋顶、窗与三处门廊，完成后自动替换网页正式资源。`web-integration-backup` 保留修改前文件；`55-candidate.blend/glb` 为本轮版本，`source` 保存对应几何脚本。

## 修改依据

- `化学楼大致形状-俯拍.png`：H 形主体，西侧中段凹口，正门在南侧中央，右侧门在东侧。修正旧脚本“正门朝东”的误判。
- `化学楼大致形状.png`：中央有抬高段，屋顶为白色。
- `正面.jpg`、`前门拍摄位置-左侧.jpg`、`前门拍摄位置-右侧.jpg`：三层立面、内院返回墙及前门位置。树木遮挡位置按可见的重复开间延续。
- `正面（正门特写）.jpg`：深红砖、深色细窗框、浅色窗间板、平顶方砖雨棚、两侧小柱及门头。
- `背面.jpg`：后门及后立面；`右侧门.jpg` 与曝光版：侧门方砖棚与小柱，缩小旧版过大的侧棚。

所有参考原图均保留在仓库上级 `assets/55-化学楼`；本目录 `references` 为查阅缩略图。原图 SHA256、像素与文件尺寸位于本轮 prompts_log/references.json。

## 推定与限制

沿用原总宽65.6m作为尺度锚点，按俯拍比例推定总深39.2m；中央连接体深13.6m、13m宽的中央段抬高1.8m；西侧凹口深4.6m。屋顶最高14.45m（含压顶），窗宽不超过1.9m、三层，16个墙段共233扇窗。前后棚宽6.8m、东侧棚宽7.2m（原12m）。这些均非实测。

照片中的雨棚是平顶，故用户提示中“塔尖”未解释为尖顶。前门照片能看到穿堂视线；模型留出中央地面通道，但现有网页统一屋顶投影的室内封闭规则仍生效，本轮不承诺可进入化学楼内部。

砖色使用更深、更饱和的红褐色，并生成小幅错缝砖纹贴图及平面UV；不将阴影照片像素直接当作色度实测。渲染为 Blender Cycles CPU 16 samples；未做浏览器GPU截图、真实头显或FPS测量。窗距、遮挡处窗数、凹口深度、门廊尺度和颜色仍由用户视觉验收。

## 验收与复现

在原有 `web` 目录运行 `npm run dev -- --host 127.0.0.1 --port 5173`，使用已有服务器时按其实际地址打开。相机入口：`?view=chemistry`、`?view=chemistry-east`、`?view=chemistry-rear`；刷新页面以清除内存中的旧场景。

使用 `D:/BlenderCLI/blender-4.4.3-windows-x64/blender.exe`：

```powershell
blender -b --factory-startup --python-exit-code 1 --python field-review/chemistry-2026-11-14-v1/build_review.py
python field-review/chemistry-2026-11-14-v1/integrate_web.py
blender -b --factory-startup --python-exit-code 1 --python scripts/build_lods.py -- buildings-55
node web/build-walk-collision.mjs
python scripts/union_walk_interiors.py
python field-review/chemistry-2026-11-14-v1/verify_web_integration.py
python scripts/validate_modular.py
node --experimental-strip-types --test web/tests/lod-*.test.mjs web/tests/walk.test.mjs
npm --prefix web run build:pages
```

Node路径、UTF8与Shapely环境沿用项目环境说明。只构建55的LOD，不执行全量校园构建。导出前后执行空间射线，检测凹口、屋顶高度/白色、每面窗的外部可见性及三个门棚；网页校验比较非目标 manifest、所有LOD哈希及化学楼范围外碰撞三角形。
