"""Search client with optional Tavily and deterministic offline search."""

import json
from pathlib import Path

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Use Tavily when available and the bundled corpus as a local mock."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Search configured provider first, then fall back to offline corpus.
        """
        settings = get_settings()
        if settings.tavily_api_key:
            try:
                from tavily import TavilyClient

                response = TavilyClient(settings.tavily_api_key).search(
                    query, max_results=max_results
                )
                return [
                    SourceDocument(
                        title=item["title"],
                        url=item.get("url"),
                        snippet=item.get("content", ""),
                        metadata={"source_id": item.get("url", "tavily-source")},
                    )
                    for item in response.get("results", [])
                ]
            except Exception:
                pass

        terms = {word.lower() for word in query.split() if len(word) > 3}
        documents: list[SourceDocument] = []
        corpus_dir = Path("ai_agent_offline_research_corpus_v2/topics")
        for path in sorted(corpus_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            topic = data.get("topic", {})
            searchable = json.dumps(data, ensure_ascii=False).lower()
            score = sum(searchable.count(term) for term in terms)
            if score:
                source_id = data.get("benchmark_metadata", {}).get("topic_id", path.stem)
                snippet = topic.get("research_question") or topic.get(
                    "working_thesis_for_evaluation", ""
                )
                documents.append(
                    SourceDocument(
                        title=topic.get("name", path.stem),
                        snippet=snippet,
                        metadata={"source_id": source_id, "score": score, "offline": True},
                    )
                )
        documents.sort(key=lambda item: item.metadata.get("score", 0), reverse=True)
        return documents[:max_results] or [
            SourceDocument(
                title="Offline research corpus",
                snippet="No exact match was found; conclusions should be treated cautiously.",
                metadata={"source_id": "offline-fallback", "offline": True},
            )
        ]
