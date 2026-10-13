# 西出口道路生成小样

**用户复核已指出：当前横向交汇、弯道走向与 IMG_4568 不符。这个小样不能作为后续形态基线。下一轮按 [照片空间形态修订计划](../shape-first-revision-plan.md) 执行，不再优先扩展工程实现。**

**当前状态：生成器测试和局部道路网格检查通过；场地剖面与肩部形态未通过验收。不得作为最终模型或继续全场铺开的基线。**

查看 [图像与剖面对照](review.html)。当前技术小样是 [diagnostic-03/west-exit-study.blend](diagnostic-03/west-exit-study.blend)，从 stage01 生成，没有覆盖原文件。

## 已完成

- 独立环境中固定 Shapely 2.1.2 / NumPy 2.3.4；实际 GEOS 与 Python 版本在 `road-generation-config.json` 中。
- 纯二维几何模块 `road_geometry.py`，负责声明连通关系、轮廓合并、约束三角化、共边细分、网格检查和统一加厚。
- 10 项代表性测试通过：直路、弯道、T/Y 分叉、变宽、带岛孔洞、不连通近邻、禁止未登记同层交叉、坡道平台、梯脚接口。
- `sample-settings.json` 集中保存路宽、节点高度、过渡范围和接口位置。`road-network.json` 保留来源和推定状态；旧坐标仍不是测量值。
- 当前小样路面为 1 个连通表面，无重复面、退化面、内部开放边；实体闭合正体积。路面与地形只在 2e-5 模型米数值精度带内有微小序列化误差，带外没有面积重叠。
- 草坪、ETERR、ESKY、楼梯等非 EPATH 对象几何与材质一致；小样范围外剩余 EPATH 顶点一致。原始模型、305 张照片和已有 GLB 合计 336 个保护文件哈希一致。
- Blender 保存后重新打开成功；本轮没有导出 GLB。

## 未解决

- 当前测试配置主路最大纵坡约 21.3%，短连接段约 58.7%。这些是测试模型的数值，不是实景测量。既有梯脚高度、平台高差、连接距离与剖面插值都需要重新核对，不能单凭调整材质验收。
- 肩部存在陡坎和分片感；草坪连接支路的部分表面也有可见分片感，尚未精修。纯色图保留展示这些问题。
- 路网节点关系、绝对宽度与位置仍有推定。删除旧重叠绕行支路是本次假设，不能当作已经确认的精确现场路线。
- 北出口及其余东花园、所有西花园道路仍未使用此生成器重建；其他旧道路缺陷未宣称修复。

## 批次

- diagnostic-01：rejected。交叉处过宽，地形保护漏掉楼梯洞口内部。
- diagnostic-02：superseded。修正过宽和洞口占用，但沿用的草坪直道接口仍有旧高差。
- diagnostic-03：technical-sample-only。接口同高、连续道路网格可检查；现场剖面与肩部仍不通过。

每批保留自己的图像和模型。没有正式 candidate；不把技术小样标为整体精修完成。

## 复现

从仓库根目录运行；运行环境在 `.local/road-venv`。生成目录名必须是新名称。

```powershell
.local\road-venv\Scripts\python.exe field-review\guanghua-refinement-v4\road-rebuild-v1\test_road_geometry.py
.local\road-venv\Scripts\python.exe field-review\guanghua-refinement-v4\road-rebuild-v1\prepare_west_sample.py NEW_BATCH
.local\road-venv\Scripts\python.exe field-review\guanghua-refinement-v4\road-rebuild-v1\validate_roads.py NEW_BATCH
& .local\blender-runtime\blender-4.4.3-windows-x64\blender.exe -b --python field-review\guanghua-refinement-v4\road-rebuild-v1\build_roads_blender.py -- NEW_BATCH
```

下一单一目标：利用现有照片复核 ETERR 上平台—西侧短梯—采光顶基座—花园地面的相对高差，重新确定剖面约束，再用同一生成器更新小样。暂不增加树木、铺装细节或其他区域。
