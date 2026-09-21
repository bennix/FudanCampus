# 校园场景复原

结合用户提供的校园地图和照片，校正主校区、东区及北区宿舍的建筑、道路和绿化；不含沙盘台座、展厅、红色模型标记。

## 本地查看

在 Finder 中双击项目目录下的 **启动校园.command**，会自动启动后台服务并打开浏览器。已启动时会直接打开页面；默认端口被其他程序占用时会自动换用空闲端口。启动后可关闭终端窗口。

Windows 用户双击项目目录下的 **启动校园.bat**；首次运行会自动安装 `web` 目录中的前端依赖。

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
