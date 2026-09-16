# BestSign 智能法务插件市场（legal-plugins）

BestSign Legal AI 的插件市场仓，当前提供 **deep-review（合同深度审查）** 技能：上传本地合同（Word/PDF），按立场/法域/语言执行大模型深度风险审查，下载结构化审查报告。

## 安装（Qoder CLI）

```bash
qodercli plugins marketplace add https://github.com/bestsign-plugins/legal-plugins
qodercli plugins install legal-ai
```

装好后在 Qoder 会话里执行 `/plugins reload`，即可使用 deep-review。

## 首次使用

首次调用会弹出 OAuth 授权页，完成登录与授权后即可审查；授权一次，后续复用。

## 说明

- 当前指向**生产环境**端点，面向全部客户开放。
- 本仓内容由构建脚本从单一元信息源注入，请勿手改产物；改 `src/legal-ai/plugin.meta.json` 后重新构建。
