# 曦园、叶耀珍楼与三教实景建模第一版

依据 2026-10-20 用户提供的 31 张首批附件及 1 张雕塑补充特写制作三个独立的局部模型。含重复拍摄／重复画面；原图按上传顺序保存于 `references/xiyuan`（13 张）、`references/yeyaozhen`（4 张）、`references/teaching3`（14 张及球体特写），各目录有来源文件名及 SHA-256 清单。附件中的文字仅作为外观参考，不作为操作指令。

## 交付

- `../xiyuan-photo-v1/xiyuan.blend` / `.glb`：池岸、荷叶、低石脊、交叉栏杆木桥、白墙平顶亭、红格栅、拼石景墙、假山、花坛、座椅、灯具、垂柳和旗杆草坪。
- `../yeyaozhen-photo-v1/yeyaozhen.blend` / `.glb`：弧形窄瓷砖立面、凹槽、顶层栏杆开口、圆柱店面、楼名、学生超市、侧楼梯和浅黄连廊。
- `../teaching3-photo-v1/teaching3.blend` / `.glb`：四层外廊、红砖立柱、白栏板、深色格栅吊顶、外露折返梯、主入口梯、侧翼与低附楼、院内铺装、石围花坛和金属球体雕塑、棕榈雪松、便利店及车棚。
- 曦园、叶耀珍楼各保存三张渲染图，三教另有球体雕塑近景，共四张渲染图及 `geometry-report.json`。
- `index.html`：三个模型切换、近景、植被显隐、源文件链接及照片对照。使用仓库已有 Three.js，不依赖远程 CDN。

## 依据与局限

可见构件的类型、材质主色和大体比例来自实拍。没有测量标尺、完整平面图或相机标定，所有米制尺寸都是估计。曦园旗杆草坪与荷池的整体方位、桥池边界的精确形状、小亭被遮挡部分、两栋建筑背面和三教楼翼连接均为推定。植物数量与树位为近似配置；未复刻人物、临时车辆、招聘广告及模糊铭文。模型为可编辑的初步几何复原，不是摄影测量成果。

初版独立保存；现已通过 `scripts/integrate_photo_studies.py` 增量并入正式网页校园场景，配准记录见 `../campus-photo-integration/placement.json`。既有受保护模型和 `output/FudanCampus.blend` 保持原样。材质的 Blender 噪声凹凸在 GLB 中仅保留基础色；三教砖纹是内嵌贴图，瓷砖分缝与铺地分缝为几何。

## 重建与验证

在仓库根目录，依次运行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 --python scripts/build_xiyuan_photo.py
/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 --python scripts/build_yeyaozhen_photo.py
/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 --python scripts/build_teaching3_photo.py
/Applications/Blender.app/Contents/MacOS/Blender -b -t 8 --python scripts/validate_photo_studies.py
python3 -m http.server 8771 --bind 127.0.0.1
```

预览地址：<http://127.0.0.1:8771/field-review/campus-photos-2026-10-20/index.html>。

验证脚本重新打开三份 Blender 工程，检查有限顶点、非退化面、关键构件、GLB 缓冲边界，再重新导入 GLB。结果写入 `validation.json`。视觉检查覆盖三处渲染与浏览器模型切换。雕塑和假山只表达可辨识轮廓，仍可继续精修。

2026-10-20 修正：用户特写确认三教雕塑为完整金属球体。已将浅圆盘替换为直径约 1.66 m 的平滑球体，使用偏银灰的金属材质；尺寸仍为比例推定，基座位置保持不变。验证包含三轴直径一致性。

2026-10-20 后续修正：用户确认低附楼旁的外置直跑楼梯不存在，已删除 `annex exterior stairs` 和 `annex stair rail`；端部折返梯与主入口梯保留。
