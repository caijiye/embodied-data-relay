# Contributing

感谢你愿意参与具身数据驿。这个项目同时包含软件、硬件设计与数据管线；贡献前请先读本文件。

## 开发环境

```bash
git clone <repo>
cd embodied-data-relay
uv venv --python 3.12
uv pip install -e ".[dev]"
ffmpeg -version   # 必须
pytest -q         # 8 个测试应通过
```

可选：

```bash
docker compose up -d minio   # 本地 S3 兼容交付演示
```

## 代码规范

- Python 3.11/3.12；类型标注优先；公共函数写简短 docstring。
- 不提交真实客户数据、密钥、Wi-Fi 密码、S3 凭证。
- 新增依赖必须更新 `pyproject.toml` 与 `NOTICE`，并确认许可证兼容 Apache-2.0。
- 质量门禁的原则：**只标记，不自动删除原始数据**。任何删除行为必须显式、可审计、可回滚。
- 硬件设计文件放在 `hardware/`，软件在 `edr/`、`scripts/`。

## 提交与 PR

1. Fork / 新建分支：`feat/...`、`fix/...`、`docs/...`。
2. 跑 `pytest -q`；涉及管线改动时附上 benchmark 或复现命令。
3. Commit 使用清晰的祈使句；建议 `git commit -s` 添加 DCO sign-off。
4. PR 描述包含：问题、方案、测试、对数据安全/许可的影响。
5. 维护者用 lazy consensus 处理；有分歧时在 issue 中记录决策。

## 硬件贡献

- 提供 BOM、接线图、3D 模型/图纸、装配步骤中的至少一项。
- 标注实测条件：主机型号、磁盘、网口、温度、功耗、持续运行时长。
- 涉及市电、UPS、电池的改动必须说明安全边界；不要提交需要市电改装的方案。
- 3D 打印件请注明材料、层高、壁厚、支撑与公差；未实测的模型明确标注 `reference only`。

## 数据与隐私

- benchmark 只使用合成数据或已获授权的公开数据集；在 `docs/BENCHMARKS.md` 记录来源与许可证。
- 不提交含人脸、工牌、客户现场标识的原始素材。
- 交付目标（S3/MinIO）由部署方配置；默认不上传任何第三方服务。

## Good first issues

- LeRobotDataset v3 exporter
- 带宽限速与优先级队列
- ZNS/SLC SSD 写入缓冲适配
- Dashboard 会话筛选与 episode 详情页
- ESP32 OLED 状态页
- 2.5GbE / 10GbE 实测 benchmark

## 许可证

提交即表示你同意：

- 软件贡献按 Apache-2.0 授权；
- 硬件设计贡献按 CERN-OHL-S-2.0 授权；
- 你有权提交该内容，且不侵犯第三方权利。
