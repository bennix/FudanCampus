# 校园场景复原

## 毛主席像（58 号）

人物已替换为 [1821427398 的「毛主席雕塑像」](https://sketchfab.com/3d-models/ef18c25e1e094cf99e2b377ad7377d05)（CC BY 4.0）。保留现有基座、铭牌和地图位置，裁去下载模型自带的小基座并统一缩放、调整石材材质。该模型源自重庆大学雕像，作为外形近似替代；网页提供模型署名链接。原文件及许可说明位于 `assets/landmarks/sources/`。

- 独立源文件：`assets/landmarks/58.blend`；造型脚本：`scripts/statue_geometry.py`。
- 网页模型：`web/public/models/shared/58.glb`，保留独立地标编号。
- 仅重做雕像与网页引用：`blender -b --python scripts/update_statue.py`。
- 将单体同步进现有完整校园工程：`blender -b output/FudanCampus.blend --python scripts/integrate_statue.py`。仅替换 58 号雕像，不重新生成其他楼栋。

结合用户提供的校园地图和照片，校正主校区、东区及北区宿舍的建筑、道路和绿化；不含沙盘台座、展厅、红色模型标记。

## 本地查看

在线地址：https://bennix.github.io/FudanCampus/ 。GitHub Pages 免费托管，推送到 `main` 后由 GitHub Actions 自动部署。在线版使用 `web` 下的 `npm run build:pages` 生成纯静态网页，复用相同的校园组件、模型与实景图片；本地启动方式保持不变。

在 Finder 中双击项目目录下的 **启动校园.command**，会自动启动后台服务并打开浏览器。已启动时会直接打开页面；默认端口被其他程序占用时会自动换用空闲端口。启动后可关闭终端窗口。

也可以手动运行：

```sh
cd /Users/zhipingxu/FudanCampus/web
npm run dev -- --host 127.0.0.1 --port 5173
```

打开 http://localhost:5173 。所有模型和前端依赖均在本地，无需外部 CDN。左键旋转、右键平移、滚轮缩放，支持校园总览、地图俯视与重点建筑近景等预设视角、建筑浮动标签、树木开关、自动环绕，以及地图／照片对照。

## 建筑标签

149 栋建筑各有一个标签，另有 10 个庭院、校门等地标标签。自动详略模式在远景显示编号、近景显示名称；悬停显示名称，点击标签靠近建筑。可选“全部名称”或关闭。N / A 编号是为了唯一标识地图中原编号不清或未标名的楼栋，不代表校方正式编号。

## 文件

- `output/FudanCampus.blend`：按区域组织的可编辑 Blender 工程。
- `output/campus_aerial.png`：鸟瞰渲染。
- `web/public/campus.glb`：网页所用三维模型。
- `references/buildings.json`：地图描摹建筑坐标、名称、近似层数和形体。
- `web/public/buildings.json`：网页浮动标签与三维锚点。
- `output/campus_plan.png`：地图方向俯视渲染。
- `output/photo-version/FudanCampus.blend`：修改前的照片版备份。
- `scripts/build_campus.py`：完整程序化建模、渲染及导出脚本。

重新生成：
```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 --python scripts/build_campus.py
```

使用 Blender 4.4.3 CLI 建模与渲染，通过 Blender MCP 加载与检查场景。建筑平面按附图描摹简化，名称沿用地图标注时期；层数、屋顶和立面仍为近似推定，未使用测绘资料，不能作为精确建筑或规划依据。GLB 保留基础材质，Blender 程序纹理不在网页中完整呈现。

修改地图数据后先运行 `python3 scripts/map_data.py` 再重建模型。运行 `python3 scripts/validate_map.py` 检查建筑与标签完整对应关系。

## 逸夫建筑外观细化

- 16 号逸夫楼：依据两张实景照片，细化错落楼体、圆弧红褐色竖塔、窗带、入口雨棚及弧形附楼。
- 14 号逸夫科技楼：依据实景照片，细化高低塔楼、红砖竖塔、玻璃门厅与大挑檐附馆。
- 两栋建筑在地图中的位置与各自标签保持对应，背面未见部分仍为近似补全。
- `scripts/yifu_geometry.py`、`scripts/yifu_science_geometry.py` 保存独立造型逻辑。
- `output/yifu_detail.png`、`output/yifu_science_detail.png` 为近景渲染。

## 光华楼与理科图书馆

- 27 号光华楼：按正面照片重建对称双塔、蓝色幕墙、顶部柱廊、中央连接楼、裙楼与入口阶梯。尺寸依校园地图相对比例推定。
- 56 号理科图书馆：仅按局部照片细化北侧连接楼面向院内的入口立面，保留地图 U 形轮廓；照片未覆盖的侧翼与背面仍为推定。
- 网页中的对应近景和实景对照可用于查看。造型脚本为 `scripts/guanghua_geometry.py` 与 `scripts/library_geometry.py`。

## 校门实景细化

按用户照片建立红砖墙、白色平檐、砖柱、红色校名、白色花格及打开的黑色铁门；暂放置于地图 65 号正门位置。校名使用字体近似表达，并非原题字描摹。网页可切换「复旦校门」近景和校门实景对照。造型脚本：`scripts/gate_geometry.py`；渲染：`output/fudan_gate_detail.png`。

## 多人协作：分栋模型

网页读取 `web/public/campus-manifest.json`，首屏加载 6 个公共／分区 GLB 和 8 个简化建筑模型，距建筑 240 米内加载完整单体。完整单体加载成功后替换简化模型；失败时保留简化模型。标签沿用原建筑编号。正门朝外仍为正南。

| 编号 | 建筑 | 独立造型脚本 |
|---|---|---|
| 14 | 逸夫科技楼 | `scripts/yifu_science_geometry.py` |
| 16 | 逸夫楼 | `scripts/yifu_geometry.py` |
| 20 | 恒隆物理楼 | `scripts/physics_geometry.py` |
| 27 | 光华楼 | `scripts/guanghua_geometry.py` |
| 51 | 综合办公楼 | `scripts/office_geometry.py` |
| 55 | 化学楼 | `scripts/chemistry_geometry.py` |
| 56 | 理科图书馆 | `scripts/library_geometry.py` |
| 65 | 复旦正门 | `scripts/gate_geometry.py` |

每栋可编辑文件是 `assets/buildings/<编号>.blend`，完整 GLB 是 `web/public/models/buildings/<编号>.glb`，简化模型是 `web/public/models/overview/<编号>.glb`。模型使用本地坐标，朝向已烘焙；清单中的 `position` 将其放回校园，`rotation` 为零，不要再次应用地图角度。公共地形、道路、树木和普通楼栋按区域保存在 `web/public/models/shared/`。

协作者可直接编辑并保存自己的单栋 Blender 文件，然后只导出这一栋，例如：

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b assets/buildings/16.blend -t 8 --python scripts/export_modular.py -- --building 16
```

提交该栋 `.blend`、完整／简化 GLB 与清单里该编号的变化即可。清单的内容哈希用于缓存更新；GLB 二进制不做文本合并，同一栋建筑尽量指定一位负责人。标签与实景图片仍在现有网页逻辑中维护。

程序化建模者可以修改对应造型脚本，再运行完整重建：

```sh
RENDER_VIEWS=none /Applications/Blender.app/Contents/MacOS/Blender -b -t 8 --python scripts/build_campus.py
```

**完整重建会重新生成八栋 `.blend`、所有模块和清单，覆盖手工编辑的单栋文件。** 合并手工造型前不要运行完整重建；需先决定以脚本还是手工 `.blend` 为该栋的造型来源。`output/FudanCampus.blend` 是完整重建的组合场景；单栋导出不会同步修改它。原 `campus.glb` 保留为历史兼容文件，网页不再请求它；仅设置 `EXPORT_LEGACY=1` 完整重建时才更新。

验证：`python3 scripts/validate_modular.py`、`node web/validate-models.mjs`，以及在 `web/` 下运行 `npx tsc --noEmit` 和 `npm run build:pages`。

## 浏览器分级显示（LOD）

桌面与移动浏览器统一使用远、中、近三档模型。首屏仅加载 15 个轻量总览资源（约 2.51 MB、40,280 个三角面）；靠近后按距离和面数预算加载细节，远离时恢复总览并释放细节几何、材质与贴图。切换边界保留 25% 缓冲区，快速跳转取消过期请求；失败保留现有模型并延迟重试。

自动适配根据粗指针和 CPU 核数选择省电档，也可手动选择省电或高画质。省电档总可见几何预算 22 万三角面、单个细节不超过 10 万面、最多 3 个细节和 1 个并发请求，像素比最高 1.25、30 FPS 上限、关闭阴影。桌面高画质预算 200 万面、最多 6 个细节和 2 个并发请求，60 FPS 上限、2048 阴影。静止时不重复渲染，后台标签页暂停渲染。预算不包含升级过程中短暂共存的旧模型和解析缓冲；这不是实际手机帧率保证。

源模型更新后重建 LOD，再发布（构建前自动校验源版本与资源哈希，防止发布过期模型）：

```sh
blender -b --python scripts/build_lods.py
# 只更新雕像时：
blender -b --python scripts/build_lods.py -- shared-58
python3 scripts/validate_lods.py
cd web && npm run test:lod && npm run build:pages
```

运行时清单：`web/public/campus-lod.json`；源模型清单仍为 `campus-manifest.json`。原始精度资源保留，LOD 是可重复生成的派生资源。
