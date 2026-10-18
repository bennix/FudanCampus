"""Build the delivery page from actual reports; never infer acceptance from file existence.

Run with Python 3.10+ (no third-party dependency). The default preserves an honest
draft when evidence is incomplete. --strict exits nonzero unless every required
delivery gate and the internal visual review pass for the current source SHA.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "guanghua-closeout-final.blend"
BASELINE = HERE.parent / "scene-closeout-v7/guanghua-unified-closeout-v7.blend"
BASELINE_SHA = "641a3ab8f02443ef98ce1bc2dcb2e8a6fdb63ba194dd6fffbec7a92aeeb146a2"
MAIN = [
    ("overall", "全场景总览", None), ("top", "全场景俯视", None),
    ("west-platform", "西平台", 4390), ("east-understory", "东园林下", 4582),
    ("east-exit", "东高台出口", 4568), ("south-walk", "南侧向西沿路", 4597),
    ("west-planter", "楼前西坛", 4464), ("east-planter", "楼前东坛", 4485),
    ("planter-top", "双坛无遮挡俯视", None), ("plinth-junction", "西坛底座接头与坡道", 4464),
    ("garage-wb1", "WB1 开放车库", 4416), ("garage-wb2", "WB2 关闭车库", 4424),
    ("corridor-junction", "东直通道与广场接口", 4493),
    ("plaque-front", "铭牌正面", 4468), ("plaque-oblique", "铭牌斜面", 4468),
    ("fudan", "FUDAN 与橙色爱心", 4603), ("pergola-seat", "藤架与环树座椅", 4547),
    ("skylight-opening", "采光顶与开口结构", 4357),
]
LOCAL = [
    ("east-road-top", "东园道路无遮挡俯视", None),
    ("east-road-side", "东园道路无遮挡侧视", None),
    ("mouth-w-n", "西北楼梯口 WOPEN", 4453),
    ("mouth-w-s", "西中楼梯口 WOPEN_S", 4357),
    ("mouth-e-n", "东中楼梯口 EOPEN", 4505),
    ("mouth-e-s", "东北楼梯口 EOPEN_S", 4492),
    ("leaf-detail", "近景叶形与枝叶连接", 4582),
    ("flower-detail", "花钵与红花", 4464),
    ("sculpture-side", "人物与驴侧面", 4467),
    ("foyer-detail", "门厅入口与柱框", 4485),
    ("pergola-structure", "藤架去叶梁柱与支脚", 4547),
]
TASKS = [
    ("C01", "照片、机位与证据", "西坛四个近似花钵底座锚点拟合；其余机位采用人工近似。", "camera-validation.json", "西坛局部拟合不证明全立面或植物覆盖一致。"),
    ("C02", "楼体与门厅", "45 组可见前柱改为凹槽圆柱与柱头；其它窗轴、开口及楼体相对定位保留。", "surface-validation.json", "继承比例与柱头雕刻为概括表达；需正面/斜视核验。"),
    ("C03", "楼前双坛、坡道与底座", "左右独立轮廓、低弧过渡、压顶、种植面及分离花钵底座重建。", "structure-validation.json", "曲率、局部标高与绝对尺度为推定。"),
    ("C04", "东高台出口与独立高程道路", "重建先前进再转向的连续园路，共用边界高程，扣除原楼梯口及旧园地重复投影。", "ground-trim-planar-validation.json", "高程为推定；实际射线和投影检查只认证所列对象/采样。"),
    ("C05", "直通道与硬景接口", "200 件原直通道实体保留，重新检查 241 点广场接口及 241 点园路边界。", "native-junction-probes.json", "设计板缝/台阶除外，不等于全场无碰撞认证。"),
    ("C06", "花园乔木", "沿 v6 修冠形、枝叶渐变、层次与透空；保留可见稀冠关系。", "canopy-contact-validation.json", "机位未全面匹配；没有伪造乔木覆盖率差统计。"),
    ("C07", "南路阔叶与杉类", "保留 16 株南路阔叶与 4 株推定杉类，修叶面积、窄冠与混植节奏。", "canopy-contact-validation.json", "精确树种、株数/树位及背冠结构推定。"),
    ("C08", "灌木、绿篱与近景叶", "18 个共享叶片原型只变形一次；修短圆叶、非对称冠面、枝叶附着和东园路避让。", "shared-foliage-repair.json", "没有可靠机位下的独立灌木覆盖统计；由局部图逐项审查。"),
    ("C09", "招牌与三处可编辑字体", "调整两处蓝底黄字的字幅、字距及厚度；两中文和 FUDAN 保留原生 FONT 并导出非空网格。", "glb-validation.json", "字体、范围、实际网页三处查看须与正式图共同核验。"),
    ("C10", "两处车库门、坡面与环境", "保留 WB1 开门、WB2 关闭门组与管道/格栅/通风构件，核验外部接续。", "native-validation.json", "地下空间和照片之外的隐藏构造未知。"),
    ("C11", "铺装与石材", "保留既有铺装方向及直通道浅槽；重建石材采用场景尺度 UV 和细微矿物粗糙度。", "surface-validation.json", "细缝/磨损尺度推定；原生程序微起伏不完整转入 GLB。"),
    ("C12", "园地与树根接地", "在可见树根周围加入小范围裸土及少量落叶，避开硬景并投影到实际园地。", "surface-validation.json", "落叶分布推定，地下根系未知。"),
    ("C13", "采光顶、栏杆与四个楼梯口", "核验既有顶、框架与四口，修玻璃响应及新园地扣口；保留四口原构件。", "glb-validation.json", "ESKY_N 存在有照片证据，但准确位置仍未知，未凭对称补造。"),
    ("C14", "藤架、座椅与花钵", "以连续藤茎和附着叶替换球团，保留梁柱/环树座椅关系，补可见红花。", "finish-validation.json", "隐蔽连接与局部尺寸推定，去叶及局部图需共同核验。"),
    ("C15", "雕塑铭牌与其它标识", "保持“驢背詩思”字序，补背部安装石材、修文字亮度和金属；保留 FUDAN/爱心组合。", "glb-validation.json", "未拍雕塑细节继续概括表达；安装厚度推定。"),
    ("C16", "材料与光照", "统一 AgX、曝光与正式渲染设置；网页记录材质转换、叶片遮罩和玻璃响应。", "export-conversion.json", "Blender 与网页光照系统不同；材质一致性按可见色区/轮廓审查。"),
    ("C17", "GLB、性能与校园接入", "近中远三级植物、共享原型与网页合批；新本地资产替换光华区域并裁除旧植被重叠。", "final-performance.json", "本机回环 HTTP 成绩不代表公网下载或真实手机帧率。"),
    ("C18", "正式图与全项交付", "同一最终源生成 18 主图、11 局部、GLB、网页与复现清单；通过前维持待验收状态。", "delivery-validation.json", "内部核验不自动代表用户视觉认可。"),
]
REPORT_NAMES = ["native-validation.json", "independent-native-repair.json", "ground-trim-planar-validation.json", "camera-validation.json", "glb-validation.json", "final-performance.json", "baseline-performance.json", "final-render-manifest.json", "canopy-before-render-manifest.json", "web-checks.json", "decoded-reimport-check.json", "decoded-reimport-reference.json", "export-conversion.json", "integration.json", "visual-review.json", "glb-metrics.json", "forest-boundary-trim.json", "structure-validation.json", "surface-validation.json", "canopy-contact-validation.json", "shared-foliage-repair.json", "finish-validation.json"]

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read(name: str, default=None):
    p = HERE / name
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return default

def number(value, digits=1):
    return f"{value:,.{digits}f}" if isinstance(value, (int, float)) else "待记录"

def esc(value):
    return html.escape(str(value), quote=True)

def link(name, label=None):
    return f'<a href="{esc(name)}">{esc(label or name)}</a>' if (HERE / name).exists() else f'{esc(label or name)}（待生成）'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--campus-url", default="http://localhost:5188/")
    parser.add_argument("--date", default="2026-10-01")
    args = parser.parse_args()
    source_sha = sha(SOURCE) if SOURCE.exists() else None
    data = {name: read(name) for name in REPORT_NAMES}
    native = data["native-validation.json"] or {}
    camera = data["camera-validation.json"] or {}
    glb = data["glb-validation.json"] or {}
    perf = data["final-performance.json"] or {}
    baseline_perf = data["baseline-performance.json"] or {}
    web = data["web-checks.json"] or {}
    visual = data["visual-review.json"] or {}
    rows = data["final-render-manifest.json"] or []
    if isinstance(rows, dict):
        rows = rows.get("renders", rows.get("views", []))
    valid_renders, render_issues = {}, []
    for row in rows:
        path = HERE / row.get("image", "__missing")
        reasons = []
        if row.get("source_sha256") != source_sha: reasons.append("源 SHA 过期")
        if not path.is_file(): reasons.append("图像缺失")
        elif row.get("image_sha256") != sha(path): reasons.append("图像 SHA 不符")
        if max(row.get("resolution", [0])) < 1800: reasons.append("分辨率不足")
        if not 40 <= row.get("samples", 0) <= 64: reasons.append("采样未在 40–64 范围")
        if not row.get("camera_matrix"): reasons.append("缺相机矩阵")
        if reasons: render_issues.append({"view": row.get("view"), "issues": reasons})
        else: valid_renders[row["view"]] = row
    missing_main = [key for key, _, _ in MAIN if key not in valid_renders]
    missing_local = [key for key, _, _ in LOCAL if key not in valid_renders]
    before_rows = data['canopy-before-render-manifest.json'] or []
    before_by_view = {r.get('view'):r for r in before_rows if isinstance(r,dict)}
    native_comparisons = []
    for key in ['west-platform','east-understory','east-exit','south-walk']:
        before,after = before_by_view.get(key,{}),valid_renders.get(key,{})
        path = HERE/before.get('image','__missing')
        before_valid = bool(before.get('source_sha256') == BASELINE_SHA and path.is_file() and before.get('image_sha256') == sha(path))
        a,b = before.get('camera_matrix',[]),after.get('camera_matrix',[])
        matrix_error = max(abs(x-y) for ar,br in zip(a,b) for x,y in zip(ar,br)) if len(a) == len(b) == 4 and all(len(r) == 4 for r in a+b) else None
        same_camera = bool(before_valid and after and matrix_error is not None and matrix_error <= 1e-6 and before.get('camera') == after.get('camera') and before.get('camera_type') == after.get('camera_type') and abs(before.get('lens',0)-after.get('lens',1000)) <= 1e-6 and abs(before.get('ortho_scale',0)-after.get('ortho_scale',1000)) <= 1e-6 and before.get('hidden_objects') == after.get('hidden_objects') and len(before.get('resolution',[])) == 2 and before['resolution'][0]*after['resolution'][1] == before['resolution'][1]*after['resolution'][0])
        native_comparisons.append({'view':key,'baseline_image_valid':before_valid,'same_camera':same_camera,'camera_matrix_maximum_error':matrix_error,'before_image':before.get('image'),'after_image':after.get('image'),'before_source_sha256':before.get('source_sha256'),'after_source_sha256':after.get('source_sha256'),'before_resolution':before.get('resolution'),'after_resolution':after.get('resolution'),'before_samples':before.get('samples'),'after_samples':after.get('samples')})
    same_source = {name: bool(isinstance(data[name], dict) and data[name].get("source_sha256") == source_sha) for name in ["native-validation.json", "camera-validation.json", "glb-validation.json", "final-performance.json", "web-checks.json", "export-conversion.json", "integration.json", "visual-review.json"]}
    native_ok = bool(same_source["native-validation.json"] and native.get("baseline_unchanged") and native.get("reopened_snapshot_equal") and native.get("straight_path_entities") == 200 and native.get("plaza_interface_samples") == 241 and native.get("road_boundary_samples") == 241 and native.get("max_actual_road_ground_difference", 1) <= 1e-4 and len(native.get("fonts", [])) == 3 and all(f.get("packed") for f in native.get("fonts", [])))
    independent = data['independent-native-repair.json'] or {}
    planar = data['ground-trim-planar-validation.json'] or {}
    trim = independent.get('records',{}).get('ground_trim',{})
    trim_solid = trim.get('solid',{})
    same_source['independent-native-repair.json'] = independent.get('final_sha256') == source_sha
    same_source['ground-trim-planar-validation.json'] = planar.get('final_source_sha256',planar.get('final_sha256')) == source_sha
    independent_ok = bool(independent.get('final_sha256') == source_sha and independent.get('reopened_snapshot_equal') is True and trim_solid.get('nonmanifold') == 0 and trim_solid.get('zero_area') == 0 and trim_solid.get('volume',0) > 0 and trim.get('protected_original_loops') == 682 and trim.get('unmatched_original_loops') == [] and planar.get('final_source_sha256',planar.get('final_sha256')) == source_sha and planar.get('duplicate_projected_area',1) <= 1e-6 and planar.get('original_holes_or_exterior_filled_area',1) <= 1e-6 and planar.get('domain_exterior_error_area',1) <= .001)
    glb_ok = bool(same_source["glb-validation.json"] and glb.get("compressedProductionGLBLoadsInThree") and glb.get("otherCampusAssetsUnchanged") and not glb.get("duplicateOutsideAssetVertices", ["unknown"]) and len(glb.get("textNodes", [])) >= 4)
    camera_fit_ok = any(r.get('anchors') and isinstance(r.get('max_axis_error'), (int,float)) and r['max_axis_error'] <= .05 for r in camera.get('fits', []))
    pviews = perf.get("views", [])
    bviews = baseline_perf.get("views", [])
    regressions = [p["medianFrameMs"] / b["medianFrameMs"] - 1 for p, b in zip(pviews, bviews) if p.get("medianFrameMs") and b.get("medianFrameMs")]
    def same_pose(p,b):
        return all(len(p.get(k,[])) == len(b.get(k,[])) == 3 and all(abs(x-y) <= .001 for x,y in zip(p[k],b[k])) for k in ['camera','target'])
    performance_checks = {
        "same_source": same_source["final-performance.json"],
        "conditions": perf.get("resolution") == [1920,1080] and perf.get("pixelRatio") == 1 and len(pviews) == 3,
        "fps": len(pviews) == 3 and all(v.get("medianFps", 0) >= 30 for v in pviews),
        "p95": len(pviews) == 3 and all(v.get("p95FrameMs", 999) <= 50 for v in pviews),
        "overview_triangles": len(pviews) == 3 and all(v.get("triangles", 9999999) <= 3000000 for v in pviews[:2]),
        "near_triangles": len(pviews) == 3 and pviews[2].get("triangles", 9999999) <= 6000000,
        "relative_regression": len(regressions) == 3 and max(regressions) <= .20 and len(bviews) == 3 and all(p.get("gpu") == b.get("gpu") for p,b in zip(pviews,bviews)),
        "baseline_conditions": len(pviews) == len(bviews) == 3 and perf.get('resolution') == baseline_perf.get('resolution') and perf.get('pixelRatio') == baseline_perf.get('pixelRatio') and perf.get('browser') == baseline_perf.get('browser') and perf.get('headless') == baseline_perf.get('headless') and perf.get('measurementSeconds') == baseline_perf.get('measurementSeconds') and all(p.get('trees') is True and b.get('trees') is True and same_pose(p,b) for p,b in zip(pviews,bviews)),
        "browser_errors": bool(pviews) and not perf.get("errors", ["unknown"]) and not perf.get("failed", ["unknown"]) and perf.get("narrowOverflow") is False,
    }
    assets = glb.get("production_assets", [])[:]
    integration = data["integration.json"] or {}
    forest = integration.get("vegetation_reused", {})
    if forest.get("url", "").endswith("05-guanghua-closeout.glb"):
        assets.append(forest)
    actual_assets = []
    asset_integrity = bool(assets)
    for a in assets:
        asset_path = (ROOT / "web/public" / a.get("url", "__missing")).resolve()
        if not asset_path.is_relative_to(ROOT / "web/public") or not asset_path.is_file():
            asset_integrity = False
            actual_assets.append({"url": a.get("url"), "valid": False, "reason": "asset absent or outside public"})
            continue
        asset_hash, asset_size = sha(asset_path), asset_path.stat().st_size
        expected_hash = a.get("sha256") or a.get("revision")
        asset_valid = bool(expected_hash and asset_hash.startswith(expected_hash) and asset_size == a.get("bytes"))
        actual_assets.append({"url": a.get("url"), "sha256": asset_hash, "bytes": asset_size, "valid": asset_valid})
        asset_integrity = asset_integrity and asset_valid
    perf_assets = perf.get("production_assets", perf.get("assets", []))
    if isinstance(perf_assets, dict):
        perf_assets = [{"url": k, **v} for k,v in perf_assets.items() if isinstance(v,dict)]
    perf_asset_by_url = {a.get("url", a.get("path")): a for a in perf_assets if isinstance(a,dict)}
    performance_checks["production_asset_binding"] = bool(actual_assets) and all(perf_asset_by_url.get(a["url"],{}).get("sha256") == a.get("sha256") and perf_asset_by_url.get(a["url"],{}).get("bytes") == a.get("bytes") for a in actual_assets)
    performance_checks['page_binding'] = perf.get('page_tsx_sha256',perf.get('page_sha256')) == sha(ROOT/'web/app/page.tsx')
    asset_bytes = sum(a.get("bytes", 0) for a in assets)
    performance_checks["new_assets_size"] = bool(asset_bytes) and asset_bytes <= 150*1024*1024
    draw_goal = len(pviews) == 3 and all(v.get("drawCalls", 99999) <= 500 for v in pviews)
    # The browser QA entry writes frozen stages separately. Preparation stages
    # must never be promoted merely because a later report exists beside them.
    web_stages = [web.get(k,{}) for k in ["build", "visual", "performance"]]
    if all(web_stages):
        actual_by_url = {a['url']:a for a in actual_assets}
        page_hash = sha(ROOT/'web/app/page.tsx')
        web_sources_ok = all(r.get('source_sha256') == source_sha and r.get('source_matches_export') is True and r.get('frozen') is True and r.get('page_sha256') == page_hash for r in web_stages)
        web_assets_ok = all(len(r.get('assets',[])) >= 3 and all(actual_by_url.get(a.get('url'),{}).get('sha256') == a.get('sha256') and actual_by_url.get(a.get('url'),{}).get('bytes') == a.get('bytes') for a in r.get('assets',[])) for r in web_stages)
        web_build, web_visual, web_performance = web_stages
        web_ok = bool(web_sources_ok and web_assets_ok and web_build.get('pass') is True and not web_visual.get('errors',["unknown"]) and not web_visual.get('failed',["unknown"]) and web_visual.get('narrowOverflow') is False and web_performance.get('requiredPass') is True)
        same_source["web-checks.json"] = web_sources_ok
    else:
        web_ok = bool(same_source["web-checks.json"] and (web.get("passed") is True or web.get("status") == "passed"))
    reimport = data['decoded-reimport-check.json'] or {}
    reimport_ok = bool(reimport.get('pass') is True and reimport.get('source_sha256') == source_sha and actual_assets and reimport.get('production_sha256') == actual_assets[0].get('sha256') and reimport.get('production_asset_unchanged') is True)
    visual_tasks = visual.get("tasks", {})
    accepted_status = {"reviewed", "passed", "retained", "修复通过", "复核通过"}
    visual_ok = same_source["visual-review.json"] and all(visual_tasks.get(f"C{i:02d}", {}).get("status") in accepted_status for i in range(1,18))
    gates = {
        "protected_v7": BASELINE.exists() and sha(BASELINE) == BASELINE_SHA,
        "native": native_ok, "camera_report": same_source["camera-validation.json"] and camera_fit_ok,
        "independent_native_audit": independent_ok,
        "glb": glb_ok and asset_integrity and reimport_ok and same_source['export-conversion.json'] and same_source['integration.json'], "formal_18_main": not missing_main, "formal_11_local": not missing_local,
        "canopy_before_after": all(r['same_camera'] for r in native_comparisons),
        "performance": all(performance_checks.values()), "web_build_checks": web_ok,
        "internal_visual_review": bool(visual_ok),
    }
    ready = all(gates.values())
    status = "内部核验完成 · 已达到运行门槛，待用户视觉审阅" if ready else "实施候选 · 尚未全项验收"
    validation = {"date":args.date, "source_sha256":source_sha, "status":status, "internal_delivery_ready":ready, "user_visual_acceptance":False, "gates":gates, "same_source_reports":same_source, "native_same_camera_comparisons":native_comparisons, "actual_production_assets":actual_assets, "performance_checks":performance_checks, "draw_calls_goal_met":draw_goal, "new_asset_bytes":asset_bytes, "missing_main_views":missing_main, "missing_local_views":missing_local, "render_issues":render_issues, "frame_time_regression":regressions, "limits":["Other camera poses are approximate", "Canopy/shrub coverage statistics not certified", "Absolute scale/levels inferred", "ESKY_N position unknown"]}
    (HERE/"delivery-validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    def task_status(code):
        if code == "C18": return "内部交付通过" if ready else "全项待验收"
        row = visual_tasks.get(code, {})
        if same_source["visual-review.json"] and row.get("status") in accepted_status:
            return "内部复核通过" if row.get("status") in {"retained", "复核通过"} else "内部修复/复核通过"
        if code in {"C03", "C04", "C05"} and native_ok and independent_ok: return "结构量检通过；视觉待核验"
        if code in {"C09", "C13", "C15"} and gates['glb']: return "导出量检通过；视觉待核验"
        if code == "C17": return "运行门槛通过；视觉待核验" if gates["performance"] and web_ok else "网页/性能待验收"
        return "已实施/复核；视觉待核验"
    matrix = ["# C01–C18 完成矩阵", "", f"日期：{args.date}。状态：**{status}**。", "", f"最终源 SHA256：`{source_sha or '缺失'}`。本表由 `build_review.py` 从当前报告生成。历史阶段报告仅证明其当时的步骤；最终结论依赖同源量检、正式图和逐项内部视觉结论。用户视觉认可不自动更新。", "", "| ID | 范围 | 已实施/保留关系 | 当前结论 | 证据 | 边界 |", "|---|---|---|---|---|---|"]
    table_html = []
    for code, title, change, evidence, limit in TASKS:
        conclusion = visual_tasks.get(code, {}).get("conclusion", change)
        matrix.append(f"| {code} | {title} | {conclusion} | {task_status(code)} | [{evidence}]({evidence}) | {limit} |")
        table_html.append(f'<tr><th>{code}</th><td>{esc(title)}</td><td>{esc(conclusion)}</td><td>{esc(task_status(code))}</td><td>{link(evidence)}</td><td>{esc(limit)}</td></tr>')
    matrix += ["", "正式图未齐或源 SHA 不符时，C18 保持待验收。C06/C08 不把近似机位的图像分割结果当作可靠照片覆盖率差。draw calls ≤500 为目标项，是否达到单独列在交付报告中。", ""]
    (HERE/"completion-matrix.md").write_text("\n".join(matrix), encoding="utf-8")
    uncertainty = """# 证据、推定与未知

照片确认的是可见构件存在、连接关系、开口方向、门状态、蓝底黄字、红绿植物色带、窄冠与阔叶混植、铭牌字序及 FUDAN/爱心组合。它们不能自动提供测量精度。

- 绝对尺寸、园地/道路标高、校园 2/3 注册尺度与平移均为推定；保持草坪和其它校园资产既有定位。
- 西坛四个可见底座锚点采用近似像素位置拟合，其偏差见 camera-validation.json。此项局部拟合不认证整个楼体、所有窗轴或植物遮挡。
- 其它固定机位是人工近似。没有全面匹配机位下的乔木覆盖率差 ≤10 个百分点认证，也没有独立灌木覆盖率认证；不得从“图更绿”推断通过。
- 树种、精确株数/树位、背冠枝系、灌木品种与隐蔽背面形态为推定。4 株杉类仍为推定杉类。
- ESKY_N 的存在有照片支持，准确位置证据不足，保留位置未知登记；未凭对称补造。
- 地下车库空间、楼梯深部、隐藏梁柱/管路、地下根系与未拍雕塑细节未知；只表现照片可见范围，雕塑部分细节为概括表达。
- 结构报告认证列出的闭合实体、净带和采样接口，不认证全场任何两个对象都无穿插。
- 原生程序材质微起伏不完整转入 GLB；转换及透明范围须结合实际网页图审查。
- 本机 Chrome 1920×1080、DPR=1、回环 HTTP 成绩仅描述该设备、相机和计时区间；不代表公网带宽、其它设备或真实手机帧率。390px 验证是布局/操作检查。
- 内部视觉核验与用户视觉认可分别记录；用户尚未确认的成果不能写成用户已接受。
"""
    (HERE/"uncertainty.md").write_text(uncertainty, encoding="utf-8")
    def gallery(specs):
        cards = []
        for key,title,photo in specs:
            row = valid_renders.get(key)
            formal = f'<a href="{esc(row["image"])}"><img loading="lazy" src="{esc(row["image"])}" alt="{esc(title)}正式图"></a>' if row else '<div class="empty">本源正式图待生成或证据未通过</div>'
            reference = f'<a href="../../../references/guanghua_lawn/img/img/IMG_{photo}.jpeg"><img loading="lazy" src="../../../references/guanghua_lawn/img/img/IMG_{photo}.jpeg" alt="参考照片 IMG_{photo}"></a>' if photo else '<div class="empty">结构核验机位 · 无单一对应照片</div>'
            cap = f'{row["resolution"][0]}×{row["resolution"][1]} · {row["samples"]} 采样 · {esc(row.get("camera",""))}' if row else '缺少与当前源关联的有效图像'
            cards.append(f'<article class="card" id="{key}"><h3>{esc(title)}</h3><div class="pair"><figure>{reference}<figcaption>{"IMG_"+str(photo)+" · 原参考照片" if photo else "结构检查"}</figcaption></figure><figure>{formal}<figcaption>{cap}</figcaption></figure></div><p class="note">{("西坛为四个近似底座锚点拟合，其余立面未认证。" if key=="west-planter" else "机位为人工近似；并排图用于构件关系审查，不承诺逐像素一致。") if photo else "无遮挡图只检查结构；植物显隐状态记在渲染清单。"}</p></article>')
        return "\n".join(cards)
    diagnostic_cards = []
    diagnostic_rows = read('diagnostic1-render-manifest.json', [])
    diagnostic_by_image = {r.get('image'):r for r in diagnostic_rows if isinstance(r,dict)}
    for before_key,after_key,title in [("before-west-planter","west-planter","西坛结构诊断"),("before-east-exit","east-exit","东出口结构诊断")]:
        before = HERE/f"diagnostic1-{before_key}.png"
        old_after = HERE/f"diagnostic1-{after_key}.png"
        images = []
        for path,caption in [(before,"v7 历史诊断"),(old_after,"结构阶段诊断")]:
            record = diagnostic_by_image.get(path.name,{})
            if path.is_file() and record.get('image_sha256') == sha(path):
                images.append((path.name,caption+' · 源 '+record.get('source_sha256','')[:12]))
        if after_key in valid_renders: images.append((valid_renders[after_key]["image"],"当前源正式图"))
        figs = ''.join(f'<figure><a href="{esc(name)}"><img loading="lazy" src="{esc(name)}" alt="{esc(title+caption)}"></a><figcaption>{esc(caption)}</figcaption></figure>' for name,caption in images if (HERE/name).exists())
        diagnostic_cards.append(f'<article class="card"><h3>{esc(title)}</h3><div class="triple">{figs}</div><p class="note">历史诊断源与当前源不同。当前相机调整后，正式图不自动构成严格同机位前后对照；诊断原始相机记录见清单。</p></article>')
    title_by_view = {key:title for key,title,_ in MAIN}
    for row in native_comparisons:
        figs = []
        for image_key, valid, caption, res_key, samples_key in [('before_image',row['baseline_image_valid'],'v7 原生基线','before_resolution','before_samples'),('after_image',bool(row.get('after_image')),'当前源正式图','after_resolution','after_samples')]:
            image_name = row.get(image_key)
            res = row.get(res_key)
            settings = f"{res[0]}×{res[1]} · {row.get(samples_key)} 采样" if res else '参数待记录'
            media = f'<a href="{esc(image_name)}"><img loading="lazy" src="{esc(image_name)}" alt="{esc(caption)}"></a>' if valid else '<div class="empty">有效同源证据待生成</div>'
            figs.append(f'<figure>{media}<figcaption>{esc(caption)} · {esc(settings)}</figcaption></figure>')
        label = '同机位前后：矩阵与焦距核对通过' if row['same_camera'] else '同机位前后证据待补或参数不符'
        diagnostic_cards.append(f'<article class="card"><h3>{esc(title_by_view[row["view"]])} · {esc(label)}</h3><div class="pair">{"".join(figs)}</div><p class="note">分辨率、采样和材料版本不同，已逐项标注。两份原生模型之间的同机位不证明与现场照片逐像素匹配，也不认证照片冠层覆盖率差。</p></article>')
    perf_rows = []
    for i,v in enumerate(pviews):
        labels=["草坪总览","全园俯视","楼前近景"]
        regression=regressions[i]*100 if i<len(regressions) else None
        perf_rows.append(f'<tr><td>{labels[i] if i<3 else i+1}</td><td>{number(v.get("medianFps"))}</td><td>{number(v.get("p95FrameMs"))}</td><td>{number(v.get("triangles"),0)}</td><td>{number(v.get("drawCalls"),0)}</td><td>{number(regression)}%</td></tr>')
    frozen_web_performance = web.get('performance',{})
    frozen_web_records = frozen_web_performance.get('records',[]) if web_ok else []
    web_by_id = {r.get('id'):r for r in frozen_web_records}
    web_proof_images = []
    web_proof_cards = []
    for ident,title in [('garage-wb1-glyphs','WB1 中文近景'),('garage-wb2-glyphs','WB2 中文近景'),('fudan','FUDAN、橙色爱心与座椅'),('plaque-front','“驢背詩思”正面'),('plaque-oblique','“驢背詩思”斜面')]:
        row = web_by_id.get(ident,{})
        image_name = row.get('image')
        image_path = HERE/(image_name or '__missing')
        if image_path.is_file() and row.get('image_sha256') == sha(image_path):
            web_proof_images.append(image_name)
            web_proof_cards.append(f'<figure><a href="{esc(image_name)}"><img loading="lazy" src="{esc(image_name)}" alt="{esc(title)}实际网页"></a><figcaption>{esc(title)} · 实际网页冻结图</figcaption></figure>')
    garage_draw_calls = [r.get('drawCalls') for r in frozen_web_records if r.get('id','').startswith('garage') and isinstance(r.get('drawCalls'),(int,float))]
    garage_draw_note = f"四个车库取景的绘制调用为 {min(garage_draw_calls):,}–{max(garage_draw_calls):,}，同样有超过 ≤500 目标的取景。" if garage_draw_calls and max(garage_draw_calls)>500 else ''
    web_proofs_html = '<details><summary>实际网页文字与支承近景</summary><div class="pair">'+''.join(web_proof_cards)+'</div><p class="note">此处是实际校园网页截图；与原生主图取景不同，不标为逐像素同机位。来源及完整SHA见web-checks.json。</p></details>' if web_proof_cards else ''
    gate_html = ''.join(f'<li class="{("ok" if passed else "pending")}">{esc({"protected_v7":"原 v7 保护","native":"原生重开与接口量检","camera_report":"同源机位记录","independent_native_audit":"独立地面/近地双干复核","glb":"压缩 GLB 与字体","formal_18_main":"18 张正式主图","formal_11_local":"11 张必要局部","canopy_before_after":"四组原生同机位前后","performance":"性能运行门槛与同条件对比","web_build_checks":"网页检查与构建","internal_visual_review":"C01–C17 内部视觉结论"}[name])}：{"通过" if passed else "待验收"}</li>' for name,passed in gates.items())
    fits=camera.get("fits",[])
    max_fit=next((r.get("max_axis_error") for r in fits if r.get("max_axis_error") is not None),None) if same_source['camera-validation.json'] else None
    fitting = f"西坛四个近似底座锚点最大轴向偏差 {number(max_fit*100 if max_fit is not None else None,2)}%。" if max_fit is not None else "西坛锚点偏差尚待记录。"
    perf_binding_note = '以下记录已绑定当前源及实际生产资产。' if same_source['final-performance.json'] and performance_checks['production_asset_binding'] else '以下为已保存的历史/候选记录，尚未证明绑定当前源及实际资产，不计入最终通过。'
    road_delta = native.get('max_actual_road_ground_difference')
    native_detail = f"直通道保留 {native.get('straight_path_entities','待记录')} 件实体，广场接口与园路边界各 {native.get('road_boundary_samples','待记录')} 个指定采样；园路/园地采样最大高度差 {road_delta:.3g} 场景单位。两处完整中文与 FUDAN 共 3 处原生可编辑文字，字体打包。" if isinstance(road_delta,(int,float)) and native_ok else '原生结构与字体量检尚待当前源记录。'
    native_detail += ' “驢背詩思”及三处字网格在当前生产 GLB 保持完整。' if gates['glb'] else ' 当前生产 GLB 的四处字网格检查尚待通过。'
    draw_target_note = f'<p class="status">总览绘制调用 ≤500 的目标未完全达到；实际数值在下方性能表单独列出。{esc(garage_draw_note)}</p>' if ready and not draw_goal else ''
    body=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光华楼前总场景 · 收官审阅</title><style>
    :root{{--ink:#162738;--sub:#566777;--paper:#f3f5f4;--line:#d6dfdd;--green:#1e6657;--amber:#8a5a18}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}}main{{max-width:1320px;margin:auto;padding:32px 24px 64px}}h1{{font-size:34px;line-height:1.25;margin:12px 0}}h2{{margin:32px 0 14px}}h3{{margin:0 0 12px;font-size:19px}}a{{color:#245b86;text-underline-offset:3px}}p{{margin:10px 0}}nav{{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}}nav a,.button{{background:#fff;border:1px solid var(--line);border-radius:6px;padding:8px 12px;text-decoration:none}}.summary,.card{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:20px;margin:16px 0}}.status{{font-weight:700;color:{"var(--green)" if ready else "var(--amber)"}}}.kicker,.note,figcaption{{color:var(--sub);font-size:14px}}.sha{{font:12px/1.6 ui-monospace,monospace;overflow-wrap:anywhere}}.gates{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));list-style:none;padding:0;gap:8px}}.ok{{color:var(--green)}}.pending{{color:var(--amber)}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.triple{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}figure{{margin:0;min-width:0}}img{{width:100%;height:auto;display:block;border-radius:5px;background:#edf0ec}}figcaption{{margin:6px 0}}.empty{{aspect-ratio:4/3;background:#eef1ef;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;color:var(--sub)}}.table-wrap{{overflow:auto}}table{{border-collapse:collapse;background:white;width:100%;font-size:14px}}th,td{{border:1px solid var(--line);padding:10px;vertical-align:top;text-align:left}}th{{background:#edf2ef;white-space:nowrap}}details{{border-top:1px solid var(--line);padding:12px 0}}summary{{cursor:pointer;font-weight:650}}.artifact-links{{display:flex;flex-wrap:wrap;gap:12px}}@media(max-width:720px){{main{{padding:20px 12px}}h1{{font-size:27px}}.pair,.triple,.gates{{grid-template-columns:1fr}}.card,.summary{{padding:14px}}}}
    </style></head><body><main><p class="kicker">本地可检查交付 · {esc(args.date)} · v7 统一基线保留</p><h1>光华楼前总场景收官审阅</h1><p class="status">{esc(status)}</p>{draw_target_note}<p>结构、植物、细部、材料与网页优化沿同一源顺序实施。此页从当前模型与报告重新生成，过期源的正式图不计入完成数。</p><nav><a href="#checks">交付状态</a><a href="#main">18 张主图</a><a href="#locals">11 张局部</a><a href="#diagnostics">诊断对照</a><a href="#web">校园与性能</a><a href="#matrix">逐项结论</a><a href="#limits">证据边界</a></nav>
    <section class="summary" id="checks"><h2>当前证据</h2><p>有效正式图：主图 <strong>{18-len(missing_main)}/18</strong>，局部 <strong>{len(LOCAL)-len(missing_local)}/{len(LOCAL)}</strong>。原生网格 {number(native.get('meshes') if same_source['native-validation.json'] else None,0)} 件，可见原生估算 {number(native.get('visible_native_triangles') if same_source['native-validation.json'] else None,0)} 三角面；此数不等于网页实际绘制量。</p><p>{esc(native_detail)}</p><p class="sha">最终源 SHA256：{esc(source_sha or '缺失')}</p><ul class="gates">{gate_html}</ul><p>{esc(fitting)} 其它机位人工近似；没有认证乔木或灌木的照片覆盖率差。用户视觉认可尚未记录。</p><div class="artifact-links">{link('guanghua-closeout-final.blend','可编辑总场景')}{link('guanghua-closeout-optimized.glb','优化景观 GLB')}{link('guanghua-building-27.glb','校园楼体 GLB')}{link('run_closeout.ps1','单一复现入口')}{link('version-manifest.json','版本与哈希')}{link('delivery-validation.json','交付门槛报告')}</div></section>
    <section id="main"><h2>18 张固定主图</h2><p class="note">点击图像查看原图。照片与模型的绝对尺度、光照和相机并非现场测量；主要比较可见形态、硬景连接与遮挡关系。</p>{gallery(MAIN)}</section>
    <section id="locals"><h2>11 张必要局部</h2>{gallery(LOCAL)}</section><section id="diagnostics"><h2>诊断与修复对照</h2>{''.join(diagnostic_cards)}<p>{link('diagnostic1-render-manifest.json','第一批诊断相机记录')} · {link('diagnostic2-render-manifest.json','第二批诊断相机记录')}</p></section>
    <section class="summary" id="web"><h2>本地校园与实际运行</h2><p><a class="button" href="{esc(args.campus_url)}">打开本地校园</a>　{link('glb-validation.json','GLB/文字/重复区域检查')}　{link('web-checks.json','网页与构建记录')}</p><p class="note">需启动校园服务；复现入口提供地址与启动方法。页面默认显示植物，检查开关用于核验遮挡。测试为本机 Chrome、1920×1080、DPR=1、每机位 {number(perf.get('measurementSeconds'),0)} 秒、回环 HTTP；操作系统缓存状态见报告，不声称公网速度。</p><p class="status">{esc(perf_binding_note)}</p><div class="table-wrap"><table><thead><tr><th>固定机位</th><th>中位 fps</th><th>p95 帧时间 ms</th><th>实际三角面</th><th>draw calls</th><th>中位帧时回退</th></tr></thead><tbody>{''.join(perf_rows) or '<tr><td colspan="6">当前源性能待记录</td></tr>'}</tbody></table></div><p>新增资产合计 {number(asset_bytes/1048576)} MiB；draw calls ≤500 目标：{"达到" if draw_goal else "未达到或尚未记录"}。门槛和每项失败原因见 {link('delivery-validation.json')}。</p><p>{link('final-performance.json','最终性能原始记录')} · {link('baseline-performance.json','同设备基线')} · {link('final-campus-view-2.png','网页总览')} · {link('final-campus-no-trees.png','隐藏植物检查')} · {link('final-campus-narrow.png','390px 布局检查')}</p><p class="note">{esc(garage_draw_note)}</p>{web_proofs_html}</section>
    <section id="matrix"><h2>C01–C18 逐项结论</h2><div class="table-wrap"><table><thead><tr><th>ID</th><th>范围</th><th>实施与复核结论</th><th>当前状态</th><th>证据</th><th>边界</th></tr></thead><tbody>{''.join(table_html)}</tbody></table></div><p>{link('completion-matrix.md','可复制完成矩阵')}</p></section>
    <section class="summary" id="limits"><h2>推定与未知</h2><p>绝对尺度、标高、精确树位/株数/树种与遮挡背面为推定；地下空间、隐藏结构、未拍雕塑细节及 ESKY_N 准确位置仍未知。未知项继续登记，不以虚构构件消除。</p><p>原生程序微起伏与网页材质不完全等价；碰撞量检仅覆盖报告所列实体与接口。其它校园资产保护结果见 GLB/集成记录。{link('uncertainty.md','完整证据边界清单')}</p><details><summary>报告与复现记录</summary><div class="artifact-links">{''.join(link(n) for n in REPORT_NAMES if (HERE/n).exists())}</div><p>{link('README.md','交付说明')} · {link('final-render-manifest.json','相机、参数与图像哈希')}</p></details></section></main></body></html>'''
    (HERE/"review.html").write_text(body, encoding="utf-8")
    file_names = ["guanghua-closeout-final.blend", "guanghua-closeout-optimized.glb", "guanghua-building-27.glb", "05-guanghua-closeout.glb", "review.html", "README.md", "completion-matrix.md", "uncertainty.md", "run_closeout.ps1", "build_review.py", "delivery-validation.json"] + [name for name in REPORT_NAMES if (HERE/name).exists()] + [r["image"] for r in valid_renders.values()]
    file_names += [p.name for p in sorted(HERE.glob('*.py'))] + [p.name for p in sorted(HERE.glob('*.mjs'))] + [p.name for p in sorted(HERE.glob('*.cjs'))]
    file_names += [r['before_image'] for r in native_comparisons if r['baseline_image_valid']] + web_proof_images
    file_names += ['review-page-validation.json','review-desktop.png','review-narrow.png']
    file_names += ['../current-scene.json', '../scene-unified-v5/scene_fingerprints.py', '../road-rebuild-v1/road_geometry.py', '../entry-planters-v5/prepare_geometry.py', '../../../scripts/export_visible_glb.py', '../../../scripts/integrate_guanghua_landscape.py', '../../../web/validate-guanghua-integration.mjs', '../../../web/validate-models.mjs', '../../../web/app/page.tsx', '../../../web/public/campus-manifest.json']
    manifest={"date":args.date,"source_sha256":source_sha,"protected_baseline":{"path":str(BASELINE.relative_to(ROOT)).replace('\\','/'),"sha256":BASELINE_SHA,"unchanged":gates['protected_v7']},"status":status,"user_visual_acceptance":False,"production_assets":actual_assets,"runtimes":{"review_builder_python":sys.version.split()[0],"configured_python":".local/road-venv/Scripts/python.exe","configured_blender":".local/blender-runtime/blender-4.4.3-windows-x64/blender.exe","configured_node":"D:/nodejs/node.exe","browser":perf.get('browser'),"device":pviews[0].get('gpu') if pviews else None},"render_parameters":{"long_edge":1800,"samples":40,"exposure":.65,"view_transform":"AgX","main_count":18,"local_count":len(LOCAL)},"files":[],"primary_reference_photos":[]}
    for name in dict.fromkeys(file_names):
        p=HERE/name
        if p.is_file(): manifest["files"].append({"path":name,"bytes":p.stat().st_size,"sha256":sha(p)})
    for photo in sorted({photo for _,_,photo in MAIN+LOCAL if photo is not None}):
        relative_path = f'../../../references/guanghua_lawn/img/img/IMG_{photo}.jpeg'
        p = HERE/relative_path
        if p.is_file(): manifest['primary_reference_photos'].append({'path':relative_path,'bytes':p.stat().st_size,'sha256':sha(p)})
    (HERE/"version-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"source_sha256":source_sha,"valid_main":18-len(missing_main),"valid_local":len(LOCAL)-len(missing_local),"gates":gates},ensure_ascii=False,indent=2))
    if args.strict and not ready: raise SystemExit(1)

if __name__ == "__main__":
    main()
