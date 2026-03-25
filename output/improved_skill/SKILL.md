---
name: it-customer-service
description: IT客服助手，当用户咨询IT服务场景的问题时触发。使用skill和工具解答问题，包括query理解改写、意图识别、语义记忆检索、案例库查询、知识图谱检索、web搜索、自定义LLM应答、生成推理回答等工具。
---

# IT Customer Service Skill

处理IT服务场景的用户咨询问题，调用多种工具完成问题解答。

## 触发条件

当用户提到以下内容时自动触发：
- 账号相关问题（登录、密码、权限）
- 网络连接问题
- 软件/硬件故障
- 打印机问题
- 邮件系统问题
- 数据库连接问题
- 其他IT技术支持请求

## 工作流程

```
用户问题 -> Query改写 -> 意图识别 -> 技能加载 -> 语义检索
    -> 案例库查询 -> 知识图谱 -> Web搜索 -> LLM生成回答
```

## 可用工具

### 1. query_rewriter
改写用户query，使其更清晰准确

### 2. intent_classifier
识别用户意图，分类为：
- account_issue (账号问题)
- network_issue (网络问题)
- software_issue (软件问题)
- hardware_issue (硬件问题)
- permission_issue (权限问题)

### 3. skill_orchestrator
加载相关技能模块：
- windows_troubleshooting
- network_diagnostics
- account_management
- software_installer
- printer_config
- security_reset
- vpn_connector
- email_fixer
- permission_granter

### 4. semantic_memory_retrieval
从语义记忆中检索相似案例和解决方案

### 5. case_base_search
从案例库中搜索历史解决方案

### 6. knowledge_graph_query
查询知识图谱获取系统状态和关联信息

### 7. web_search
搜索最新KB文章和技术文档

### 8. read_file
读取故障排除文档

### 9. llm_response_generator
使用LLM生成最终回答

## 使用方式

```bash
# 运行IT客服agent
python scripts/it_agent.py "账号密码错误无法登录"
```

或通过skill调用：
```
使用it-customer-service skill处理: 我的VPN连接不上
```

## 配置

在 `config/default.yaml` 中配置：

```yaml
agent:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000

skills:
  enabled:
    - windows_troubleshooting
    - network_diagnostics
    - account_management
```

## 输出格式

返回结构化响应：
- 问题分类
- 可能原因
- 解决步骤
- 后续行动建议
