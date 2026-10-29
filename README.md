# 泰拉瑞亚手机 1.4.5.x 亚共版汉化修正

## 简介
本项目为亚共体 ＆ THTRS 服务器自发发起的一个汉化修正计划，优化原版汉化大量内容的同时补充一些详细信息，同时加入部分个性化介绍内容

Action中将自动在仓库更新时将汉化与字体内容导入文件中，可以随时下载，使用方式见下方

⚠️注意：当前Action中自动生成的文件只能在1.4.5.8.5版本的安卓安装包中使用，请勿在其他版本或ios版使用该文件

## 目前
- 当前版本：1.4.5.8.5
- 修改大量原版汉化错误内容
- 添加个性化介绍
- 添加大量物品的详细提示
- 自动工作流生成data.unity3d
- 自动工作流完成字体修改

## 分支：音译版（`yinyi-zh-translit`）

把游戏里所有能看到的英文按**读音**强行音译成汉字：Cloud → 克劳德，Eye of Cthulhu →
艾 奥夫 克苏鲁。
### 在游戏里切换

这套语言占用了游戏自带的「德语」槽位：

- 设置 → 语言 → 选第三项 **「开源仓库：CSFTTerrariaHansProject（Github）」**（即德语槽位）→ 全场音译
- 选第二项 **「亚共版汉化修正 v2026.26」** → 回到主分支的正常亚共版汉化

因此同一份 `data.unity3d` 里两种文本同时存在，随时切换、随时切回，不需要重装。

| 内容 | 落到哪个语言文件 |
| --- | --- |
| 亚共版正常汉化（主分支内容，语言菜单文案保持原样） | `zh-Hans*.json` |
| 音译版 | `yinyi-extra/de-DE*.json`（构建时覆盖德语槽位） |

### 生成方式

- 语言文件由「人工音译语料 + 机器补全」生成，构建脚本在 `tools/yinyi/`
- 语料来自 Steam 创意工坊模组《泰拉瑞亚音译版》（作者 HoCha113），放在 `sources/yinyi/`
- 该分支的 Actions 产物名为 `yinyi-result`，替换方式与 Main 分支完全相同（同样支持 1.4.5.8 安卓包）
- 只改了语言文本，字体字符集未变，因此不需要重新生成 `Font/`

想改某句翻译：编辑 `tools/yinyi/overrides.json` 或 `sources/yinyi/*.json`，然后运行
`python tools/yinyi/build.py` 重新生成 `yinyi-extra/`。

## 特别鸣谢
- 一只皮皮蛙（参考）
- 泰拉瑞亚中文wiki（参考）
- MorenRX（字体方面帮助）


## 参与者
- Cjx
- 欢愉
- 小史
- ka

## 交流与反馈
- 反馈/交流QQ群：634750168
- 音译版反馈： （星梦）1011819146

## 声明
本汉化完全免费使用，禁止用于商业用途，严禁倒卖！
如使用本仓库的汉化文件请在汉化中声明

## 使用步骤

需要内容：
- 在 Actions 下载最新的 data.unity3d （⚠️请使用 Main 分支⚠️）
- 泰拉瑞亚手机版 1.4.5.8.5 版本安装包 apk 文件
- MT 管理器

1. 使用 MT 管理器查看泰拉安装包文件，进入 /assets/bin/Data/ 找到 data.unity3d
2. 把你下载的 data.unity3d 文件添加替换掉原来的那个，压缩级别 ⚠️ 仅储存，选自动签名（注意选错了游戏会出问题）
3. 完成后安装即可，建议备份存档后再安装

## 工具
- 自动生解包/打包语言与字体工具：https://github.com/Cjx8848/UnpackTerrariaTextAsset
- 自动生成字体分页：BMFont（xml）
- 生成字体txt文件：https://github.com/WindFrost-CSFT/XnaFontRebuilder

## 仓库
- GitHub：https://github.com/WindFrost-CSFT/CSFTTerrariaHansProject
