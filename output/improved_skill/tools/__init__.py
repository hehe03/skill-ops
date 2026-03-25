import json
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    result: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": "assistant",
            "content": f"Calling tool: {self.tool_name}",
            "tool_calls": [{
                "id": f"call_{random.randint(1000, 9999)}",
                "type": "function",
                "function": {
                    "name": self.tool_name,
                    "arguments": json.dumps(self.arguments, ensure_ascii=False)
                }
            }]
        }
    
    def to_result(self) -> Dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": f"call_{random.randint(1000, 9999)}",
            "tool_name": self.tool_name,
            "content": str(self.result) if self.result else "Done"
        }


class BaseTool:
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, **kwargs) -> Any:
        raise NotImplementedError
    
    def __call__(self, **kwargs) -> Any:
        return self.execute(**kwargs)


class QueryRewriter(BaseTool):
    """Query改写工具"""
    
    def __init__(self):
        super().__init__("query_rewriter")
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        rewritten = self._rewrite(query)
        return {
            "original_query": query,
            "rewritten_query": rewritten,
            "language": "zh-CN"
        }
    
    def _rewrite(self, query: str) -> str:
        rewrites = {
            "登录不上": "用户登录认证失败",
            "连不上": "网络连接失败",
            "打不开": "应用程序启动失败",
            "不能用": "服务不可用",
            "错误": "系统错误",
            "很慢": "性能问题"
        }
        for old, new in rewrites.items():
            if old in query:
                return query.replace(old, new)
        return query


class IntentClassifier(BaseTool):
    """意图识别工具"""
    
    def __init__(self):
        super().__init__("intent_classifier")
    
    def execute(self, query: str, context: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        intent = self._classify(query)
        return {
            "query": query,
            "intent": intent,
            "confidence": 0.92,
            "sub_intent": self._get_sub_intent(intent)
        }
    
    def _classify(self, query: str) -> str:
        keywords = {
            "account_issue": ["登录", "密码", "账号", "权限", "锁定", "LDAP"],
            "network_issue": ["网络", "WiFi", "VPN", "连接", "DNS", "掉线"],
            "software_issue": ["软件", "启动", "崩溃", "版本", "安装"],
            "hardware_issue": ["打印机", "硬件", "设备", "电脑", "显示器"],
            "email_issue": ["邮件", "邮箱", "收发", "附件"],
            "permission_issue": ["权限", "访问", "共享", "管理员"]
        }
        
        for intent, words in keywords.items():
            for word in words:
                if word in query:
                    return intent
        return "general_inquiry"
    
    def _get_sub_intent(self, intent: str) -> str:
        sub_intents = {
            "account_issue": random.choice(["password_reset", "account_locked", "ldap_failure"]),
            "network_issue": random.choice(["wifi_fail", "vpn_fail", "dns_error"]),
            "software_issue": random.choice(["app_crash", "install_fail", "version_mismatch"]),
            "hardware_issue": random.choice(["printer_offline", "device_not_found"]),
            "email_issue": random.choice(["send_fail", "receive_fail", "attachment_fail"])
        }
        return sub_intents.get(intent, "general")


class SkillOrchestrator(BaseTool):
    """技能编排器"""
    
    SKILLS = {
        "account_issue": "account_management",
        "network_issue": "network_diagnostics",
        "software_issue": "software_installer",
        "hardware_issue": "windows_troubleshooting",
        "email_issue": "email_fixer",
        "permission_issue": "permission_granter"
    }
    
    def __init__(self):
        super().__init__("skill_orchestrator")
    
    def execute(self, skill: str = None, intent: str = None, issue: str = None, **kwargs) -> Dict[str, Any]:
        selected_skill = skill or self.SKILLS.get(intent, "windows_troubleshooting")
        
        return {
            "skill_loaded": selected_skill,
            "status": "loaded",
            "issue": issue,
            "available_tools": self._get_skill_tools(selected_skill)
        }
    
    def _get_skill_tools(self, skill: str) -> List[str]:
        skill_tools = {
            "account_management": ["ad_query", "password_reset", "account_unlock"],
            "network_diagnostics": ["ping_test", "traceroute", "dns_check"],
            "software_installer": ["check_version", "download_pkg", "install"],
            "printer_config": ["list_printers", "install_driver", "test_print"]
        }
        return skill_tools.get(skill, ["generic_tool"])


class SemanticMemoryRetrieval(BaseTool):
    """语义记忆检索"""
    
    def __init__(self):
        super().__init__("semantic_memory_retrieval")
        self._memory = self._init_memory()
    
    def execute(self, query: str, top_k: int = 3, **kwargs) -> List[Dict[str, Any]]:
        results = []
        for item in self._memory:
            if any(word in item["issue"] for word in query):
                results.append({
                    **item,
                    "similarity": random.uniform(0.7, 0.95)
                })
        
        results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def _init_memory(self) -> List[Dict[str, Any]]:
        return [
            {"issue": "密码错误", "solution": "通过AD自助服务重置密码", "cases": 45},
            {"issue": "账号锁定", "solution": "联系IT管理员解锁账号", "cases": 32},
            {"issue": "VPN连接失败", "solution": "检查网络并重新连接VPN", "cases": 28},
            {"issue": "打印机脱机", "solution": "检查网络连接并重启打印机", "cases": 21},
            {"issue": "软件崩溃", "solution": "清除缓存并重新启动应用", "cases": 18}
        ]


class CaseBaseSearch(BaseTool):
    """案例库查询"""
    
    def __init__(self):
        super().__init__("case_base_search")
        self._cases = self._init_cases()
    
    def execute(self, keywords: str, category: str = None, **kwargs) -> Dict[str, Any]:
        matching_cases = []
        for case in self._cases:
            if keywords in case["title"] or keywords in case["keywords"]:
                matching_cases.append(case)
        
        return {"cases": matching_cases[:5], "total": len(matching_cases)}
    
    def _init_cases(self) -> List[Dict[str, Any]]:
        return [
            {"id": "CASE-2024-001", "title": "密码过期处理", "keywords": ["密码", "过期"], "resolution": "通过AD自助服务重置", "category": "account"},
            {"id": "CASE-2024-002", "title": "账号锁定解锁", "keywords": ["锁定", "解锁"], "resolution": "IT管理员手动解锁", "category": "account"},
            {"id": "CASE-2024-003", "title": "VPN连接超时", "keywords": ["VPN", "超时"], "resolution": "检查网络并重新认证", "category": "network"},
            {"id": "CASE-2024-004", "title": "打印机驱动安装", "keywords": ["打印机", "驱动"], "resolution": "下载并安装对应驱动", "category": "hardware"},
            {"id": "CASE-2024-005", "title": "邮件发送失败", "keywords": ["邮件", "发送"], "resolution": "检查发件箱并重试", "category": "email"}
        ]


class KnowledgeGraphQuery(BaseTool):
    """知识图谱查询"""
    
    def __init__(self):
        super().__init__("knowledge_graph_query")
    
    def execute(self, entity: str, **kwargs) -> Dict[str, Any]:
        return {
            "entities": [
                {"type": "service", "name": "AD域控", "status": "online", "last_check": datetime.now().isoformat()},
                {"type": "service", "name": "VPN服务", "status": "online", "last_check": datetime.now().isoformat()},
                {"type": "service", "name": "邮件服务", "status": "online", "last_check": datetime.now().isoformat()}
            ],
            "relations": self._get_relations(entity)
        }
    
    def _get_relations(self, entity: str) -> List[Dict[str, Any]]:
        return [
            {"source": "用户", "target": "AD域控", "type": "authenticates_with", "status": "normal"},
            {"source": "用户", "target": "VPN服务", "type": "connects_to", "status": "normal"},
            {"source": "AD域控", "target": "LDAP", "type": "uses", "status": "normal"}
        ]


class WebSearch(BaseTool):
    """Web搜索"""
    
    def __init__(self):
        super().__init__("web_search")
    
    def execute(self, query: str, site: str = None, **kwargs) -> Dict[str, Any]:
        return {
            "results": [
                {
                    "title": f"KB-{random.randint(5000, 9999)}: {query}问题解决指南",
                    "url": f"https://support.example.com/kb/{random.randint(100, 999)}",
                    "snippet": f"解决{query}问题的详细步骤..."
                },
                {
                    "title": f"常见问题: {query}",
                    "url": "https://faq.example.com",
                    "snippet": f"关于{query}的常见问题解答"
                }
            ],
            "total_results": 2
        }


class ReadFile(BaseTool):
    """读取文档"""
    
    def __init__(self):
        super().__init__("read_file")
    
    def execute(self, path: str, **kwargs) -> Dict[str, Any]:
        docs = {
            "troubleshooting": self._get_troubleshooting_doc(),
            "account": self._get_account_doc(),
            "network": self._get_network_doc()
        }
        
        key = path.split("/")[-1].replace(".md", "").replace("troubleshooting", "troubleshooting")
        
        return {
            "path": path,
            "content": docs.get(key, docs["troubleshooting"]),
            "lines": 50
        }
    
    def _get_troubleshooting_doc(self) -> str:
        return """# 故障排除指南

## 常见问题排查步骤

1. 确认问题现象
2. 检查网络连接
3. 查看系统日志
4. 重启相关服务
5. 如仍未解决，请联系IT支持

## 快速诊断命令

- ping: 测试网络连通性
- ipconfig: 查看IP配置
- netstat: 查看网络连接状态
"""
    
    def _get_account_doc(self) -> str:
        return """# 账号管理指南

## 密码重置

1. 访问自助服务门户
2. 验证身份
3. 设置新密码
4. 确认重置成功

## 账号解锁

请联系IT管理员或提交工单
"""
    
    def _get_network_doc(self) -> str:
        return """# 网络问题排查

## VPN连接问题

1. 检查本地网络
2. 尝试断开重连
3. 清除VPN缓存
4. 检查证书有效期
"""


class LLMResponseGenerator(BaseTool):
    """LLM回答生成"""
    
    def __init__(self, llm_client=None):
        super().__init__("llm_response_generator")
        self.llm_client = llm_client
    
    def execute(self, issue: str, context: Dict[str, Any], **kwargs) -> str:
        skill = context.get("skill", "通用")
        cases = context.get("cases_found", 0)
        
        response = f"""根据您遇到的「{issue}」问题，我为您准备了以下解决方案：

## 问题分类
{context.get('intent', 'IT支持问题')}

## 可能原因
1. 系统服务异常
2. 账号状态问题
3. 网络连接问题

## 解决步骤
1. 请先尝试重启相关服务
2. 如问题持续，请联系IT支持

## 后续行动
- 如需人工帮助，请点击「转人工服务」
- 更多知识库文章，请访问IT支持门户

---
感谢您的咨询，祝您工作愉快！
"""
        return response


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register(QueryRewriter())
        self.register(IntentClassifier())
        self.register(SkillOrchestrator())
        self.register(SemanticMemoryRetrieval())
        self.register(CaseBaseSearch())
        self.register(KnowledgeGraphQuery())
        self.register(WebSearch())
        self.register(ReadFile())
        self.register(LLMResponseGenerator())
    
    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
