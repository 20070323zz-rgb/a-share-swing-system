# launchd catchup bugfix report

- 修复时间：2026-06-10 18:42
- 权限等级：L2 联网数据权限
- 范围：本地 launchd/catchup 自动化脚本修复
- 安全边界：不接券商 API，不真实下单，不读取真实账户，不保存密码/token，不修改交易规则，不修改仓位规则，不新增模拟交易

## 1. 错误原因

`scripts/run_catchup_check.sh` 使用 `set -u`，launchd 自动运行时没有传入命令行参数，脚本在空数组场景下展开 `${ARGS[*]}`，触发：

```text
ARGS[*]: unbound variable
```

这属于 shell 空数组展开兼容问题，不是 `src/automation_scheduler.py` 的调度规则错误。

## 2. 修复方式

- 在使用 `ARGS` 前显式初始化：`ARGS=()`。
- 手动无参数运行时，如果 `AUTOMATION_CATCHUP_REAL` 不是 `1`，继续自动添加 `--dry-run`。
- launchd 自动运行时，如果 plist 环境变量启用真实 catchup，则不注入 `--dry-run`。
- 日志输出使用安全的 `ARGS_TEXT="${ARGS[*]-}"`。
- 调用 Python 时区分空参数数组和非空参数数组，避免再次触发 `set -u`。

## 3. 验证命令

已执行并通过：

```bash
bash -n scripts/run_catchup_check.sh scripts/run_daily_close.sh
python3 -m py_compile scripts/update_etf_data.py src/automation_scheduler.py src/automation_state.py
python3 src/automation_scheduler.py --mode status
python3 src/automation_scheduler.py --mode catchup --dry-run
bash scripts/run_catchup_check.sh
```

## 4. 验证结果

- 手动运行 `bash scripts/run_catchup_check.sh`：成功，默认 dry-run。
- `logs/catchup_check.log` 中修复后的新记录不再出现 `ARGS[*]: unbound variable`。
- `logs/launchd_catchup_check.err.log`：无新增错误输出。
- 18:30 的 catchup 自动运行记录显示脚本可正常进入 scheduler。

## 5. 是否保持原设计

- 手动运行默认 dry-run：yes。
- launchd 通过环境变量启用真实 catchup：yes。
- 不重复执行已经 success 的节点：由 `automation_state.json` 和 `is_success()` 继续控制。
- 不重复写 `paper_trades.csv` / `paper_positions.csv`：catchup 不直接写交易，只调用既有脚本；模拟交易幂等逻辑保持不变。

## 6. 是否需要重新安装 launchd

本轮没有修改 plist 文件，只修改了 launchd 调用的 shell 脚本内容。因此不需要重新安装 launchd job。

如未来修改 plist，再运行：

```bash
cd /Users/dayin/Code/a-share-swing-system && bash scripts/install_launchd_jobs.sh
```

## 7. L2 边界确认

- 不接券商交易 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不修改交易规则。
- 不修改仓位规则。
- 不新增模拟交易。
