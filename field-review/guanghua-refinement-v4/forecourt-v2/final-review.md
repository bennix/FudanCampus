# 最终续审记录

2026-09-30。按用户要求从既有最终 checkpoint 续审，仅进行铭牌检查、最终渲染与审阅。沿用 `forecourt-complete-v2.blend`；未运行 `build.py`、`finalize.py` 或 `repair_plaque.py`，未重新建模、保存模型或重新导出。

## 中断时已经完成的状态

读取 `.local/forecourt-final.log`、`.local/forecourt-plaque.log`、`.local/forecourt-finish.log`、`.local/forecourt-browser.log` 及两份原验证 JSON：

- `FORECOURT_FINAL_COMPLETE`：完整模型、两种 GLB 与八个视角渲染已生成。
- `PLAQUE_CLEARANCE_REPAIRED`：铭牌与粗石交叠已经修正，雕像两角度已重渲染。
- `FINAL_REOPEN_AND_WEST_URNS_OK`：修正后 checkpoint 已重开，西侧花钵世界坐标保持。
- `FORECOURT_BROWSER_OK`：原审阅页七个视角、树叶开关和窄屏检查通过。

本次再次实际重开最终 blend，74 个受保护对象的几何及变换摘要全部匹配 `build-info.json`；旧 checkpoint、最终 blend、完整 GLB 与雕像 GLB 的 SHA-256 在续审前后全部一致。完整哈希存于 `final-review-validation.json`。

## 铭牌验收

主参考：`references/guanghua_lawn/img/img/IMG_4468.jpeg`；IMG_4467 为相近视角辅助。字序和基座正面的相对位置可以确认，嵌装深度及现场绝对尺寸无法从照片精确量得。

| 检查 | 结果 |
| --- | --- |
| 文字内容 | 繁体“驢背詩思”，左至右顺序正确；已逐字查看正面近景 |
| 文字载体 | 可导出的独立网格，`feature_id=POET_DONKEY` 保留 |
| 字面范围 | 文字处于铭牌水平及垂直边界内 |
| 文字与牌面 | 文字位于牌面前方约 0.003703 个模型单位，未埋入牌面 |
| 粗石与铭牌 | 应用修改器后的粗石全部位于铭牌背后；保守最小间隔约 0.064947 个模型单位，无穿插 |
| 背后石面 | 45 个牌面采样位置沿向后方向均命中基座；距离约 0.078265–0.202496 个模型单位。这验证背后存在石面，不代表牌面与石面贴合 |
| 导出一致性 | 完整 GLB 与雕像 GLB 中的铭牌、文字世界变换及范围均与 blend 一致 |

视觉审阅保留两项明确差异：本版铭牌位于粗石前方，斜视可见间隔，尚不能称为实景嵌装复原；文字在现有光照下偏暗，本版使用略凸的文字网格，不根据照片断言现场凹刻或凸刻深度。这些是现有版本的外观限制，本次不扩展到几何或材质修改。

## 最终渲染和对照

仅补充一个最终批次，使用现有场景、材质和光照，Cycles 64 采样及去噪；临时近景相机只存在于渲染进程，不写回 checkpoint。

- `final-plaque-front.png`：1600 × 1000，正交正面，逐字与牌面边缘核对。
- `final-plaque-oblique.png`：1600 × 1000，斜视，检查石面避让和安装间隔。
- `final-statue.png`：1800 × 1350，沿用 `FC statue photo4468` 原机位，便于与旧雕像图比较。

已有 `after-entry.png`、`after-entry-oblique.png`、`after-entry-top.png`、`after-plaza.png`、`after-edge.png`、`after-statue-side.png` 和 `after-overall.png` 继续覆盖入口对称、曲径退让、铺装、路缘、另一侧和全园位置。本次逐张查看铭牌三张终稿及已有入口、铺装、路缘、雕像另一侧与全园图。新图与导出使用同一份 checkpoint 几何。

入口双花钵等形等高，直路通行带完整；铺装分格连续、路缘分段可辨。雕像大形、帽子、衣袍、低头驴及基座可辨；衣袍厚度、人物细节和石面仍为概括表达，金属表面偏暗，不能称为精确雕塑复制。未拍到的面继续按简化推定处理。

审阅页增加铭牌近景按钮和两张近景，并使用新雕像终稿。网页复核通过：1231 个网格载入、八个视角、铭牌文字网格、树叶开关及 390px 窄屏均正常，14 张对照图全部可加载，无脚本错误和页面横向溢出。实际查看网页铭牌近景，四字可辨且无石面穿插。结果独立记录于 `final-browser-validation.json`，保留原浏览器报告。

## 结论与复现

本轮续审已完成，现有 checkpoint 及两种导出一致，铭牌字序、边界和无穿插检查通过。最终图已产出并查看；牌面嵌装、字面亮度及雕塑细节差异已明确记录。现有比例重建与隐藏面推定的限制仍适用。

若另开一轮外观精修，单一建议目标是铭牌嵌装关系与字面可读性；本次只交付审阅结果，不启动该修改。校园正式资产未在此次续审中更新。

如需复现本次续审，运行 `resume_final_review.py`，再运行 `check-final-review.cjs`。前者只打开完成的 blend，检查并渲染，内部没有保存 blend 或导出调用；后者核验本地 8771 端口的审阅页。不要为续审重新执行建模脚本。
