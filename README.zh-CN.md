# Robot Asset Toolkit

[English](README.md) | [简体中文](README.zh-CN.md)

一套面向机器人资产制作的 Agent Skill 与小型工具集，连接 CAD、可视化装配、URDF 和可运动 USD。

**明确各类数据的职责：CAD/GLB 提供外观，经过核对的机器人描述提供运动与物理定义。**

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

这是 **skill＋专项命令行工具**。装配理解、link 映射、动力学与 USD 合成需要按具体模型执行，并非任意机器人一键重建器；不包含导航、控制器或任务调度系统实现。

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
```

skill 主体和技术说明使用英文；Agent 应按用户的语言回复，可以继续全程用中文。

## 直接运行工具

入口工具需要 Python 3.10+，仅使用标准库。转换子进程使用 FreeCAD、Blender 自带的模块，不要求向系统 Python 安装 bpy 或 FreeCAD。

### STEP 转 GLB

分别安装 FreeCAD 和 Blender，并传入实际可执行文件路径：

```sh
python scripts/step_to_glb.py input.step output.glb \
  --freecad-python /path/to/freecad/python \
  --blender /path/to/blender \
  --linear-mm 0.01 --angle-deg 5
```

PowerShell 示例：

```powershell
python scripts/step_to_glb.py 'D:/models/input.step' 'D:/exports/output.glb' `
  --freecad-python 'C:/Apps/FreeCAD/bin/python.exe' `
  --blender 'C:/Apps/Blender/blender.exe' `
  --linear-mm 0.01 --angle-deg 5
```

输出为 GLB 及同名 `.conversion.json`、`.validation.json`，拒绝覆盖已有结果。源 CAD 保留，不做一般减面，也不自动摆正或居中；重复顶点索引形成的退化三角形会清理并记录数量。

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
  --out /path/to/final_urdf --zip /path/to/final_urdf.zip
```

结果包含 `robot.urdf`、所需网格和简短说明。网格路径改为相对路径，原有机构参数、惯量和几何数据保持不变。可用 `--report /path/to/new-report.json` 保存报告；两种模式的 `--package` 都可重复传入。

自动打包支持 **二进制 STL 和仅使用基本几何体的 URDF**。ASCII STL 需先用网格工具转换；带图片纹理或其他格式网格的依赖需显式收集。Xacro 先展开。静态检查不验证基本几何体尺寸、真实惯量、mimic 耦合语义、碰撞、控制能力或模拟器兼容性。

## 依赖与实测范围

| 组件 | 用途与状态 |
| --- | --- |
| Python 3.10+ | URDF 静态工具和流程入口；CI 检查 Python 3.10、3.12 |
| FreeCAD 1.1.1＋Blender 5.1.2 | 已在 Windows 用自动生成的双色、两部件、带嵌套层级 STEP 装配进行端到端测试 |
| Isaac Sim 5.1 | 技术流程参考了真实机器人的导入与有限步物理验证；仓库未附通用 USD 一键合成器 |
| `omniverse-cad-to-simready` | USD 转换流程可选依赖的外部 skill；其转换器与环境需单独安装 |

FreeCAD 子脚本目前依赖其 `ShapeAppearance` 与 MeshPart 分段接口；遇到未展开的 `App::Link` 会报错，不会静默漏件。其他版本和系统需另行验证。仓库不附带图片、专有 CAD 或厂商机器人模型。

USD 外观组合覆盖逐 link 几何与 PBR 材质迁移。真正图片贴图还需要 UV、纹理文件和着色器连接验证；历史纯颜色案例不代表所有图片纹理都支持。缺少依赖时应明确报告。

## 目录

```text
SKILL.md                 Agent 使用入口
agents/openai.yaml       可选 Codex 显示信息
references/              按任务读取的技术说明
scripts/                 STEP 转换子脚本与 URDF 工具
tests/                   可移植静态测试与 CAD 测试模型生成器
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

CI 仅运行标准库工具测试，不安装 FreeCAD、Blender 或 Isaac Sim。静态测试覆盖封装/截断 STL、非法关节树、路径解析、防止覆盖，以及打包后几何与安装变换的保留。

欢迎提交可复现的改进和测试。使用可再分发的模型或生成测试样本；不要提交凭据、个人路径、大型 CAD/网格与仿真输出。报告具体软件版本和实际验证范围。

## 许可证与外部软件

本仓库采用 [MIT 许可证](LICENSE)。FreeCAD、Blender、Isaac Sim、USD 转换器等是独立项目，使用各自的许可证与安装要求。本仓库不包含或重新授权厂商 CAD、机器人模型；外部转换 skill 通过引用使用，不复制其实现。
