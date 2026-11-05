# 机器人资产与装配仿真工具箱

[English](README.md) | [简体中文](README.zh-CN.md)

面向可复用机器人资产、柔性装配测试和真实求解记录展示的 Agent Skill 与专项工具集。覆盖 CAD、可视化装配、URDF、可运动 USD、连接器插拔、柔性排线、弹片与卡扣解锁。

**让几何来源、物理定义、求解记录和渲染回放分别可追溯。** 英文展示名为 Robot Asset & Assembly Simulation Toolkit，仓库名和调用名仍为 `robot-asset-toolkit`。

## 能做什么

| 流程 | 结果 |
| --- | --- |
| STEP/STP → GLB | 显式设置细分精度，保留可读取颜色和装配层级，自动进行 Blender 回读检查 |
| 机器人与工具装配 | 安装面对齐、坐标转换与干涉检查 |
| 扩展已有 URDF | 增加固定或可动部件，保留原有运动结构 |
| 从装配建立 URDF | 按刚体、关节、坐标系和真实机构资料建模 |
| AGV/AMR＋机械臂 | 整机组合、轮子/升降关节、移动根节点与验证 |
| URDF＋GLB → 可运动 USD | 保留运动与碰撞，把 GLB 外观和材质挂到实际 link |
| 最终 URDF 打包 | 静态结构检查、相对网格路径、ZIP 内 STL 格式校验 |
| 柔性与弹性装配建模 | 刚体、等效弹簧与 FEM 的选择，排线端部连接、卡扣/凸轮联动及工程近似 |
| 连接器插拔测试 | 到位、未解锁试拉、机构解锁、拔出、回弹和错位碰撞的分项验证 |
| 真实求解记录展示 | 同步实体材质/透视碰撞、机构特写、便携回放流程和循环 GIF |

装配理解、link 映射、动力学、FEM 建模和测试控制适配器仍需按具体模型执行。附带工具负责静态文件、记录完整性和视频转换，不提供任意连接器通用物理模型、插拔控制器、导航系统或机器人策略。

## 作为 skill 安装

克隆仓库后，将整个目录放入或链接到所用 Agent 支持的 skill 发现目录。`SKILL.md`、`agents/`、`references/` 和 `scripts/` 保持在一起；具体发现路径以当前 Agent 的安装说明为准。

```sh
git clone https://github.com/DuoChen-317/robot-asset-toolkit.git
```

在 Codex 中也可以请求安装：

```text
使用 $skill-installer 安装 https://github.com/DuoChen-317/robot-asset-toolkit 中的 skill。
```

调用示例：

```text
用 $robot-asset-toolkit 把这个 STEP 装配高精度转成 GLB。
用 $robot-asset-toolkit 把这个夹爪安装到已有机械臂 URDF 上。
用 $robot-asset-toolkit 将小车底盘与机械臂组合成整机描述。
用 $robot-asset-toolkit 用 URDF 负责物理、GLB 负责外观，生成 Isaac USD。
用 $robot-asset-toolkit 验证这个连接器和 socket 的插入、保持力与拉柄解锁。
用 $robot-asset-toolkit 建模柔性排线或弹片，明确 FEM、端部连接与材料近似。
用 $robot-asset-toolkit 将同一物理求解记录渲染成实体与透视同步画面，再生成 README GIF。
```

skill 主体和技术说明使用英文；Agent 应按用户的语言回复，可以继续全程用中文。

## 直接运行工具

原有转换/URDF 工具需要 Python 3.10+ 和标准库，转换子进程使用 FreeCAD、Blender 自带模块。新增可选 USD 检查工具需要 `pxr`，NPZ 检查工具需要 NumPy，GIF 工具调用单独安装的 FFmpeg/FFprobe；缺少这些可选依赖不影响 URDF 工具。

### STEP 转 GLB

分别安装 FreeCAD 和 Blender，并传入实际可执行文件路径：

```sh
python scripts/step_to_glb.py input.step output.glb \
  --freecad-python /path/to/freecad/python \
  --blender /path/to/blender \
  --work-dir /project/_conversion_work \
  --linear-mm 0.01 --angle-deg 5
```

PowerShell 示例：

```powershell
python scripts/step_to_glb.py 'D:/models/input.step' 'D:/exports/output.glb' `
  --freecad-python 'C:/Apps/FreeCAD/bin/python.exe' `
  --blender 'C:/Apps/Blender/blender.exe' `
  --work-dir 'D:/models/_conversion_work' `
  --linear-mm 0.01 --angle-deg 5
```

最终输出目录只放验证通过的 GLB；转换和校验 JSON 报告放在 `<工作目录>/reports/`。GLB 先在工作目录暂存并验证，再发布到最终目录。`--work-dir` 默认是输出目录旁的 `_conversion_work/`，已有过程目录时传入该路径复用。拒绝覆盖已有模型和报告。源 CAD 保留，不做一般减面，也不自动摆正或居中；重复顶点索引形成的退化三角形会清理并记录数量。

`0.01 mm` 和 `5°` 是可调整的起点，**不是全模型曲面误差的实测保证**。回读检查覆盖部件数、面数、实际顶点包围盒、层级、节点变换与可读取材质颜色。详见[转换细节与限制](references/step-to-glb.md)。

### 检查 URDF

```sh
python scripts/check_pack_urdf.py validate /path/to/robot.urdf
python scripts/check_pack_urdf.py validate /path/to/robot.urdf \
  --package robot_description=/path/to/robot_description
```

### 整理便携 URDF 包

```sh
python scripts/check_pack_urdf.py pack /path/to/robot.urdf \
  --out /project/final_urdf \
  --work-dir /project/_conversion_work \
  --report /project/_conversion_work/reports/urdf-pack.json \
  --zip /project/packages/robot.zip
```

结果包含 `robot.urdf`、所需网格和简短说明。网格路径改为相对路径，原有机构参数、惯量和几何数据保持不变。可用 `--report /path/to/new-report.json` 保存报告；两种模式的 `--package` 都可重复传入。

ZIP 和详细报告保存在最终资产目录外。输入、输出文件夹沿用具体项目的名称，不要求 `source/` 或固定层级；只创建当前任务需要的目录。GLB、装配、URDF 和 USD 共用的规则见[项目结构规范](references/project-layout.md)。

自动打包支持 **二进制 STL 和仅使用基本几何体的 URDF**。ASCII STL 需先用网格工具转换；带图片纹理或其他格式网格的依赖需显式收集。Xacro 先展开。静态检查不验证基本几何体尺寸、真实惯量、mimic 耦合语义、碰撞、控制能力或模拟器兼容性。

### 检查仿真资产、求解记录与预览

```sh
# 使用带 pxr 的 Python 检查 USD 静态结构。
python scripts/inspect_usd.py /project/final_usd/module.usd \
  --package-root /project/final_usd --report /project/_conversion_work/reports/usd.json

# NumPy 记录检查：数组键和顺序由实际求解适配器确定。
python scripts/check_sim_record.py trajectory.npz \
  --time-key telemetry --time-column 0 --pose-key body_q --deform-key shell_q

# 从真实渲染帧采样；保留原始 MP4 供高清观看。
python scripts/make_preview_gif.py insertion.mp4 preview.gif \
  --ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe --width 960 --fps 8 --colors 128
```

三个工具都拒绝覆盖已有报告；GIF 工具也拒绝覆盖已有输出。USD 检查覆盖作者定义的物理属性和当前组合，不验证烘焙后的碰撞或实际运动；记录检查不判定到位与保持力；GIF 转换不替代源视频的真实物理来源证明。

具体流程见[柔性与弹性机构](references/compliant-mechanisms.md)、[插拔验证](references/connector-validation.md)、[原生记录与展示](references/physics-recording-and-presentation.md)。这些说明区分实时求解和烘焙回放，要求分项报告验收结果；案例的载荷、材料和显卡选择不作为所有模型的默认值。

## 依赖与实测范围

| 组件 | 用途与状态 |
| --- | --- |
| Python 3.10+ | URDF 静态工具和流程入口；CI 检查 Python 3.10、3.12 |
| FreeCAD 1.1.1＋Blender 5.1.2 | 已在 Windows 用自动生成的双色、两部件、带嵌套层级 STEP 装配进行端到端测试 |
| Isaac Sim 5.1 | 机器人导入、连接器/排线/FEM 原生求解案例；需核对安装版本的 API 与 beta 设置 |
| `pxr` / NumPy（可选） | USD 依赖/物理属性和 NPZ 状态完整性检查；可用生成样本脱离 Isaac 测试 |
| FFmpeg＋FFprobe（可选） | GIF 调色板转换与完整解码检查，仅制作预览时需要 |
| `omniverse-cad-to-simready` | USD 转换流程可选依赖的外部 skill；其转换器与环境需单独安装 |

FreeCAD 子脚本目前依赖其 `ShapeAppearance` 与 MeshPart 分段接口；遇到未展开的 `App::Link` 会报错，不会静默漏件。其他版本和系统需另行验证。仓库不附带专有 CAD、厂商机器人模型或大型仿真缓存。

USD 外观组合覆盖逐 link 几何与 PBR 材质迁移。真正图片贴图还需要 UV、纹理文件和着色器连接验证；历史纯颜色案例不代表所有图片纹理都支持。缺少依赖时应明确报告。

历史 [FFC 与 QSFP 案例](references/case-studies.md)记录独立端口完整循环与工程近似。QSFP 整柜单模块循环通过，但全柜 FEM 回弹和多模块并发仍有未通过项；这些是有明确范围的工程演示，不是标定后的插拔力预测或通用性能基准。案例资产与视频在另一个[仿真作品集](https://github.com/DuoChen-317/simulation-portfolio)中，需相应访问权限；本 skill 不依赖该私有作品集。

## 目录

```text
SKILL.md                 Agent 使用入口
agents/openai.yaml       可选 Codex 显示信息
references/              按任务读取的技术说明
scripts/                 转换、URDF、USD、求解记录与 GIF 工具
tests/                   自动生成样本测试，含可选 USD/NumPy/视频检查
README.md                英文说明
README.zh-CN.md           中文说明
LICENSE                  本仓库的 MIT 许可证
```

## 验证与开发

```sh
python -m unittest discover -s tests -v
python -m compileall -q scripts
```

可选 CAD 集成测试：用 FreeCAD Python 生成测试装配，再用转换入口写到新的输出目录。

```sh
/path/to/freecad/python tests/make_step_fixture.py /path/to/test-work/assembly.step
python scripts/step_to_glb.py /path/to/test-work/assembly.step /path/to/test-work/assembly.glb \
  --freecad-python /path/to/freecad/python --blender /path/to/blender
```

CI 运行标准库工具，并在可选证据工具任务中安装 USD、NumPy 和 FFmpeg；不安装 FreeCAD、Blender 或 Isaac Sim。测试覆盖封装/截断 STL、非法关节树、路径解析、防止覆盖、打包后几何与变换保留，以及 USD 缺失依赖、非法求解记录和 GIF 解码。缺少可选依赖时，相应本地测试会跳过。

欢迎提交可复现的改进和测试。使用可再分发的模型或生成测试样本；不要提交凭据、个人路径、大型 CAD/网格与仿真输出。报告具体软件版本和实际验证范围。

## 许可证与外部软件

本仓库采用 [MIT 许可证](LICENSE)。FreeCAD、Blender、Isaac Sim、USD 转换器等是独立项目，使用各自的许可证与安装要求。本仓库不包含或重新授权厂商 CAD、机器人模型；外部转换 skill 通过引用使用，不复制其实现。
