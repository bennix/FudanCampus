# 车库文字导出修复

修正西入口 v3、植被 v2 的独立 GLB：两处“光华楼广场自行车库”及 FUDAN 原来是 Blender FONT 对象，被仅选择 MESH 的导出流程漏掉。导出时从字体生成临时网格，保留名称、世界变换、材质及 feature_id，导出后清理临时对象；原始 .blend 的 SHA-256 保持一致，文字仍可编辑。

| 导出 | 原大小 | 修正后 | 已有网格比对 |
| --- | ---: | ---: | --- |
| ../west-entry-v3/west-entry-aligned-v3.glb | 200,891,228 字节 | 204,759,944 字节 | 1084 个保持 |
| ../vegetation-v2/vegetation-v2.glb | 161,148,064 字节 | 165,016,180 字节 | 见 vegetation-v2.json |

每份导出增加 3 个文字网格，约 3.87 MB。所有原有网格的位置、旋转、缩放、属性数据、索引、材质和 metadata 完整比对通过；原有嵌入纹理逐张内容哈希一致。修正文件经 Blender 重新导入，三处文字均为非空网格，包围盒与源场景的差异小于 0.001。

两份原审阅页均加入“车库一文字”“车库二文字”“FUDAN”近景按钮，并更新模型缓存版本。本地浏览器已实际查看全部六个近景：两处中文标牌完整可读、FUDAN 正常显示，控制台无错误。截图为本目录的六份 JPG，浏览器记录见 browser-validation.json；各导出文件及源文件哈希见 west-entry-v3.json、vegetation-v2.json。

从仓库根目录运行已有 Blender：`blender -b --python scripts/repair_garage_text_exports.py`。两版原生成脚本也已接入 scripts/export_visible_glb.py，后续生成时会包含 FONT 对象。此修复只更新两份独立 GLB 与相关导出/审阅记录，未更新校园正式清单，未提交或推送 Git。

先前各版本的 validation.json、browser-validation.json 及渲染图保留为当时的检查记录；修正后的 GLB 大小、哈希和文字显示以本目录为准。
