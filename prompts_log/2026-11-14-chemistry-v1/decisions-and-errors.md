# 本轮过程记录

原始用户提示词在 user-prompt.txt，参考图元数据在 references.json。修改计划及推定值在 field-review/chemistry-2026-11-14-v1/plan.md；交付与限制在该目录 README.md。

1. 读取期末论文要求、个人总结、两级AGENTS约定以及55几何入口；确认当前分支 feature/LiZedong-23307130271，开始时仓库干净。
2. 备份55源、GLB、旧overview、两档LOD、manifest、标签及碰撞/室内文件，共13条路径；记录9张参考图。
3. 旧版空间检查在西侧中段命中X=-32.8，未凹进，需求验证失败（baseline-check.txt）。
4. 初次apply_patch同时删除/新增同一路径被拒绝，未写入文件；改用PowerShell UTF8 here-string写入完整几何源。无数据丢失。
5. 第一版候选通过基础空间验证；渲染后修正不对称连接体的门洞偏移：门洞/基座按世界X=0居中，并将前后全景相机后移避免裁掉两翼。
6. 增强逐窗验证后，GLB回读误报玻璃被墙挡住：原测试假定每8个顶点一窗，但导出会因UV/法线拆分重排顶点。修正为检测朝外玻璃面的三角形重心射线，导出前233个玻璃面、回读后466个三角形逐面可见（build-vertex-order-test-error.txt保留报错，build.txt为最终输出）。
7. 只替换55，生成buildings-55三档LOD并更新碰撞与屋顶投影；其他建筑 manifest、199项LOD及范围外碰撞保持不变。Node量化提示UV不在[0,1]而跳过UV量化：砖纹有意平铺，保留原UV属预期，不是贴图丢失。
8. 沙箱内Node测试子进程 spawn EPERM（tests.txt）；经工具自动审批在沙箱外重跑，21项通过（tests-unsandboxed.txt）。
9. 首次完整构建被光华楼旧快照对55模型的历史哈希锁阻止（build-pages-old-snapshot-error.txt）。保留原报告和快照，只将55转入独立化学楼校验；其他历史资产哈希检查保留。
10. 完整构建通过，Vite既有大chunk警告保留；HTTP实际下载三档模型确认hash/bytes（http-check.txt）。
11. 将同材质重复几何合批，保留16个墙段窗玻璃和3个门棚的检查元数据，减少网格数；最终统计与重复验证结果见statistics.json和本轮输出。

未验证：真实测量尺寸、遮挡区域精确窗数、浏览器GPU和头显效果、FPS、人工工时节省。不得在论文中将推定值/自动检查写成实测或用户已验收。

12. 日志同步首次使用相对Path的parent，误将源/目标指向同一目录，被Windows共享锁拒绝；改用绝对工作区路径复制，原日志内容完好。
13. 最终合批31个网格、52428三角形；重新通过逐窗GLB回读、3档HTTP、范围保护、21测试及完整构建。
