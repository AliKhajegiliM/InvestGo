from __future__ import annotations

from smartmoney.llm.extractors import LLMClient, LLMConfig, regex_extract_events


def test_regex_extractor_returns_structured_events():
    text = "The company announced a buyback program of 5% with the earnings call on April 12, 2024."
    events = regex_extract_events(text, doc_id="doc-1")
    assert any(evt["type"] == "buyback" for evt in events)
    buyback = next(evt for evt in events if evt["type"] == "buyback")
    assert buyback["magnitude"] == 5.0
    assert buyback["citation"].startswith("doc-1:")


def test_llm_client_uses_fallback_when_disabled(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    client = LLMClient(LLMConfig(enabled=False))
    events = client.extract_events("Guidance raised ahead of earnings on May 1, 2024", doc_id="doc-2")
    assert events
