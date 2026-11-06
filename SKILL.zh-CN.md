---
name: chalk-roster
description: 在批量生成火柴人 / 线稿 / 粉笔风动画短片之前，先冻结角色与风格名册和分镜节拍表，再对连续性（标识、道具、钩子、口播密度）做 SHIP / FIX / HOLD 门禁。适用于无脸 YouTube 火柴人剧集、多场线稿解说，或任何不能在镜头间漂角色的粉笔风短片。
---

# chalk-roster

火柴人短片最容易死在：帽子中途变色、道具瞬移、钩子拖到第 12 秒才出现。**chalk-roster** 是渲染前的连续性门禁：先锁名册与风格，再写带时码的节拍，跑检查器，通过后才去烧生成额度。

## 何时使用

- 无脸 / 火柴人 / 线稿 / 粉笔风、且有固定班底的短片
- 多场解说，同一剪影必须一眼可认
- 系列内容，风格指纹要跨集锁定
- 任何本想直接开写逐镜提示词的计划

**不要**用它做实拍剪辑卡点、音乐锁剪、混音拆解、真人姿势摆拍或聊天贴纸包——那些是别的活。

## 核心思路

1. **名册卡**（冻结）：频道 + 风格锁 + 角色（固定标识 markers + 禁止项 forbid）。
2. **节拍表**：有序分镜，含时长、出场角色、动作（禁止发呆）、道具归属、移交记录、口播词数、钩子标记。
3. **门禁**：`chalkroster.py check` → **SHIP** / **FIX** / **HOLD**。

### 裁决

| 裁决 | 含义 | 能否生成镜头 |
| --- | --- | --- |
| `SHIP` | 连续性干净 | 可以 |
| `FIX` | 软问题（口播密度、运动方向、禁止词） | 先改节拍再查 |
| `HOLD` | 硬伤（未知角色、道具跳跃、无钩子、风格不全） | 禁止生成 |

## 步骤

1. 复制 `templates/roster.json` → `roster.json`。填好 `style`（画幅、线宽、头填、肢体规则、背景、强调色上限）和 `cast`（id、至少 1 个 marker、forbid）。
2. 复制 `templates/beats.json` → `beats.json`。每行一镜；早段标钩子；写清道具持有者；每次转手写进 `transfers` 并设 `transfer: true`。
3. 形态检查：`python3 scripts/chalkroster.py lint roster.json beats.json`
4. 门禁：`python3 scripts/chalkroster.py check roster.json beats.json`
5. 仅当 `SHIP`：把每镜扩成生成提示词，出场角色的 **冻结 markers** 必须逐字重复。
6. `FIX` / `HOLD`：按列表修；禁止“差不多改一下标识”却不记移交。

## 名册结构

```json
{
  "channel": {"name": "chalk-bytes", "lock_style_across_episodes": true},
  "vo_lang": "zh",
  "style": {
    "aspect_ratio": "9:16",
    "line_weight": "medium",
    "head_fill": "hollow",
    "limb_rule": "two-arms-two-legs",
    "bg_rule": "flat-black",
    "max_accent_colors": 3,
    "accent_colors": ["鲜红", "电光蓝", "暖金"],
    "fingerprint": "hollow-head/medium-line/flat-black/3-accent"
  },
  "cast": [
    {
      "id": "guide",
      "role": "解说替身",
      "silhouette": "瘦高",
      "markers": ["红毛线帽", "黄T恤"],
      "forbid": ["写实五官", "多出来的手臂"]
    }
  ]
}
```

## 节拍结构

每镜需要 `duration_s`、`action`，通常还有 `cast`。道具是 `道具名 → 持有者id|null`。改持有者或改 marker 都必须有显式移交。

口播密度（词/秒）：英文 `1.8–2.9`，中文 `3.2–5.2`。钩子须在 `hook_deadline_s`（默认 5 秒）内落地。

## 示例

- 干净 30 秒集：`examples/cache-lie-roster.json` + `examples/cache-lie-beats.json` → `SHIP`。
- 道具瞬移：`examples/broken-prop-jump-beats.json` 配同一名册 → `HOLD`，补上移交记录即可。
- 内置演示：`python3 scripts/chalkroster.py demo`

## 提示

- markers 用**日常词语**（“红毛线帽”），不要写色号或骨骼配方。
- 剪影变了 = 新角色 id，不是偷偷改 marker。
- 强调色数量 ≤ `max_accent_colors`，用普通颜色词命名。
- 系列模式：打开 `channel.lock_style_across_episodes`，各集保持同一 `style.fingerprint`。
- 发呆的粉笔人会失败——每镜都要有具体 `action`。
