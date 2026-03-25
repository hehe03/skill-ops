#!/bin/bash
# Initialize IT Customer Service Agent project

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SKILL_DIR")"

TARGET_DIR="${1:-.}"

echo "Initializing IT Customer Service Agent at: $TARGET_DIR"

mkdir -p "$TARGET_DIR"/{scripts,tools,output}

# Copy tools
cp -r "$SKILL_ROOT/tools" "$TARGET_DIR/"

# Copy scripts
cp "$SKILL_ROOT/scripts/it_agent.py" "$TARGET_DIR/scripts/"

# Create config
cat > "$TARGET_DIR/config.yaml" << 'CONFIGEOF'
agent:
  name: "IT客服Agent"
  version: "1.0.0"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000

skills:
  enabled:
    - windows_troubleshooting
    - network_diagnostics
    - account_management
    - software_installer
    - printer_config
    - security_reset
    - vpn_connector
    - email_fixer
    - permission_granter

tools:
  query_rewriter:
    enabled: true
  intent_classifier:
    enabled: true
  skill_orchestrator:
    enabled: true
  semantic_memory_retrieval:
    enabled: true
  case_base_search:
    enabled: true
  knowledge_graph_query:
    enabled: true
  web_search:
    enabled: true
  read_file:
    enabled: true
  llm_response_generator:
    enabled: true
CONFIGEOF

echo ""
echo "Project initialized successfully!"
echo ""
echo "Usage:"
echo "  python scripts/it_agent.py \"账号密码错误无法登录\""
echo "  python scripts/it_agent.py \"VPN连接失败\""
echo "  python scripts/it_agent.py \"打印机无法使用\""
echo ""
