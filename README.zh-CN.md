# chalk-roster

**中文** | [English](README.md)

火柴人 / 线稿 / 粉笔风动画短片的**渲染前角色与风格连续性门禁**。先冻结名册、写好带时码的节拍，跑检查器，只有 `SHIP` 才去烧生成额度。

## 功能

- **风格锁** — 画幅、线宽、头填、肢体规则、背景、强调色上限与指纹
- **角色名册** — 每名角色有固定标识（markers）与禁止项（forbid）
- **节拍表** — 分镜含动作（禁止发呆）、出场、道具归属、移交、钩子标记
- **连续性门禁** — 未知角色、道具瞬移、偷偷改标识、无钩子 → `HOLD`；口播密度 / 运动方向 / 禁止词 → `FIX`
- **标准库脚本** — `scripts/chalkroster.py`（`lint` / `check` / `demo`）+ 单元测试

## 安装

克隆本仓库并让代理读取，或把文件夹拷进你的 skills 目录。

```bash
git clone https://github.com/fangdididi/chalk-roster.git
cd chalk-roster
```

### Claude Code / Codex / Cursor 类代理

- 放到代理加载 skills 的路径，**或**
- 打开本目录并说：「按 SKILL.zh-CN.md（chalk-roster）检查这一集计划。」

无需 API Key。辅助脚本仅用 Python 3 标准库。

## 用法

```bash
# 形态检查
python3 scripts/chalkroster.py lint templates/roster.json templates/beats.json

# 完整门禁
python3 scripts/chalkroster.py check templates/roster.json templates/beats.json

# 内置 SHIP 演示
python3 scripts/chalkroster.py demo

# 测试
python3 -m unittest discover -s tests -v
```

常见代理流程：

1. 填写 `roster.json`（风格 + 角色）。
2. 填写 `beats.json`（分镜、钩子、道具、移交）。
3. 运行 `check`，按 `SHIP` / `FIX` / `HOLD` 分支。
4. `SHIP` 后再把分镜扩成生成提示词——出场角色的冻结 markers 必须逐字重复。

## 示例

| 文件 | 预期 |
| --- | --- |
| `examples/cache-lie-roster.json` + `examples/cache-lie-beats.json` | `SHIP` |
| 同一名册 + `examples/broken-prop-jump-beats.json` | `HOLD`（道具跳跃） |

## 目录结构

```
chalk-roster/
├── SKILL.md              # English skill
├── SKILL.zh-CN.md        # 中文技能
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/chalkroster.py
├── tests/test_chalkroster.py
├── templates/roster.json
├── templates/beats.json
└── examples/
```

## 裁决速查

| 裁决 | 退出码 | 含义 |
| --- | --- | --- |
| SHIP | 0 | 连续性干净 — 可以生成 |
| FIX | 2 | 软问题 — 先改节拍 |
| HOLD | 3 | 硬伤 — 禁止生成 |
