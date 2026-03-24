#!/usr/bin/env python3
"""
生成IT客服场景的Agent Trace测试数据
主题：agent使用skill和工具解答IT领域客服问题
"""
import json
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any


IT_ISSUES = [
    ("账号密码错误无法登录", ["账号锁定", "密码过期", "忘记密码", "LDAP认证失败"]),
    ("网络连接不上", ["WiFi无法连接", "VPN连接失败", "网络掉线", "DNS错误"]),
    ("打印机无法使用", ["打印机脱机", "打印任务卡住", "驱动丢失", "打印空白"]),
    ("软件无法启动", ["应用程序崩溃", "许可到期", "缺少DLL", "版本不兼容"]),
    ("邮件收发异常", ["邮件发送失败", "收不到邮件", "邮件延迟", "附件无法打开"]),
    ("文件无法访问", ["权限不足", "文件被占用", "磁盘空间不足", "路径不存在"]),
    ("账户权限不足", ["需要管理员权限", "无法访问共享目录", "功能灰显"]),
    ("系统运行缓慢", ["CPU占用高", "内存不足", "磁盘IO瓶颈", "恶意软件"]),
    ("视频会议无法进入", ["会议链接失效", "音视频设备异常", "带宽不足"]),
    ("数据库连接失败", ["连接超时", "服务不可用", "防火墙阻止"]),
]

TOOLS = [
    "query_rewriter",
    "intent_classifier",
    "semantic_memory_retrieval",
    "case_base_search",
    "knowledge_graph_query",
    "web_search",
    "llm_response_generator",
    "skill_orchestrator",
    "read_file",
    "execute_shell",
    "database_query",
    "api_gateway",
]

SKILLS = [
    "windows_troubleshooting",
    "network_diagnostics",
    "account_management",
    "software_installer",
    "printer_config",
    "security_reset",
    "vpn_connector",
    "email_fixer",
    "permission_granter",
]


def generate_tool_call_record(tool_name: str, arguments: str, result: str = "") -> Dict[str, Any]:
    """生成tool调用记录"""
    record = {
        "role": "tool",
        "tool_call_id": f"call_{random.randint(1000, 9999)}",
        "tool_name": tool_name,
        "content": result if result else f"Executed {tool_name} with args: {arguments}"
    }
    return record


def generate_skill_use_record(skill_name: str, issue: str) -> Dict[str, Any]:
    """生成skill使用记录"""
    return {
        "role": "tool",
        "tool_call_id": f"call_{random.randint(1000, 9999)}",
        "tool_name": "skill_orchestrator",
        "content": f"Loading skill '{skill_name}' to handle: {issue}",
        "skill_loaded": skill_name
    }


def generate_trace(trace_id: int, issue: str, has_anomaly: bool = False) -> List[Dict[str, Any]]:
    """生成单条trace记录序列"""
    records = []
    
    issue_title, sub_issues = random.choice(IT_ISSUES)
    
    records.append({
        "role": "user",
        "content": issue_title
    })
    
    records.append({
        "role": "assistant",
        "content": f"我将使用IT客服Agent来处理您关于「{issue_title}」的问题。让我先分析一下问题并加载相关技能。",
        "tool_calls": [
            {
                "id": f"call_{random.randint(100, 999)}",
                "type": "function",
                "function": {
                    "name": "query_rewriter",
                    "arguments": json.dumps({"query": issue_title})
                }
            }
        ]
    })
    
    records.append(generate_tool_call_record("query_rewriter", f'{{"query": "{issue_title}"}}', 
        f'Query rewritten: {issue_title} -> 账号登录问题'))
    
    records.append({
        "role": "assistant",
        "content": "让我识别您的意图并检索相关解决方案...",
        "tool_calls": [
            {
                "id": f"call_{random.randint(100, 999)}",
                "type": "function",
                "function": {
                    "name": "intent_classifier",
                    "arguments": json.dumps({"query": issue_title, "context": {}})
                }
            }
        ]
    })
    
    intent_result = random.choice(["account_issue", "network_issue", "software_issue", "permission_issue"])
    records.append(generate_tool_call_record("intent_classifier", f'{{"query": "{issue_title}"}}',
        f'Intent identified: {intent_result}'))
    
    selected_skill = random.choice(SKILLS)
    records.append({
        "role": "assistant",
        "content": f"根据分析，我将加载「{selected_skill}」技能来处理这个问题。",
        "tool_calls": [
            {
                "id": f"call_{random.randint(100, 999)}",
                "type": "function",
                "function": {
                    "name": "skill_orchestrator",
                    "arguments": json.dumps({"skill": selected_skill, "issue": issue_title})
                }
            }
        ]
    })
    
    records.append(generate_skill_use_record(selected_skill, issue_title))
    
    records.append({
        "role": "assistant",
        "content": "技能已加载，让我检索语义记忆中的相似案例...",
        "tool_calls": [
            {
                "id": f"call_{random.randint(100, 999)}",
                "type": "function",
                "function": {
                    "name": "semantic_memory_retrieval",
                    "arguments": json.dumps({"query": issue_title, "top_k": 3})
                }
            }
        ]
    })
    
    memory_results = [
        {"issue": "密码错误", "solution": "重置密码", "similarity": 0.92},
        {"issue": "账号锁定", "solution": "联系IT解锁", "similarity": 0.85}
    ]
    records.append(generate_tool_call_record("semantic_memory_retrieval", f'{{"query": "{issue_title}"}}',
        json.dumps(memory_results)))
    
    if random.random() > 0.3:
        records.append({
            "role": "assistant",
            "content": "让我查询案例库...",
            "tool_calls": [
                {
                    "id": f"call_{random.randint(100, 999)}",
                    "type": "function",
                    "function": {
                        "name": "case_base_search",
                        "arguments": json.dumps({"keywords": issue_title.split()[0], "category": intent_result})
                    }
                }
            ]
        })
        
        case_result = {
            "cases": [
                {"id": "CASE-2024-001", "title": "密码过期处理", "resolution": "通过AD自助服务重置"},
                {"id": "CASE-2024-002", "title": "账号锁定解锁", "resolution": "IT管理员手动解锁"}
            ]
        }
        records.append(generate_tool_call_record(
            "case_base_search", 
            json.dumps({"keywords": issue_title.split()[0]}),
            json.dumps(case_result)
        ))
    
    if random.random() > 0.5:
        records.append({
            "role": "assistant",
            "content": "让我查询知识图谱获取更多关联信息...",
            "tool_calls": [
                {
                    "id": f"call_{random.randint(100, 999)}",
                    "type": "function",
                    "function": {
                        "name": "knowledge_graph_query",
                        "arguments": json.dumps({"entity": issue_title.split()[0]})
                    }
                }
            ]
        })
        
        kg_result = {
            "entities": [
                {"type": "service", "name": "AD域控", "status": "online"},
                {"type": "system", "name": "认证服务", "status": "normal"}
            ],
            "relations": [{"source": "用户", "target": "AD域控", "type": "authenticates_with"}]
        }
        records.append(generate_tool_call_record(
            "knowledge_graph_query", 
            json.dumps({"entity": issue_title.split()[0]}),
            json.dumps(kg_result)
        ))
    
    if random.random() > 0.6:
        records.append({
            "role": "assistant",
            "content": "让我搜索最新的KB文章...",
            "tool_calls": [
                {
                    "id": f"call_{random.randint(100, 999)}",
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "arguments": json.dumps({"query": issue_title, "site": "support.microsoft.com"})
                    }
                }
            ]
        })
        
        search_result = {"results": [{"title": "KB502xxx: 解决AD认证问题", "url": "https://..."}]}
        records.append(generate_tool_call_record(
            "web_search", 
            json.dumps({"query": issue_title}),
            json.dumps(search_result)
        ))
    
    records.append({
        "role": "assistant",
        "content": "让我读取相关的故障排除文档...",
        "tool_calls": [
            {
                "id": f"call_{random.randint(100, 999)}",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": json.dumps({"path": f"c:\\skills\\{selected_skill}\\troubleshooting.md"})
                }
            }
        ]
    })
    
    doc_content = f"""# {selected_skill} 故障排除指南

## 常见问题

### 账号密码错误
1. 检查账号是否锁定
2. 验证密码是否过期
3. 确认LDAP连接正常
4. 建议用户使用自助服务重置密码
"""
    records.append(generate_tool_call_record("read_file", 
        json.dumps({"path": f"c:\\skills\\{selected_skill}\\troubleshooting.md"}),
        doc_content[:200] + "..."))
    
    if has_anomaly:
        anomaly_type = random.choice(["high_latency", "error", "empty_response", "excessive_tokens"])
        
        if anomaly_type == "high_latency":
            records.append({
                "role": "assistant",
                "content": "正在执行诊断命令，请稍候...",
                "tool_calls": [
                    {
                        "id": "call_diag",
                        "type": "function",
                        "function": {
                            "name": "execute_shell",
                            "arguments": "ipconfig /all && netstat -an"
                        }
                    }
                ]
            })
            records.append({
                "role": "tool",
                "tool_call_id": "call_diag",
                "tool_name": "execute_shell",
                "content": "[模拟执行延迟...]",
                "latency_ms": random.randint(30000, 60000)
            })
        elif anomaly_type == "error":
            records.append({
                "role": "assistant",
                "content": "让我查询用户账号状态...",
                "tool_calls": [
                    {
                        "id": "call_db",
                        "type": "function",
                        "function": {
                            "name": "database_query",
                            "arguments": "SELECT * FROM users WHERE username='xxx'"
                        }
                    }
                ]
            })
            records.append({
                "role": "tool",
                "tool_call_id": "call_db",
                "tool_name": "database_query",
                "content": "Error: Connection timeout after 30s",
                "has_error": True,
                "error_type": "connection_timeout"
            })
        elif anomaly_type == "excessive_tokens":
            for _ in range(5):
                records.append({
                    "role": "assistant",
                    "content": "让我继续深入分析...",
                    "tool_calls": [
                        {
                            "id": f"call_{random.randint(100, 999)}",
                            "type": "function",
                            "function": {
                                "name": random.choice(TOOLS),
                                "arguments": "{}"
                            }
                        }
                    ]
                })
                records.append(generate_tool_call_record(random.choice(TOOLS), "{}", 
                    "Detailed analysis result..." * 50))
    
    records.append({
        "role": "assistant",
        "content": generate_solution(issue_title, selected_skill),
        "tool_calls": [
            {
                "id": f"call_{random.randint(100, 999)}",
                "type": "function",
                "function": {
                    "name": "llm_response_generator",
                    "arguments": json.dumps({
                        "issue": issue_title,
                        "context": {"skill": selected_skill, "cases_found": 2}
                    })
                }
            }
        ]
    })
    
    records.append(generate_tool_call_record("llm_response_generator", 
        json.dumps({"issue": issue_title}),
        f"Generated response for: {issue_title}"))
    
    return records


def generate_solution(issue: str, skill: str) -> str:
    """生成解决方案"""
    solutions = [
        f"根据我的分析，您遇到的「{issue}」问题可能是由于账号状态异常导致的。建议您：\n\n1. 尝试使用自助密码重置服务\n2. 如账号已锁定，请联系IT管理员解锁\n3. 检查网络连接是否正常\n4. 确认您的VPN是否需要重新认证\n\n如仍未解决，请提供更详细的问题描述。",
        f"针对「{issue}」问题，我为您准备了以下解决方案：\n\n1. 首先请确认账号未过期或被锁定\n2. 尝试清除浏览器缓存后重新登录\n3. 如使用VPN，请先断开后重新连接\n4. 检查本地网络 DNS 设置是否正确\n\n如需进一步帮助，请点击「转人工服务」。",
    ]
    return random.choice(solutions)


def generate_normal_traces(num: int, output_dir: Path) -> int:
    """生成正常trace"""
    count = 0
    for i in range(num):
        issue = random.choice(IT_ISSUES)[0]
        records = generate_trace(i, issue, has_anomaly=False)
        
        output_file = output_dir / f"trace_{i:04d}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        count += 1
    
    return count


def generate_anomaly_traces(output_dir: Path) -> List[Dict]:
    """生成异常trace"""
    anomalies = []
    
    for i in range(3):
        issue = "账号密码错误无法登录"
        records = generate_trace(100 + i, issue, has_anomaly=True)
        
        output_file = output_dir / f"trace_anomaly_{i:03d}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        anomalies.append({
            "trace_id": f"trace_anomaly_{i:03d}",
            "type": "high_latency" if i == 0 else ("error" if i == 1 else "excessive_tokens"),
            "file": str(output_file)
        })
    
    return anomalies


def generate_dataset(output_dir: str, num_traces: int = 100):
    """生成完整数据集"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    normal_count = generate_normal_traces(num_traces, output_path)
    anomalies = generate_anomaly_traces(output_path)
    
    total = normal_count + len(anomalies)
    
    info = {
        "total_traces": total,
        "normal_traces": normal_count,
        "anomaly_traces": len(anomalies),
        "generated_at": datetime.now().isoformat(),
        "description": "IT客服场景Agent Trace数据集",
        "scenarios": [issue[0] for issue in IT_ISSUES],
        "tools": TOOLS,
        "skills": SKILLS
    }
    
    with open(output_path / "_dataset_info.json", 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {total} traces in {output_dir}")
    print(f"  - Normal traces: {normal_count}")
    print(f"  - Anomaly traces: {len(anomalies)}")
    print(f"  - Scenarios: {len(IT_ISSUES)}")
    print(f"  - Tools: {len(TOOLS)}")
    print(f"  - Skills: {len(SKILLS)}")
    
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate IT support agent trace dataset")
    parser.add_argument("-o", "--output", default="data/it_support_traces", help="Output directory")
    parser.add_argument("-n", "--num", type=int, default=100, help="Number of normal traces")
    
    args = parser.parse_args()
    generate_dataset(args.output, args.num)
