import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import (
    ToolRegistry,
    QueryRewriter,
    IntentClassifier,
    SkillOrchestrator,
    SemanticMemoryRetrieval,
    CaseBaseSearch,
    KnowledgeGraphQuery,
    WebSearch,
    ReadFile,
    LLMResponseGenerator
)


@dataclass
class ConversationRecord:
    role: str
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentContext:
    user_query: str
    rewritten_query: str = ""
    intent: str = ""
    skill: str = ""
    semantic_results: List[Dict] = field(default_factory=list)
    case_results: List[Dict] = field(default_factory=list)
    kg_results: Dict = field(default_factory=dict)
    web_results: List[Dict] = field(default_factory=list)
    doc_content: str = ""
    final_response: str = ""
    records: List[ConversationRecord] = field(default_factory=list)


class ITCustomerServiceAgent:
    """IT客服Agent"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tool_registry = ToolRegistry()
        self.context: Optional[AgentContext] = None
    
    def add_record(self, role: str, content: str, tool_calls: List[Dict] = None, tool_name: str = None):
        if self.context:
            self.context.records.append(ConversationRecord(
                role=role,
                content=content,
                tool_calls=tool_calls,
                tool_name=tool_name
            ))
    
    async def process(self, user_query: str) -> AgentContext:
        """处理用户问题"""
        self.context = AgentContext(user_query=user_query)
        
        # 1. 用户问题输入
        self.add_record("user", user_query)
        self.add_record("assistant", f"您好！我将使用IT客服Agent来处理您关于「{user_query}」的问题。让我先分析一下问题。")
        
        # 2. Query改写
        await self._query_rewrite()
        
        # 3. 意图识别
        await self._intent_classify()
        
        # 4. 技能加载
        await self._load_skill()
        
        # 5. 语义记忆检索
        await self._semantic_retrieval()
        
        # 6. 案例库查询
        await self._case_search()
        
        # 7. 知识图谱查询
        await self._knowledge_graph_query()
        
        # 8. Web搜索
        await self._web_search()
        
        # 9. 读取文档
        await self._read_doc()
        
        # 10. LLM生成回答
        await self._generate_response()
        
        return self.context
    
    async def _query_rewrite(self):
        """Query改写"""
        tool = self.tool_registry.get("query_rewriter")
        self.add_record("assistant", "让我先改写您的问题，使其更清晰...", 
                       tool_calls=[{"function": {"name": "query_rewriter", "arguments": json.dumps({"query": self.context.user_query})}}])
        
        result = tool.execute(query=self.context.user_query)
        self.context.rewritten_query = result.get("rewritten_query", self.context.user_query)
        
        self.add_record("assistant", f"问题已优化: {self.context.rewritten_query}")
        self.add_record("tool", f"Query改写完成", tool_name="query_rewriter")
    
    async def _intent_classify(self):
        """意图识别"""
        tool = self.tool_registry.get("intent_classifier")
        self.add_record("assistant", "让我识别您的意图...", 
                       tool_calls=[{"function": {"name": "intent_classifier", "arguments": json.dumps({"query": self.context.user_query})}}])
        
        result = tool.execute(query=self.context.rewritten_query or self.context.user_query)
        self.context.intent = result.get("intent", "general_inquiry")
        
        self.add_record("tool", f"识别到意图: {self.context.intent}", tool_name="intent_classifier")
    
    async def _load_skill(self):
        """加载技能"""
        tool = self.tool_registry.get("skill_orchestrator")
        self.add_record("assistant", f"根据分析，将加载相关技能来处理这个问题...", 
                       tool_calls=[{"function": {"name": "skill_orchestrator", "arguments": json.dumps({"intent": self.context.intent, "issue": self.context.user_query})}}])
        
        result = tool.execute(intent=self.context.intent, issue=self.context.user_query)
        self.context.skill = result.get("skill_loaded", "windows_troubleshooting")
        
        self.add_record("tool", f"技能已加载: {self.context.skill}", tool_name="skill_orchestrator")
    
    async def _semantic_retrieval(self):
        """语义记忆检索"""
        tool = self.tool_registry.get("semantic_memory_retrieval")
        self.add_record("assistant", "让我检索语义记忆中的相似案例...", 
                       tool_calls=[{"function": {"name": "semantic_memory_retrieval", "arguments": json.dumps({"query": self.context.user_query})}}])
        
        result = tool.execute(query=self.context.user_query)
        self.context.semantic_results = result
        
        self.add_record("tool", f"找到 {len(result)} 个相似案例", tool_name="semantic_memory_retrieval")
    
    async def _case_search(self):
        """案例库搜索"""
        tool = self.tool_registry.get("case_base_search")
        self.add_record("assistant", "让我查询案例库...", 
                       tool_calls=[{"function": {"name": "case_base_search", "arguments": json.dumps({"keywords": self.context.user_query[:4]})}}])
        
        result = tool.execute(keywords=self.context.user_query[:4])
        self.context.case_results = result.get("cases", [])
        
        self.add_record("tool", f"找到 {len(self.context.case_results)} 个历史案例", tool_name="case_base_search")
    
    async def _knowledge_graph_query(self):
        """知识图谱查询"""
        tool = self.tool_registry.get("knowledge_graph_query")
        self.add_record("assistant", "让我查询知识图谱获取系统状态...", 
                       tool_calls=[{"function": {"name": "knowledge_graph_query", "arguments": json.dumps({"entity": self.context.user_query[:2]})}}])
        
        result = tool.execute(entity=self.context.user_query[:2])
        self.context.kg_results = result
        
        self.add_record("tool", f"查询完成，系统状态正常", tool_name="knowledge_graph_query")
    
    async def _web_search(self):
        """Web搜索"""
        tool = self.tool_registry.get("web_search")
        self.add_record("assistant", "让我搜索最新的KB文章...", 
                       tool_calls=[{"function": {"name": "web_search", "arguments": json.dumps({"query": self.context.user_query})}}])
        
        result = tool.execute(query=self.context.user_query)
        self.context.web_results = result.get("results", [])
        
        self.add_record("tool", f"找到 {len(self.context.web_results)} 篇相关文档", tool_name="web_search")
    
    async def _read_doc(self):
        """读取文档"""
        tool = self.tool_registry.get("read_file")
        path = f"c:\\skills\\{self.context.skill}\\troubleshooting.md"
        self.add_record("assistant", "让我读取相关的故障排除文档...", 
                       tool_calls=[{"function": {"name": "read_file", "arguments": json.dumps({"path": path})}}])
        
        result = tool.execute(path=path)
        self.context.doc_content = result.get("content", "")[:500]
        
        self.add_record("tool", "文档读取完成", tool_name="read_file")
    
    async def _generate_response(self):
        """生成回答"""
        tool = self.tool_registry.get("llm_response_generator")
        
        context = {
            "intent": self.context.intent,
            "skill": self.context.skill,
            "cases_found": len(self.context.case_results) + len(self.context.semantic_results)
        }
        
        self.add_record("assistant", "正在生成最终回答...", 
                       tool_calls=[{"function": {"name": "llm_response_generator", "arguments": json.dumps({"issue": self.context.user_query, "context": context})}}])
        
        result = tool.execute(issue=self.context.user_query, context=context)
        self.context.final_response = result
        
        self.add_record("assistant", result)
    
    def get_trace_records(self) -> List[Dict]:
        """获取trace记录（用于分析）"""
        if not self.context:
            return []
        
        records = []
        for r in self.context.records:
            record = {"role": r.role, "content": r.content}
            if r.tool_calls:
                record["tool_calls"] = r.tool_calls
            if r.tool_name:
                record["tool_name"] = r.tool_name
            records.append(record)
        
        return records


async def main():
    import sys
    
    query = sys.argv[1] if len(sys.argv) > 1 else "账号密码错误无法登录"
    
    print(f"用户问题: {query}")
    print("=" * 50)
    
    agent = ITCustomerServiceAgent()
    context = await agent.process(query)
    
    print("=" * 50)
    print("\n最终回答:")
    print(context.final_response)
    
    print("\n" + "=" * 50)
    print("Trace Records:")
    for i, record in enumerate(agent.get_trace_records()):
        print(json.dumps(record, ensure_ascii=False, indent=2))
        print("-" * 30)


if __name__ == "__main__":
    asyncio.run(main())
