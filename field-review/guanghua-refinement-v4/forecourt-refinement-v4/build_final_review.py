"""Assemble existing evidence images and verified checkpoints into a local review."""
import hashlib
import html
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

O = Path(__file__).resolve().parent
ROOT = O.parents[2]
PHOTOS = ROOT / 'references/guanghua_lawn/img/img'
STAGES = [
    dict(id='01', title='楼前入口与连续挡墙', photo='4464', extra='4485', checkpoint='stage01-building-entry.blend',
         change='重建平台、中央台阶、两侧坡道及弧形种植坛；挡墙、压顶与圆花钵底座连续接合。',
         check='坡道末端与平台同为推定标高 3.45；花钵底与压顶同为 0.915；修改实体闭合且体积为正。'),
    dict(id='02', title='东入口花钵盆足与压顶', photo='4491', checkpoint='stage02-east-urn.blend',
         change='扩大盆足、降低细颈并减薄压顶；盆足平面坐落在石顶；先分离与西花钵共享的数据。',
         check='盆足底与压顶同为推定标高 0.92；东侧两盆独立，西花钵几何保持。'),
    dict(id='03', title='直通道铺装与凹槽边带', photo='4492', checkpoint='stage03-straight-path.blend',
         change='中间通道改为独立矩形错缝铺装；两边拆出 198 个独立边带实体及浅弧槽。',
         check='中心宽约 2.94、边带宽 0.33、槽深 0.06 均为推定；修改实体通过闭合与正体积检查。'),
    dict(id='04', title='曲径黑三角与纹理黑楔形', photo='4496', checkpoint='stage04-curve-repair.blend',
         change='合并四段道路上表面、去除重叠面与北端折返面，清理两个退化面；替换旧纹理中的重复黑楔形。',
         check='去除约 8.10 平方单位重复投影面积；曲径非流形边 0、零面积面 0、正体积 33.959；新贴图已打包。'),
    dict(id='05', title='广场分格与入口铺装', photo='4485', extra='4464', checkpoint='forecourt-refined-v4.blend',
         change='独立广场材质统一浅色大分格、细板缝和入口坡面纹理方向，保持广场边界。',
         check='大分格 6、小板 1.2 × 1.5、浅带 0.18 均为推定；本阶段全部网格几何保持。'),
]

def rel(path):
    return Path(os.path.relpath(path, O)).as_posix()

def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', size)

def sheet(name, rows, headings):
    cell_w, cell_h, pad = 640, 425, 20
    width = pad + len(headings) * (cell_w + pad)
    height = 110 + len(rows) * (cell_h + 70)
    canvas = Image.new('RGB', (width, height), '#f3f5f5')
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 15), '光华楼前场精修 v4 · 五阶段审阅', font=font(30), fill='#19342e')
    draw.text((pad, 57), '原照片与人工近似机位对照；所有未实测尺寸均为推定', font=font(20), fill='#52645f')
    for r, (label, paths) in enumerate(rows):
        y = 105 + r * (cell_h + 70)
        draw.text((pad, y), label, font=font(23), fill='#19342e')
        for c, path in enumerate(paths):
            x = pad + c * (cell_w + pad)
            draw.text((x, y + 31), headings[c], font=font(18), fill='#52645f')
            with Image.open(path) as source:
                tile = ImageOps.contain(ImageOps.exif_transpose(source).convert('RGB'), (cell_w, cell_h - 10), Image.Resampling.LANCZOS)
                top = y + 60
                draw.rectangle((x, top, x + cell_w, top + cell_h - 10), fill='#e1e6e4')
                canvas.paste(tile, (x + (cell_w - tile.width) // 2, top + (cell_h - 10 - tile.height) // 2))
    canvas.save(O / name)

def figure(path, caption):
    url = html.escape(rel(path), quote=True)
    return f'<figure><a href="{url}"><img loading="lazy" src="{url}" alt="{html.escape(caption)}"></a><figcaption>{html.escape(caption)}</figcaption></figure>'

def main():
    verification = json.loads((O / 'final-validation.json').read_text(encoding='utf-8'))
    audit = json.loads((O / 'delivery-audit.json').read_text(encoding='utf-8'))
    assert audit['all_checked_solids_closed_positive_volume_no_zero_area']
    evidence_paths = []
    blocks = []
    for stage in STAGES:
        key, photo = stage['id'], stage['photo']
        paths = [PHOTOS / f'IMG_{photo}.jpeg', O / f'stage{key}-before-{photo}.png',
                 O / f'stage{key}-after-{photo}.png', O / f'stage{key}-after-top.png']
        evidence_paths.extend(paths)
        assert all(p.is_file() for p in paths), paths
        figures = ''.join(figure(p, caption) for p, caption in zip(paths, [f'实拍 IMG_{photo}', '修改前 · 同一人工机位', '修改后 · 人工近似机位', '修改后 · 正交俯视（隐藏遮挡）']))
        supplements = ''
        if stage.get('extra'):
            p = PHOTOS / f"IMG_{stage['extra']}.jpeg"
            a = O / f"stage{key}-after-{stage['extra']}.png"
            evidence_paths.extend([p, a])
            supplements = '<details><summary>辅助照片视角</summary><div class="pair">' + figure(p, f"实拍 IMG_{stage['extra']}") + figure(a, '修改后 · 人工近似机位') + '</div></details>'
        if key == '04':
            supplements += '<div class="pair">' + figure(O / 'stage04-before-junction.png', '交汇处修改前') + figure(O / 'stage04-after-junction.png', '交汇处修改后 · 黑三角及纹理黑楔形已处理') + '</div>'
        blocks.append(f'<section id="stage{key}"><h2>{key} · {stage["title"]}</h2><p>{stage["change"]}</p><p class="check">验收：{stage["check"]}</p><div class="evidence">{figures}</div>{supplements}<p><a href="{stage["checkpoint"]}">可编辑检查点</a> · <a href="stage{key}-validation.json">阶段验证记录</a></p></section>')
    sheet('five-stages-photo-comparison.png', [(s['id'] + ' · ' + s['title'], [PHOTOS / f"IMG_{s['photo']}.jpeg", O / f"stage{s['id']}-after-{s['photo']}.png"]) for s in STAGES], ['参考照片', '修改后 · 人工近似机位'])
    sheet('five-stages-top-overview.png', [(s['id'] + ' · ' + s['title'], [O / f"stage{s['id']}-after-top.png"]) for s in STAGES], ['修改后 · 正交俯视'])
    report = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光华楼前场精修 v4 · 最终审阅</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f3f5f5;color:#243d35;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1500px;margin:auto;padding:34px}header,section{background:white;padding:28px;border:1px solid #dce5df;border-radius:12px;margin-bottom:24px}h1{font-size:32px;line-height:1.35}h2{font-size:24px}a{color:#126950}nav{display:flex;flex-wrap:wrap;gap:18px}figure{margin:0;background:#edf1ef;border-radius:7px;overflow:hidden}img{display:block;width:100%;height:300px;object-fit:contain}figcaption{padding:10px 14px;font-size:14px}.hero img{height:auto;max-height:750px}.evidence{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.pair{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:18px}.check{background:#eaf5ef;padding:12px 16px;border-left:4px solid #279b74}details{margin-top:18px}summary{cursor:pointer}.note{color:#52645f}@media(max-width:1050px){.evidence{grid-template-columns:repeat(2,1fr)}main{padding:15px}}@media(max-width:650px){.evidence,.pair{grid-template-columns:1fr}header,section{padding:18px}h1{font-size:25px}}
    </style><main><header><h1>光华楼前场精修 v4 · 最终审阅</h1><p>五个阶段已保存。第四阶段同时处理曲径重复面造成的黑三角及旧贴图中的重复黑楔形，最终 v4 已包含修复。</p>'''
    report += f'<p class="check">六份检查点均已重开；当前校验值与重开记录一致。主草坪、西入口等 {verification["protected_lawn_and_west_meshes"]} 个受保护网格及楼体主体保持。最终场景中重新检查的 {audit["previously_audited_solids_checked_in_final"]} 个修改实体全部闭合、无零面积面且体积为正。两项新纹理均已打包。</p>'
    report += '<p class="note">照片可确认可见构件和连接关系；绝对尺寸、路线标高、两侧镜像及相机参数仍为推定。相机为人工近似，未做测量配准。楼体沿用受保护的旧比例模型；植被与旧土填充体未作为建筑实体审计，未做全场景全部对象之间的碰撞认证。</p><nav>'
    report += ''.join(f'<a href="#stage{s["id"]}">{s["id"]} {s["title"]}</a>' for s in STAGES)
    report += '</nav><p><a href="forecourt-refined-v4.blend">最终可编辑模型</a> · <a href="five-stages-photo-comparison.png">五阶段照片对照总览</a> · <a href="five-stages-top-overview.png">五阶段俯视总览</a> · <a href="final-validation.json">重开与保护验证</a> · <a href="delivery-audit.json">收尾审计</a></p></header><section class="hero">'
    report += figure(O / 'stage05-after-overall.png', '最终 v4 整体渲染') + '</section>' + ''.join(blocks) + '</main></html>'
    (O / 'final-review.html').write_text(report, encoding='utf-8')
    table = '\n'.join(f'|{s["id"]} {s["title"]}|IMG_{s["photo"]}' + (f'、{s["extra"]}' if s.get('extra') else '') + f'|[俯视](stage{s["id"]}-after-top.png)|[近似照片视角](stage{s["id"]}-after-{s["photo"]}.png)|[{s["checkpoint"]}]({s["checkpoint"]})|' for s in STAGES)
    readme = f'''# 光华楼前场精修 v4 · 收尾交付

[打开完整审阅页](final-review.html) · [最终可编辑模型](forecourt-refined-v4.blend) · [整体渲染](stage05-after-overall.png)

来源为 `../west-entry-v3/west-entry-aligned-v3.blend`，原文件未覆盖。五个阶段均完成；断网前的纹理修复已实际写入第四阶段及最终模型，本次核对文件、审计最终模型并补齐审阅汇总。

|阶段|主参考|俯视|照片近似视角|检查点|
|---|---|---|---|---|
{table}

[五阶段照片对照总览](five-stages-photo-comparison.png) · [五阶段俯视总览](five-stages-top-overview.png)

## 修改与核验

''' + '\n\n'.join(f'**{s["id"]} {s["title"]}**：{s["change"]} {s["check"]}' for s in STAGES) + f'''

六份检查点已通过重开及必要 feature_id 检查，本次核对 SHA-256 全部一致。受保护的 {verification['protected_lawn_and_west_meshes']} 个主草坪、西入口等网格及楼体主体顶点/拓扑保持；来源文件校验值保持。见 [重开验证](final-validation.json)。

最终文件重新打开后，{audit['previously_audited_solids_checked_in_final']} 个之前通过阶段实体检查的修改对象再次全部通过：非流形边 0、零面积面 0、正体积、坐标有限。曲径使用独立清洁石材纹理，广场使用独立校准纹理，两项纹理均已打包；曲径贴图无 RGB 最大通道低于 0.05 的黑像素。贴图统计与交汇近景共同支持黑楔形残留已处理。见 [收尾审计](delivery-audit.json) 和 [交汇前后近景](final-review.html#stage04)。

## 证据边界

照片确认可见构件与连接关系；绝对尺寸、路线/标高、镜像及相机参数均为推定。相机为人工近似视角，未做测量配准。主草坪与西入口是保护基线，楼体沿用旧比例模型；植被与旧土填充网格未作为建筑实体审计，未做全场景全部对象之间的碰撞认证。

本轮交付可编辑 Blender 检查点与审阅证据，尚未接入网页资产。下一单一建议目标是依据照片核对东高台与保留的独立高程道路之间的接续关系。
'''
    (O / 'README.md').write_text(readme, encoding='utf-8')
    inventory = []
    for path in sorted(set(evidence_paths + [O / 'stage04-before-junction.png', O / 'stage04-after-junction.png', O / 'stage05-after-overall.png'])):
        with Image.open(path) as source:
            source.verify()
        inventory.append(dict(file=rel(path), bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (O / 'review-evidence-manifest.json').write_text(json.dumps(dict(images=inventory, camera_status='manual approximate; not solved', dimensions='inferred; not measured'), ensure_ascii=False, indent=2), encoding='utf-8')
    print('FINAL_REVIEW_BUILT', len(inventory), 'verified evidence images')

if __name__ == '__main__':
    main()
