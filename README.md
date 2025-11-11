# hcpatcher

一个 json 补丁框架，支持 JSON 文件的批量修改和自动翻译。

## 声明

- **本项目主要受到游戏 Mod 汉化工作流的启发**
- **本项目是实验性质的**
- **本项目使用生成式AI**
- **本项目对任何使用后果不负责**

## 功能特性

- 🚀 **批量处理** - 支持多个补丁文件同时应用
- 🌐 **自动翻译** - 集成翻译 API，支持中英文自动翻译
- 📝 **操作灵活** - 支持赋值、删除、列表插入等多种操作
- 🔧 **配置简单** - 基于 JSON 的补丁格式，易于编写和维护
- 📊 **日志记录** - 详细的变更日志和错误报告

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/hoofcushion/hcpatcher.git
cd hcpatcher

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 目录结构

```
hcpatcher/
├── source/          # 原始文件（将需要修改的文件放在这里）
├── patches/         # 补丁文件（\*.json）
├── output/          # 输出目录（自动生成）
├── dict_cache.json  # 翻译缓存
├── diff.log         # 补丁更改记录
├── init.py          # 主程序
└── requirements.txt # 依赖列表
```

### 3. 准备源文件

将需要修改的 JSON 文件复制到 `source/` 目录中：

```bash
# 示例：修改游戏配置文件
cp /path/to/game/configs/items.json source/
cp /path/to/game/configs/npcs.json source/
```

### 4. 编写补丁文件

在 `patches/` 目录中创建 JSON 补丁文件：

**示例：`patches/items.json`**

```json
{
 "items.json": {
  "weapons.sword.name/=": "<translate>",
  "weapons.sword.description/=": "<translate>",
  "weapons.bow.price/=": 500
 }
}
```

**示例：`patches/npcs.json`**

```json
{
 "npcs.json": {
  "merchant.dialogue/=": "欢迎光临我的商店！",
  "guard.quests/+$": "新任务",
  "old_quest/-": null
 }
}
```

### 5. 运行补丁

```bash
python init.py
```

处理完成后，修改后的文件将输出到 `output/` 目录。

## 补丁语法

### 操作符说明

| 操作符  | 功能           | 示例                     |
| ------- | -------------- | ------------------------ |
| `"/="`  | 赋值/替换      | `"name/=": "新名称"`     |
| `"/-"`  | 删除           | `"discard/-": null`     |
| `"/+$"` | 列表末尾添加   | `"tags/+$": "new_tag"`   |
| `"/+^"` | 列表开头添加   | `"effects/+^": "buff"`   |
| `"/+N"` | 在指定位置插入 | `"items/+1": "new_item"` |

### 路径语法

使用点号分隔的路径访问嵌套属性：

```json
{
 "game.json": {
  "player.stats.health/=": 200,
  "player.inventory.0/=": "药水",
  "levels.dungeon.monsters/+$": "龙"
 }
}
```

### 自动翻译

使用 `<translate>` 作为值，系统会自动翻译原文：

```json
{
 "dialogue.json": {
  "intro/=": "<translate>",
  "quest.start/=": "<translate>",
  "quest.complete/=": "任务完成！"
 }
}
```

## 补丁文件示例

### 简单汉化补丁

**`patches/translation.json`**

```json
{
  "game_text.json": {
    "ui.menu.start/=": "<translate>",
    "ui.menu.options/=": "<translate>",
    "ui.menu.quit/=": "退出游戏"
  },

  "items.json": {
    "potion.name/=": "<translate>",
    "potion.effect/=": "恢复生命值"
  }
}
```

### 游戏平衡调整补丁

**`patches/balance.json`**

```json
{
 "game_config.json": {
  "difficulty.easy.hp_multiplier/=": 2.0,
  "difficulty.hard.enemy_damage/=": 150,
  "unused_feature/-": null
 },

 "items.json": {
  "weapons.sword.damage/=": 50,
  "armors.shield.defense/+$": 10,
  "consumables.potion.effect/+1": "再生"
 }
}
```

### RPG 游戏角色补丁

**`patches/characters.json`**

```json
{
 "characters.json": {
  "heroes.warrior.name/=": "勇士",
  "heroes.warrior.skills/=": ["斩击", "防御", "冲锋"],
  "villains.dragon.weakness/+^": "冰属性",
  "npcs.merchant.goods/+$": "神秘药水"
 }
}
```

## 运行测试

```bash
python init.py test
```

## 输出说明

- **`output/`** - 处理后的文件
- **`diff.log`** - 详细的变更记录
- **`dict_cache.json`** - 翻译缓存，避免重复翻译

## 注意事项

1. **备份原始文件** - 建议在处理前备份原始文件
2. **编码问题** - 确保所有 JSON 文件使用 UTF-8 编码
3. **文件路径** - 补丁中的文件名必须与 `source/` 目录中的文件名完全匹配
4. **翻译质量** - 自动翻译可能不完美，建议人工校对重要文本

## 故障排除

### 常见错误

1. **文件未找到**

   ```
   Warning: source/game.json not found
   ```

   确保文件名和路径正确

2. **路径不存在**

   ```
   Path not found: player.stats.mana
   ```

   检查 JSON 路径是否正确

3. **翻译失败**
   ```
   翻译失败: ..., 返回原文: original text
   ```
   检查网络连接、环境配置或翻译服务状态

## 未来可能实现的功能

- **Lua Table 补丁支持** - 支持 Lua 配置文件的修改
- **纯文本替换补丁** - 支持非结构化文本文件的批量替换
- **管理并检索翻译进度** 支持记录翻译进度，追踪失效补丁

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
