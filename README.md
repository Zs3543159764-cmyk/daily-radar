# 五份免费云端日报 → 微信

**当前是可部署程序，不代表你的账号已完成模型调用或微信送达实测。** 2026-10-14 本地已验证五个主题的实时采集和关键逻辑。详细证据见 `VALIDATION.md`。

## 运行路线和费用边界

公开 GitHub 仓库的标准 Linux Actions 定时运行 → RSS／公开 GitHub 数据 → OpenRouter 免费模型 → PushPlus 微信接口。无需电脑常开，不用 ChatGPT 定时任务，不经过 Gmail，不调用 OpenAI 付费 API。

没有试用后自动付费逻辑。程序只接受 ID 以 `:free` 结尾或 `openrouter/free` 的模型，并每次核验模型目录所有已列出的价格字段都为零；供应商 prompt/completion 价格上限也设为零。不启用付费联网搜索、工具、插件或付费模型回退。若服务端违反声明返回非零费用，后续模型调用锁定，需要人工排查。不要为本项目充值、绑定自动充值或启用 GitHub 付费运行器。

免费不是稳定性保证：OpenRouter 当前免费账号 50 请求／天，本程序最多 20 请求／UTC 日，每个主题最多两次尝试，正常约 5—10 次／日；其他客户端会共享账号额度。免费模型可能限流、下架。公开仓库 Actions 定时任务可能延迟，60 天无仓库活动时可能自动停用；本程序有日常状态提交，但仍应检查 Actions 是否启用。历史状态分支或状态持久化失败会影响去重和增量计算。

## 五个主题

- AI／科技／大模型：10:30
- 东亚文化／书法／艺术设计：12:00
- 全球地缘政治：16:30
- 商业金融市场：19:30
- GitHub 每日热门项目：22:30

以上是根据已有聊天中时间顺序整理的部署默认值，**不是读取当前 ChatGPT 后台任务配置所得**。全部使用北京时间。修改 `config.json` 时间时也必须同步修改 workflow 的 UTC cron 和 SLOT 映射。没有修改或删除现有 ChatGPT 任务。

GitHub 提示词根据原聊天完整要求整理。其他四份提示词根据已读取的报告和主题重建，不能宣称逐字复制原任务。

## 部署步骤

1. 将本目录中的源码放在一个 **Public** 仓库根目录，保留 `.github/workflows/daily-radar.yml`。公开的是代码和公开仓库数据，不要上传个人文件、`.env`、密钥或本地报告。默认不启用定时发送。
2. 在 OpenRouter 免费账号创建 API Key。前往 GitHub 仓库 **Settings → Secrets and variables → Actions → Secrets**，添加：
   - `OPENROUTER_API_KEY`：OpenRouter 密钥。
   - `PUSHPLUS_TOKEN`：PushPlus 用户或消息令牌，默认只推给本人，不配置群组。
   - 可选 `PUSHPLUS_SECRET_KEY`：PushPlus 用户密钥，用于查询最终投递结果；必须配合用户 Token，消息 Token 不支持该查询。
   密钥只填 GitHub Secrets；不要放在代码、issue、聊天、README 或 workflow 普通变量中。
3. **Actions → Five daily radars (free only) → Run workflow**：先选择 `ai` + `collect-only`，检查运行 Summary 中的原始材料。
4. 选择 `ai` + `generate-preview`，实测免费模型，检查中文质量、来源链接、时效。再用 `all` + `generate-preview` 检查全部五份。该模式不会推微信。
5. 检查后选择 `ai` + `send`，这一步会向自己的微信发消息。PushPlus 返回受理不等于送达：提供可选用户密钥后程序查询最终状态；未提供时应在 PushPlus 消息列表和微信中确认。
6. 全链路成功后，在 **Settings → Secrets and variables → Actions → Variables** 添加 `RADAR_ENABLED`，值为 `true`。至此才开启每日自动发送。将它改成 `false` 可停用定时发送；也可直接 Disable workflow。

不要先删原来的 ChatGPT 任务，等新系统稳定运行后再决定。

## 采集和质量的实际边界

- 新闻主要来自公开 RSS 和 Google News 检索摘要；未自动读取付费全文，没有把“标题线索”视为独立核实。每份报告会列出采集覆盖和失败来源。
- 新闻默认使用 48 小时窗口；书法艺术使用 7 天窗口。无日期、过旧或未来材料会被排除；某来源返回零条不等于请求失败。
- 地缘政治和金融材料不足时必须标“待核实”，不能凭模型记忆补写伤亡、行情或细节。
- 书法小众来源和社交平台图片覆盖有限，无法承诺原 ChatGPT 报告的全面性。可在 `config.json` 增加可靠的官方 RSS。
- GitHub 从 Trending 和分类检索构建候选池，**不是全站完整排名**。分类检索按 Star 发现候选，排序分值 = 正 24h 增量 + 正 7d 增量/7 + 最近推送活跃度（0—7）+ Trending 位次项（最高 200）。不直接以历史 Star 总数排序；第一天尚无增量数据，排序参考有限。
- 24h／7d 增量来自实际快照。24h 基准误差允许 ±6 小时；7d ±24 小时。缺少基准写“暂无可靠数据”。目前没有采集 Commit 数量、Release、Issue/PR 活跃度，也不能仅凭描述验证创新性或刷 Star。
- 若模型限流、输出截断、生成未提供的链接或不满足基础校验，降级为带明显标签的原始资讯汇总，同时 Actions 显示失败。来源链接检查不是事实正确性的充分保证。
- 长文自动按最多 9000 字分条，避免正文截断。生成正文与来源可能超过手机通知预览长度，需要在微信打开消息查看。

## 历史、去重和公开信息

`radar-state` 分支持久保存公开 Star 快照、模型调用次数、发送状态和正文哈希；**不保存 Token、模型密钥、用户密钥、报告正文或 PushPlus 消息短链码**。避免删除该分支，删除后系统无法知道过去哪些报告已发送。

同日同主题同分段只发送一次。超时后发送结果不明时停止自动重发，避免重复；需先检查 PushPlus 消息列表再人工处理 `pending` 记录。模型重生成内容发生变化时仍不会重发已受理的同日分段。被拒绝或最终失败也需人工核查后处理，不盲目循环。

GitHub Actions 的日志和 Summary 在公开仓库可能公开：仅包含公开采集数据和生成的资讯报告。不要将此程序改为读私人邮件或私人文件后继续沿用公开仓库。Key 永远不输出。

## 本地验证

要求 Python 3.9+（推荐 3.12），没有第三方依赖。

```bash
python3 radar.py --validate
python3 -m unittest test_radar -v
python3 radar.py --topic all --collect-only
```

本地输出在 `reports/`，采集状态在 `state/`，默认被 `.gitignore` 排除。本地不会自动读取 `.env`；如需调用模型，应通过环境变量安全提供密钥。`--send` 必须显式传入，且要求两个必填密钥都已配置。

## 官方依据（核查于 2026-10-14）

- GitHub 免费标准运行器：https://docs.github.com/en/billing/concepts/product-billing/github-actions
- GitHub 定时限制：https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- OpenRouter 免费额度：https://openrouter.ai/pricing
- 免费路由：https://openrouter.ai/openrouter/free
- OpenRouter 额度查询：https://openrouter.ai/docs/api_reference/limits
- PushPlus 发送限制：https://www.pushplus.plus/doc/help/limit.html
- PushPlus 消息接口：https://pushplus.plus/doc/guide/api.html
- PushPlus 最终投递状态：https://pushplus.plus/doc/guide/openApi.html
