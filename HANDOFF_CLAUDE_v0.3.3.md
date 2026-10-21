# CyberWork-Bench v0.3.3：给 Claude 的交接

更新：2026-10-20，Asia/Taipei。主机：当前 Linux 工作区 `/home/meow/SO101`。本次完成了新版任务登记、网页发布和本交接；没有恢复机械臂仿真执行。

**型号对应关系已由用户确认（2026-10-20）：R5 就是本项目的 L5 Pro。现有 `assets/vendor/ARX_R5/urdf/R5a.urdf` 作为该 L5 Pro 的对应模型继续复用，不再列为型号不匹配、模型替换或迁移阻碍。此前历史说明中将 R5 称作另一型号代理的表述已被此确认纠正。**

## 1. 用户现在要做什么

用户最终要搭一套**实机 benchmark**，先在仿真中还原任务并控制机械臂/灵巧手完成演示，再通过 HTML 给 MacBook Air 远程查看。之后希望评估不同模型，但当前 CyberWork 演示不是 π0.5 或其他学习模型的 benchmark 成绩。

当前明确要求：

1. 场景设计、任务描述、评分规则严格以最新完整文档 **v0.3.3** 为准。不能为了跑通降低阈值、跳过步骤，或自行补规则后称为原文标准。
2. **网页只展示新版任务与新版验收的演示，不展示未复核的旧任务演示。** 旧文件保留归档，不能只改版本号继续展示。用户进一步询问复用：已有场景资产应尽量复用，旧轨迹若确实通过新版场景与评分核验，也可沿用原录像；必须保留原始录制版本并另附新版验收，不能一律要求全部重跑。
3. 用户之前要求停止工作，随后授权阅读新文档、更新网页并写交接，由 Claude 接手。当前没有仿真任务在执行；请从新版规范核对开始，不继续旧控制会话。
4. 单臂 RealMan RM75-B + AG-95；双臂 ARX L5 Pro，两基座相隔 60 cm；灵巧手 Wuji / O6。L5 Pro 厂家参数等待确认事项已列在新文档附录 D。
5. 用户曾允许直接逐步控制，不要求专门训练/编写任务策略；曾允许为 D4/D5/H7/H8 **另加约束辅助演示**。这不是修改标准任务的授权；辅助不能算标准纯接触通过，目前新网页发布入口也拒绝辅助记录。
6. H-open O2/O3 用户此前明确确认：O2“先把大球入箱，再拿喷壶喷三下”；O3“喷三下、喷壶入箱，最后大球也入箱”。v0.3.3 仍只给 O1 示例，网页将 O2/O3 明确列为用户补充定义，不冒充原文。

## 2. 当前真实状态

| 项目 | 状态 |
|---|---|
| 最新文档 | 已完整读取并保存，包含通用评分；不再缺独立评分文档 |
| 新版任务登记 | 31 个入口，第一季主榜 12 项，已上网页 |
| 网页内容 | 任务描述、原文阶段权重、失败条件、2.0 秒保持规则、道具、采集、能力标签、原文链接 |
| 新版已验收演示 | **0**；所有入口待生成与验收，H8 按文档本期推迟 |
| 旧演示 | 旧 v0.3.2 判分下 27/31 有成功记录，不能当作新版成绩；已从网页移除 |
| 仿真判分实现 | 仍以旧版开发实现为主，尚未迁移到 v0.3.3 |
| 实机执行 / 模型评测 | 未完成；本轮没有发硬件动作 |

不要把“31 个任务已经登记”“旧判分 27 个通过”和“新版任务验收”混为一谈。网页显示 0 仅指尚未完成新版验收，**不是 31 个场景都不兼容**；已有 31 个任务入口均可作为迁移起点。

## 3. 入口与目录

| 内容 | 绝对位置 |
|---|---|
| 工作区地图，进入前必读 | `/home/meow/SO101/docs/00_WORKSPACE_MAP.md` |
| 项目根 | `/home/meow/SO101/experiments/cyberwork_bench` |
| 最新规范，项目内副本 | `/home/meow/SO101/experiments/cyberwork_bench/SPEC_v0.3.3.md` |
| 用户原始附件 | `/home/meow/.codex/attachments/99bcc94a-7202-4f43-ae5b-bdf95326415b/cyberwork_bench_full_v0.3.3.md` |
| 本交接 | `/home/meow/SO101/experiments/cyberwork_bench/HANDOFF_CLAUDE_v0.3.3.md` |
| 新网页产物根 | `/home/meow/SO101/outputs/cyberwork_bench/20261020_v033` |
| **当前服务目录** | `/home/meow/SO101/outputs/cyberwork_bench/20261020_v033/public` |
| 网页 HTML / 数据 | 上述 `public/index.html`、`public/report.json` |
| 完整规范阅读页 / 原文下载 | 上述 `public/spec.html`、`public/SPEC_v0.3.3.md` |
| 旧仿真执行及调试根，离线归档 | `/home/meow/SO101/outputs/cyberwork_bench/20261019_v032` |
| 旧完整执行尝试 | 上述 `debug/`，每次一个目录 |
| 旧 checkpoint / 材料诊断 | 上述 `prototypes/`，不能当作完整演示 |
| 旧发布选择 | 上述 `release_selection.json`、`release_extra_attempts.json`；新网页不读取 |

最新版原文 SHA-256（项目副本与附件完全一致）：

```text
23957455c1aa0c0cad76324ed84fae725a1c9021c6b3ab0426e2753cda1750e8
```

旧资料：`SPEC_v0.3.2.md`、`SPEC_v0.2.4.md`、`HANDOFF_v0.3.2.md`、`SPEC_ALIGNMENT_v0.3.2.md`、`USER_APPROVED_EXTENSIONS.md`，都在项目根。它们只能解释历史，不能覆盖 v0.3.3。`HANDOFF_v0.3.2.md` 等有当时的运行状态，接手时以本交接和实时文件为准。

## 4. 网页与服务

用户访问地址：**http://100.69.243.126:8765/**，通过同一 Tailscale 网络访问。服务只绑定此私网地址，没有开放公网。

完整规范：**http://100.69.243.126:8765/spec.html**。

| 用途 | 文件 / 命令 |
|---|---|
| systemd 用户服务 | `cyberwork-demo-viewer.service` |
| 实际服务配置 | `/home/meow/.config/systemd/user/cyberwork-demo-viewer.service` |
| 新版服务模板 | `/home/meow/SO101/experiments/cyberwork_bench/deployment/cyberwork-demo-viewer-v033.service` |
| 切换前服务备份 | `/home/meow/SO101/outputs/cyberwork_bench/20261020_v033/deployment/service_before_v033.service` |
| 静态服务代码 | `/home/meow/SO101/experiments/cyberwork_bench/tools/serve_demo_site.py` |

服务当前为 enabled / active。不要直接启动另一个进程抢 8765，也不要把服务切回旧 `20261019_v032/public`。目录列表关闭，支持 HTTP Range 和 `Cache-Control: no-cache`。

```bash
systemctl --user status cyberwork-demo-viewer.service --no-pager
systemctl --user cat cyberwork-demo-viewer.service
journalctl --user -u cyberwork-demo-viewer.service -n 30 --no-pager
```

普通网页内容更新不需重启服务；改服务参数才需要 `systemctl --user daemon-reload` 和 `systemctl --user restart cyberwork-demo-viewer.service`。

**新版网页源码**：

| 文件（相对项目根） | 用途 |
|---|---|
| `cwbench/web_spec_v033.py` | 读取并核对原文哈希；从 §1、§3–§6、§9 提取 31 项任务；读取 §2 通用规则；安全渲染 Markdown；新版能力标签适配 |
| `web/v033.html` | 新页面模板、筛选、任务卡、详情窗口、规则与文档入口 |
| `web/v033.css` | 桌面 / 手机样式 |
| `tools/build_v033_site.py` | **当前唯一新版构建入口**；不扫描旧输出，不回退使用旧视频 |
| `tools/verify_v033_site.mjs` | 浏览器验收：卡片、规则、筛选、全部详情、原文链接、无旧视频、手机无溢出 |
| `tests/test_web_v033.py` | 原文提取、安全转义、旧记录隔离与拒绝旧版本注册 |

构建与测试：

```bash
cd /home/meow/SO101/experiments/cyberwork_bench
.venv/bin/python tools/build_v033_site.py \
  --run /home/meow/SO101/outputs/cyberwork_bench/20261020_v033
.venv/bin/python -m unittest discover -s tests -p test_web_v033.py -v
```

`tools/build_demo_site.py`、`web/demo.html`、`cwbench/rubrics.py`、`cwbench/spec_contract.py` 是**旧网页 / 旧规则路径**，不要拿它们覆盖当前站点。

新演示发布机制目前尚无记录：可选注册表 `20261020_v033/verified_demos.json` 将任务 ID 映射到 `episodes/` 下的执行证据目录。例如 `{"S1":"new_run_name"}`。发布器要求该目录有 `result.json`、`manifest.json`、`replay_audit.json`、`spec_audit.json`、`model.mjb`、`trajectory.npz`、`demo.mp4`。

验收记录必须是 v0.3.3、规范哈希一致，且 `task_success`、`scene_alignment_passed`、`scoring_alignment_passed` 均为 true，控制重放通过；`artifact_sha256` 绑定模型、轨迹、视频、原始 result、manifest、replay 共六个文件。禁止辅助或中间位姿覆盖。原始录制可为 0.3.2 或 0.3.3，`captured_spec_version` 必须如实记录。复用旧录制时必须另有 `method: revalidated_saved_recording`，网页显示原始录制版本与新版验收版本，原始文件不改写。

**必须先实际完成新版验收，不能手工填 passed 或仅修改旧版本号。** 当前还没有配套完整的 v0.3.3 仿真验收流水线；网页发布器只是证据门禁，不能替代判分与物理核验。

## 5. 仿真源码、环境与模型资产

| 位置（相对项目根） | 内容 |
|---|---|
| `cwbench/scenes.py` | 当前任务建模，仍主要是 v0.3.2 适配 |
| `cwbench/scenes_v024.py`、`cwbench/geometry.py` | 复用的旧几何 / 道具构造 |
| `cwbench/scoring.py` | 当前开发判分，**不等于 v0.3.3 已实现** |
| `cwbench/env.py` | MuJoCo reset / step / 观测 / 安全停止 |
| `cwbench/robots.py` | 机器人 / 末端安装、关节与执行器接口 |
| `configs/*.yaml` | 旧任务配置；后续按 v0.3.3 迁移数值与规则来源 |
| `cwbench/experts.py` | 使用仿真真值的脚本控制与视频渲染 |
| `tools/direct_control.py` | 持续进程，经 stdin JSON 逐步控制机械臂与手指；保存每个动作和状态 |
| `cwbench/dexterity.py`、`dexterity_o6.py`、`arm_motion.py` | Wuji / O6 手指控制与单臂路由 |
| `cwbench/cloth_bag.py`、`paperboard.py`、`foam_ball.py` | 布袋、纸板薄壳、被动弹性海绵球近似 |
| `cwbench/adaptive_bag.py`、`adaptive_towel.py`、`flex_runtime.py` | 柔性网格和独立软体运行时 |
| `cwbench/grasp_assist.py` | 独立可选抓持辅助；标准演示不能混用 |
| `tools/replay_demo.py` | 初态只加载一次，随后重放保存 ctrl；辅助试验还重放明确记录的事件 |
| `tools/package_demo.py` | 旧演示打包；新版发布仍需补 v0.3.3 验收 |
| `tools/recheck_saved_rules.py` | 旧轨迹离线重判；不是重新运行仿真，且有未修复问题（见下） |

必须显式选 Python，不要混用 SO101 真机 / LIBERO / Conda 环境：

| 环境 | 实时核实版本 | 用途 |
|---|---|---|
| `/home/meow/SO101/experiments/cyberwork_bench/.venv/bin/python` | Python 3.11.15，MuJoCo 3.10.0 | 旧刚体执行、旧成功重放、新网页构建 |
| `/home/meow/SO101/experiments/cyberwork_bench/.venv-flex/bin/python` | Python 3.11.15，MuJoCo 3.16.0 | 软体 discrete 试验 |

离屏渲染用 `MUJOCO_GL=egl`。版本锁和说明位于 `requirements-release-lock.txt`、`requirements-flex-lock.txt`、`FLEX_RUNTIME.md`。不要升级旧环境后宣称历史控制仍精确重放。`pyproject.toml` 的项目版本仍是 0.3.2，这是仿真代码尚未迁移的实际状态，与网页规范版本分开。

**模型资产**（相对项目根）：

- RM75-B：`assets/vendor/RM75-B/urdf/RM75-B.urdf`，邻近 `meshes/`。
- 当前双臂：`assets/vendor/ARX_R5/urdf/R5a.urdf`，**用户已确认 R5 对应本项目 L5 Pro，直接继续复用**。保留原资产目录名与文件名。
- 另有 `assets/vendor/arx_l5/arx_l5.xml`，来源说明在同目录 README；作为备用历史资产保留，当前无需为解决型号名称而切换模型。
- Wuji Hand 2：`assets/vendor/wuji_hand2/mjcf/right_mjlab.xml`、`identified_parameters.json`。
- O6：`assets/vendor/somehand/linkerhand_o6_right/model.xml`。
- 来源和文件哈希：`assets/PROVENANCE.json`、`assets/FILE_SHA256.json`。
- AG95 为 95 mm 开口参数化代理，非原厂指垫 CAD；手–臂法兰、摩擦、材料、真实关节限制仍未实物校准。

### 5.1 哪些资产可以复用

v0.3.3 合并任务、评分、道具与采集规范，没有把现有 31 个任务入口换成另一套任务。迁移应以复用为主，重点修改不符合规范的几何与判分。

| 资产 | 复用方式 | 位置 / 边界 |
|---|---|---|
| 桌面、灯光、相机、坐标系、渲染 | 继续沿用场景基础设施 | `cwbench/geometry.py`、`configs/scene.yaml`；实机相机参数仍须标定 |
| RM75-B、Wuji、O6 模型和 mesh | 继续使用同一官方/来源模型，复核安装与限制 | 上述 `assets/vendor/`；不必重新做 mesh |
| AG95 参数化模型 | 可继续用于仿真，补真实指垫、安装和开口核验 | `cwbench/robots.py`；不得标成已标定原厂模型 |
| R5 双臂模型（对应 L5 Pro） | 继续复用现有 URDF、mesh、关节接口与 60 cm 双臂安装 | 用户已确认对应关系；不再要求换模型或重新确认型号 |
| 碗、杯、箱、篮、方块、水果、珠子、刷子、簸箕、销孔、卡片、旋钮、按钮 | 复用几何生成器和对象，只修具体尺寸、碰撞、初态及布局偏差 | `cwbench/scenes.py`、`scenes_v024.py`、`geometry.py`；暂停前已修的篮口、瓶高、倒角等不要丢掉 |
| 抽屉、瓶盖螺旋机构、输送带、试管架 | 复用关节/执行器及机构代码 | 核对行程、阻力、间隙、支撑和任务要求；D6 螺纹为运动学代理 |
| D4/D5/H7/H8 软体模型 | 复用网格、缝合、薄壳、被动弹性体和调试经验，继续修正 | `cloth_bag.py`、`paperboard.py`、`foam_ball.py`、`adaptive_*`；材料未标定、四项未完整通过，不算现成合格场景 |
| IK、运动控制、手指控制、接触检测 | 继续沿用，不要求重写策略 | `ik.py`、`experts.py`、`dexterity*.py`、`arm_motion.py`、`contact_ik.py`；读取真值控制不是模型能力成绩 |
| 环境接口、录制、轨迹、渲染、独立重放、远程服务 | 继续使用接口与工具 | `env.py`、`record.py`、`tools/replay_demo.py`、`tools/serve_demo_site.py` 等；按新字段扩展 |
| 旧 YAML、能力标签和任务编排 | 作为迁移底稿，按新原文核对 | 许多 BASE 尺寸和权重相同；版本号与阈值语义不能机械替换 |
| 旧成功 / 失败轨迹和视频 | 先复核，能通过新规的补验收后复用；只重跑不满足或缺证据的记录 | `20261019_v032/debug/`；保留原始模型、动作、版本、失败和哈希 |
| 旧 checker | 保留基础工具，修改核心语义 | `inside/on/lifted`、时间保持、顺序累计、保持型阶段等按下节修正，不能原样认定合规 |

优先评估两条复用途径：**同模型旧轨迹重验收**，或**修正少量场景参数后复用控制动作重新执行**。只有这两条都不成立时再重做该任务控制。不能把“暂未验收”解释成“必须全套重建”。

## 6. 新版迁移最先处理的规则差异

完整文档 §2 已解决“缺评分文档”的问题。不要再沿用缺失文档的旧说明。

1. `inside`：顶视投影**完全**在口沿内，落在底或内容物上、不搭边、已释放、2 秒内位移 <1 cm。旧实现的“80% 体积采样占比 + 瞬时速度阈值”不符合这个定义。
2. `on`：中心投影、底面接触及 ≤1 cm 高差、释放静止。不能直接继承旧的 80% 投影比例规则。
3. `lifted`：**物体底面**相对起始支撑面的高度；不是 body 原点相对初始 body 原点的位移。
4. 成功保持：2.0 秒实际仿真时间 / 真机墙钟，与控制频率无关。不要只数 50 步。
5. 阶段：按顺序累计历史最高进度；success=1 时 progress=1。D3/H6 的保持型阶段结束结算；`episode` 与 `item` 错误作用域按 §2.3，采集作废按 §9，不能混为一个规则。
6. H8：**球完全进入袋内**，不能用 80% 入袋替代；本期推迟。
7. 所有阈值源于 YAML；原文没给出的实测参数（如 D5 的 k）需明确待测，不能把开发值当成正式值。
8. 对照数据：S8/S9 记忆与对照各 100 条，不能禁止对照组训练采集；布局 1000–1499，公开布局的演示不属于正式训练集。
9. 逐项检查道具尺寸、数量、原始状态、顺序、不可借用的支撑与失败条件。D1 专属可达区、D3 无扶持对照、H 系列 DNI 尚未验收。

建议先实现独立新版规则与反例测试，再核对已有场景，优先复验现有轨迹；需要修改场景或原轨迹不合格时才重新从初态执行。独立控制重放仍然必须通过。先做 A1/A2/S1/S2 等较短任务作为端到端验证，不要一边继承旧 checker 一边继续积累“新版成功”。

## 7. 暂停前保留的改动与风险

项目不是干净提交。`git status` 显示 umbrella 仓库的 `experiments/cyberwork_bench/` 和 `docs/00_WORKSPACE_MAP.md` 为 untracked。没有为本工作创建 commit；不要 reset、clean 或覆盖用户改动。

上一个任务被用户停止前，已做但未作为新版发布的更改包括：

- A1 直径配置 13 cm → 12.7 cm；小瓶总高度修到 12 cm；篮子窄边开口改到至少 20 cm。
- S2 增加 100×100×30 mm 底座与 1 mm×45° 入口倒角的碰撞几何；胶带卷改为贯通孔形状。
- S7 O2 补查抽屉关闭；H1 补查抬升历史；D2 抬升阶段检查双臂同持；S6 取消错件当前阶段分；H8 松手阶段等到 2 秒再给分；S8/S9 对照采集限制已修正。
- **这些仍是针对旧代码的局部修补，不是 v0.3.3 的完整评分实现。** 新规范要求历史进度与保持型阶段等更完整的语义，需要重新审计，不能机械采用这些补丁。
- 最近旧环境测试日志：`/home/meow/SO101/outputs/cyberwork_bench/20261019_v032/regression_spec_full.log`：67 项测试，2 项跳过。它证明当时的回归，不证明新规范通过。
- `tools/recheck_saved_rules.py` 的批量重判在 S4 写 JSON 时遇到 `TypeError: Object of type int64 is not JSON serializable`，未修复；日志是旧产物根的 `rule_recheck_release.log`。不能宣称 8 项全部复核完成。
- D5 新增 `engage_roll_bundle` 的五距离约束诊断尚无完整成功，未做完整独立回放验收；不要当成熟控制接口直接采用。
- 旧的两个空闲 D5 checkpoint 诊断进程已关闭，最后保存的文件仍在。清理记录：`20261020_v033/closed_idle_diagnostics.json`。

旧版本四个未通过入口，供定位失败证据：

| 任务 | 记录（相对旧产物根） | 局部进展，不是完整成功 |
|---|---|---|
| D4 | `debug/assisted04_D4_spreader`；另有 `debug/discrete06_D4` | 前者撑口后暂停；后者曾方块入袋，橙子未完成；两物入袋并直立释放尚未完成 |
| D5 | `debug/assisted02_D5`；`prototypes/bundle_after_first*`、`prototypes/roll_bundle_after_first01` | 第一折达标；第二折回弹 / 几何不合格；checkpoint 不能算完整演示 |
| H7 | `debug/assisted03_H7` | 三片压平；第四片、循环互扣、释放和提箱尚未完成 |
| H8 | `debug/assisted03_H8_L1`、`debug/assisted04_H8_foam` | L1 口宽和另一手抬球有局部进展；刚性球卡袋沿；弹性球版本暂停。BASE L2 未通过 |

每次尝试通常包含 `result.json`、`manifest.json`、`model.mjb`、`trajectory.npz`、`trace.jsonl`、`operator_commands.jsonl`、`source/`；辅助还包含 `assistance_events.jsonl`。失败与成功都保留，不要删失败只留成功。

## 8. 本次网页验证证据

以下均在 `/home/meow/SO101/outputs/cyberwork_bench/20261020_v033/`：

- `website_tests.log`：5 项网页数据、旧版本隔离、显式重验收复用及哈希防篡改测试通过（测试中的假文件仅为临时夹具，不会进入实际站点）。
- `website_build_audit.json`：31 项，12 主榜，0 新版验收演示；原文哈希正确。
- `network_release_audit.json`：原私网 URL 返回 200，规范版本正确，旧演示 URL 返回 404。
- `verification_live/browser_audit.json`：31 卡片、31 评分区、31 能力区、全部详情、筛选和原文锚点通过，无旧图 / 视频；430 px 手机页面、详情和全文无横向溢出。
- `verification_live/website_desktop.png`、`website_cards.png`、`website_mobile.png`：实测页面截图。

这些是网页验收，**不是机械臂任务验收**。没有在 Mac Safari 本体测试；服务地址、浏览器和手机布局是在当前 Linux 上验证。

接手先读最新规范和本交接，再核实服务、Git 状态与解释器。继续仿真时只操作仿真，不能由这次授权推导出允许真机执行。
