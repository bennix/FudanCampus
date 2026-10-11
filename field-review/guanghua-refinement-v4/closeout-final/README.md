# 光华楼前总场景：实施与交付

本目录以已接受的 [v7 统一基线](../scene-closeout-v7/guanghua-unified-closeout-v7.blend) 为起点，顺序实施结构、植物与细部、材料光照、GLB 优化和本地校园接入。原 v7 不覆盖；其它校园资产及原有未提交工作按差异/哈希保护。

**当前实际验收状态以 [交付门槛报告](delivery-validation.json) 和 [单一审阅页](review.html) 为准。** 文件存在、导出成功或部分正式图生成不自动表示全部完成；用户视觉认可单独记录。

- [可编辑总场景](guanghua-closeout-final.blend)，[结构检查点](guanghua-closeout-structure.blend)。
- [优化景观 GLB](guanghua-closeout-optimized.glb)，[校园楼体 GLB](guanghua-building-27.glb)，[旧园区外植被裁切派生资产](05-guanghua-closeout.glb)。
- [C01–C18 完成矩阵](completion-matrix.md)，[推定与未知](uncertainty.md)，[版本/哈希](version-manifest.json)。
- [原生重开、实体、字体及接口量检](native-validation.json)，[机位与锚点](camera-validation.json)，[正式图及相机清单](final-render-manifest.json)。
- [生产 GLB 检查](glb-validation.json)，[本地校园接入](integration.json)，[最终性能](final-performance.json)，[同设备基线](baseline-performance.json)，[网页检查与构建](web-checks.json)。

审阅页必须经工作区根目录 HTTP 服务打开，才能正确读取原始照片。参考照片使用 `../../../references/guanghua_lawn/img/img/IMG_####.jpeg`；原照片不改写，不另外冒充现场测量。

[静态审阅页布局与请求检查](review-page-validation.json) 单独记录 1440×1000 桌面与 390×844 窄屏、全图加载及页面 SHA。它不会打开 3D 校园，也不替代实际校园的帧率/文字验收。

## 单一复现入口

在工作区根目录运行 [run_closeout.ps1](run_closeout.ps1)。默认 `Verify` 只重跑量检、网页构建和性能，不重新保存原生模型。实际运行需要已配置的本地 Blender、road-venv Python、Node、浏览器和 npm 依赖；缺失时直接报错，不自动安装。

```powershell
# 刷新文档与审阅页。证据缺失时保留候选状态。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode Review

# 全部证据同源且满足交付门槛才返回成功。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode Review -Strict

# 重跑原生、GLB/校园、构建、实际浏览器及性能检查。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode Verify

# 只补正式图；同源已完成的图会保留，其余按固定机位续跑。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode Render

# 从当前源导出并切换本地光华资产，随后完整网页验证。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode Export

# 从受保护 v7 顺序重建候选、重渲染并重导出/接入。
# 会更新本目录候选与本地校园光华资产；历史基线保留。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode Full

# 启动仅供本机审阅的工作区 HTTP 服务。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode ServeReview

# 静态审阅页检查：需已有上面的本机审阅服务，且其它压测结束。
& .\field-review\guanghua-refinement-v4\closeout-final\run_closeout.ps1 -Mode Review -CheckReviewPage
```

本地校园为 [http://localhost:5188/](http://localhost:5188/)，审阅页为 [本机审阅地址](http://127.0.0.1:8766/field-review/guanghua-refinement-v4/closeout-final/review.html)。`Verify`/`Export`/`Full` 会在校园服务未运行时启动隐藏服务窗口；`ServeReview` 在本机 8766 端口服务工作区文件。停止服务可关闭对应进程；入口不删除文件。

完整重建依次执行：`audit_baseline.py`、`extract_structure.py`、`prepare_planters.py`、`prepare_structures.py`、`assemble.py`、`finish.py`、`finish_surfaces.py`、`repair_shared_foliage.py`、`refine_canopy.py`、`repair_ground.py`。独立原生复核修复随后按精确顺序执行：Blender `extract_native_audit_geometry.py` → Python `prepare_ground_trim.py --padding 0` → Blender `repair_native_audit.py` → Python `prepare_ground_trim.py --padding 0.00002` → Blender `repair_ground_trim_boundary.py` → Python `verify_ground_trim.py`。第二次准备继续用第一次的原始几何提取，绑定当时当前模型 SHA，只修浮点切口边界，不重复植物编辑。

随后执行 `fit_camera.py`、`camera_validate.py` 与 `audit_native.py`。正式图由 `render.py -- final` 生成；独立导出进程执行 `export_web.py`、`optimize.mjs`、`trim_forest.mjs`，通过明确的 `--source`/`--report-dir` 接入脚本切换本地资产。入口不运行全量 `export_modular.py`。

全重建保存后的二进制源 SHA 可能改变，旧视觉结论不会自动绑定到新源。内部审阅必须核对新正式图和差异后更新与源 SHA 绑定的 `visual-review.json`；`build_review.py` 不会伪造逐项通过。`Full` 默认可生成诚实候选报告；`-Strict` 只在全部证据齐全时成功。入口不会修改 `current-scene.json`，不会提交、推送、发布或清理。[activate_delivery.py](activate_delivery.py) 是单独的受门槛保护激活步骤，仅在 Strict 全部门槛通过后切换当前场景；不属于复现入口的默认动作。

## 判定规则

`build_review.py` 直接计算当前模型、原 v7 与正式图 SHA，核对原生、机位、GLB、导出、接入、性能、网页和内部视觉记录是否属于同一源。18 张主图和 11 张必要局部必须齐全，达到 1800px 长边、40–64 采样，并含相机矩阵与图像 SHA。任一过期图、缺图、缺报告或失败门槛都会保持待验收。

另外用 `render.py -- canopy-before` 从受保护 v7 生成四张 900px/12 采样基线图（西平台、东林下、东出口、南路），使用当前相机。审阅页逐一核对相机矩阵、焦距、画幅比例和显隐后，才标记为原生模型同机位前后；分辨率/采样差异明确标注。四组对照也属于 Strict 必需证据，但不冒充与现场照片的测量匹配。

性能按本机 Chrome 1920×1080、DPR=1、同一设备/相机/叶开关、每机位 10 秒对比，检查中位 ≥30 fps、p95 ≤50ms、两处总览 ≤300 万三角面、楼前近景 ≤600 万、同设备中位帧时回退 ≤20%及新增资产 ≤150 MiB。draw calls ≤500 目标单独报告；实际得分见原始记录。本机回环加载不代表公网速度，390px 布局检查不代表真实手机性能。

性能检查按顺序运行，期间保持模型/资产冻结并结束其它渲染或浏览器压测；`--frozen` 是该条件的记录，不会自动隔离显卡。完整重建中的正式渲染结束后才进入网页压测。

西坛四个近似底座锚点有局部拟合记录，其余机位为人工近似。乔木和灌木覆盖率没有在全面可靠匹配机位下认证，不制造覆盖率统计。绝对尺度、现场标高、精确树位/株数/杉种、隐藏结构、地下空间及 ESKY_N 准确位置仍保持推定或未知。全部证据边界见 [uncertainty.md](uncertainty.md)。
