# 实景模型并入复旦校园

已将曦园、叶耀珍楼、第三教学楼并入正式校园网页场景。左侧新增三个区域及三教金属球近景，可随时返回全校鸟瞰。

三教沿用 60 号地图锚点，庭院铺装在二教边界前截断；用户否定的附楼外置直跑梯和扶手已删除，端部折返梯及主入口梯保留。叶耀珍楼沿用 75 号锚点，门前铺装不覆盖南侧道路。曦园保留 68 号地标，将池塘、亭、桥、草坪及植被置入对应街区。三教雕塑在建筑平面缩放后仍保持三轴等径。

尺寸、背面和局部连接关系依据照片推定，非测绘精度。变换记录见 `placement.json`。独立 Blender 文件继续保留；本次更新完整校园网页场景，未覆盖旧 `output/FudanCampus.blend`。

## 增量交付与验证

`manifest-before.json` 和 `lod-before.json` 保存前置清单；`cleanup.json` 记录占位模型、对应细节及冲突植被的移除。派生资源另存为 `-photo.glb`，原始文件和既有精修建筑保持不变。

新模型分为建筑主体、铺装和植被，并生成远／中／近三级资源。远景总计 41,482,760 字节、2,385,148 三角面，低于现有 45 MB／250 万预算。

校验包含保护哈希、全部既有模型、增量替换、GLB 载入、LOD 预算、球体等径、错误楼梯不存在、TypeScript 编译及 14 项 LOD 测试。网页实查截图保存在本目录。

## 重建

仓库根目录执行：

```sh
node web/integrate-photo-cleanup.mjs
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/integrate_photo_studies.py
node web/pack-photo-integration.mjs
python3 scripts/validate_modular.py
python3 scripts/validate_lods.py
node web/validate-photo-integration.mjs
npm --prefix web run build:pages
```

清理脚本基于此批次固定前置快照。未来出现其他模型更新时，必须先合并快照差异，不能用旧快照覆盖新清单。

## 室外步行

首页提供步行模式，WASD／方向键移动、拖动看向、Shift 快走、Esc 恢复观察视角；触屏可长按方向按钮。道路、草地、广场和露天庭院可自由通行。固定碰撞网格不随视觉 LOD 切换，胶囊碰撞体及分步移动阻止穿墙；建筑屋顶投影封闭室内入口，保留露天庭院孔洞。

`web/build-walk-collision.mjs` 从当前远景资源提取实体表面，排除已隐藏的旧建筑；`scripts/union_walk_interiors.py`（需要 Shapely）合并建筑投影。修改模型后须重新生成这两项数据。构建时校验源版本及碰撞哈希。5 项步行测试覆盖开放区域、庭院、薄墙持续冲撞、开放门口禁入和校园实际落脚点；浏览器验证曦园、三教步行与退出，截图见 `walk-*.png`。
