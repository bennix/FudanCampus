# 化学楼砖色校正与提交记录

用户认可前轮几何，指定sRGB #D46B57并要求git add/commit；原话见user-prompt.txt。

- 修改前备份13条正式资源路径及前轮渲染，未覆盖前轮历史。
- 直接解码旧GLB嵌入PNG，代表砖色样本为RGB(86,24,13)，说明此前写入纹理的浮点数偏小。
- 使用用户指定sRGB值(212,107,87)生成砖纹，细微颗粒约±2/255；材质无纹理时常量正确转换到线性。保留已有方砖缝和几何。
- verify_color.py确认导出砖面中位色准确为#D46B57，90%以上像素距目标不超过3/255，baseColorFactor中性。
- 初次几何缓冲比较假定PNG大小变化不会影响byteOffset而失败；修正为分别按新/旧bufferView偏移读取字节，再比较原始几何数据。节点、网格、accessor定义和几何字节均保持一致。报错保存在color-check-offset-assumption-error.txt。
- Blender 4.4.3空间检查与GLB回读通过；仅重建buildings-55三档LOD，同步manifest及碰撞。集成校验确保所有非55 LOD/模块以及范围外碰撞保持不变。
- Node 21项测试、完整build:pages、HTTP实际三档资源hash/bytes验证，详见对应输出。构建保留既有大JS chunk提示。
- 恢复构建自动重写的两个非目标光华楼报告的原始CRLF，确认规范化内容与HEAD相同。
- 本地提交包含化学楼两轮建模、网页接入、备份、比较渲染与原始prompts。忽略__pycache__、.blend1和本地依赖/构建缓存；不推送。

未实测真实尺寸、GPU/头显画面和FPS。#D46B57是sRGB砖面底色，最终屏幕颜色仍受照明/色调映射影响。
