#!/usr/bin/env python3
"""LLM engine for trace-optimize-skill
Supports OpenRouter and GLM-style providers.
Configuration is read from scripts/llm_config.yaml in the project.
"""
import json
import os
from typing import List, Dict, Optional
import requests

try:
    import yaml
except Exception:
    yaml = None  # YAML support is optional; code will raise informative error if used without PyYAML


class LLMClient:
    def __init__(self, config: Dict):
        self.provider = config.get("provider", "openrouter")
        self.api_key = config.get("api_key") or os.environ.get("LLM_API_KEY")
        self.base_url = config.get("base_url") or config.get("openrouter_base_url") or "https://openrouter.ai/api/v1/chat/completions"
        selfglm_base = config.get("glm_base_url") or config.get("glm_base")
        self.glm_base_url = selfglm_base
        self.openrouter_model = config.get("openrouter_model", "claude-3")
        self.glm_model = config.get("glm_model", "glm-130b")
        self.strategies = config.get("strategies", [])
        self.enabled = bool(config.get("enabled", True))
        # Normalize base urls if provided in config
        if self.base_url and not self.base_url.startswith("http"):
            self.base_url = "https://" + self.base_url

    def _call_openrouter(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        endpoint = self.base_url
        payload = {"model": model or self.openrouter_model, "messages": [{"role": "user", "content": prompt}]}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # OpenRouter response shapes may vary
            choices = data.get("choices", []) or []
            if choices and isinstance(choices, list):
                msg = choices[0].get("message", {})
                return msg.get("content", "")
        except Exception:
            return None
        return None

    def _call_glm(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        endpoint = self.glm_base_url or "https://glm.openmodel.ai/api/v1/generate"
        payload = {"model": model or self.glm_model, "prompt": prompt}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # Support multiple possible shapes
            if isinstance(data, dict):
                if "text" in data:
                    return data["text"]
                if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                    c = data["choices"][0]
                    if isinstance(c, dict):
                        return c.get("text") or c.get("content") or c.get("message", {}).get("content", "")
        except Exception:
            return None
        return None

    def generate_insights(self, anomalies: List[Dict], context: str) -> str:
        if not self.enabled:
            return "LLM disabled by configuration."
        # Build a structured prompt including enabled strategies
        enabled = [s for s in self.strategies if s.get("enabled", True)]
        strategy_names = [s.get("name", "strategy") for s in enabled]
        prompt_parts = []
        prompt_parts.append("你是一名资深 IT 服务与软件开发顾问。基于以下异常分析与上下文，输出深度分析、根因假设、可落地的改进策略。已启用策略：{}。".format(", ".join(strategy_names) if strategy_names else "无"))
        prompt_parts.append("上下文：\n" + context)
        prompt_parts.append("异常点：\n" + json.dumps(anomalies, ensure_ascii=False))
        if strategy_names:
            prompt_parts.append("策略清单：" + ", ".join(strategy_names))
        prompt = "\n\n".join(prompt_parts)
        # Try provider-specific calls
        if self.provider.lower() == "openrouter":
            content = self._call_openrouter(prompt, model=self.openrouter_model)
            if content:
                return content
        # GLM path
        content = None
        if self.glm_base_url or self.glm_model:
            content = self._call_glm(prompt, model=self.glm_model)
        if content:
            return content
        return "LLM 调用失败，回退到规则性分析。"
