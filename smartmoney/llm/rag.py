"""Rudimentary retrieval augmented generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..types import CatalystEvent
from .extractors import LLMClient, LLMConfig


@dataclass(slots=True)
class Document:
    doc_id: str
    text: str
    metadata: Dict[str, object]


class LocalRAG:
    """Tiny TF-IDF backed retriever used in tests."""

    def __init__(self, docs: Iterable[Document] | None = None, config: LLMConfig | None = None):
        self.docs: List[Document] = list(docs or [])
        self.vectorizer = TfidfVectorizer(stop_words="english") if self.docs else None
        self.document_matrix = None
        self.llm = LLMClient(config or LLMConfig(enabled=False))
        if self.docs:
            self._fit()

    def _fit(self) -> None:
        corpus = [doc.text for doc in self.docs]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.document_matrix = self.vectorizer.fit_transform(corpus)

    def add_documents(self, docs: Iterable[Document]) -> None:
        self.docs.extend(list(docs))
        self._fit()

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        if not self.docs or self.vectorizer is None or self.document_matrix is None:
            return []
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.document_matrix).ravel()
        order = sims.argsort()[::-1][:top_k]
        return [(self.docs[idx], float(sims[idx])) for idx in order if sims[idx] > 0]

    def extract_events(self, query: str, top_k: int = 5) -> List[CatalystEvent]:
        events: List[CatalystEvent] = []
        for doc, score in self.search(query, top_k=top_k):
            extracted = self.llm.extract_events(doc.text, doc.doc_id)
            for evt in extracted:
                evt.setdefault("citation", doc.doc_id)
                events.append(evt)
        return events


__all__ = ["LocalRAG", "Document"]
