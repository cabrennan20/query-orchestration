# Query Orchestrator

> Internal tool for Search team query orchestration, testing, and comparison

Query Orchestrator is a composable system for rapidly prototyping, testing, and deploying search algorithms on ElasticSearch. Inspired by Algolia's internal tooling, it enables teams to iterate quickly on search improvements without deploying code.

## Features

- **Composable Building Blocks**: Mix and match keyword search, vector search, merging strategies, and re-ranking
- **Config-Based Algorithms**: Define search algorithms as JSON configurations, not code
- **Parallel Execution**: Run multiple search methods simultaneously and merge results
- **Side-by-Side Comparison**: Test multiple algorithms against the same query
- **Safe Prototyping**: Test new algorithms without affecting production traffic
- **Non-Engineer Friendly**: Product managers and merchandisers can configure algorithms
- **Fast Iteration**: Seconds to try, minutes to verify, seconds to deploy

## Architecture

```
┌─────────────────┐
│   Web UI        │  ← Simple interface for testing
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI        │  ← REST API for algorithm execution
└────────┬────────┘
         │
┌────────▼────────┐
│  Algorithm      │  ← Orchestrates block execution
│  Executor       │
└────────┬────────┘
         │
┌────────▼────────────────────────┐
│  Composable Blocks              │
│  ┌──────────┐  ┌─────────┐     │
│  │ Keyword  │  │ Vector  │     │
│  │ Search   │  │ Search  │     │
│  └──────────┘  └─────────┘     │
│  ┌──────────┐  ┌─────────┐     │
│  │  Merge   │  │ Rerank  │     │
│  └──────────┘  └─────────┘     │
└────────┬────────────────────────┘
         │
┌────────▼────────┐
│ ElasticSearch   │  ← Your search cluster
└─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- ElasticSearch 8.x cluster
- Node.js (optional, for UI development)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd query-orchestration
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your ElasticSearch credentials
```

4. Start the API server:
```bash
python main.py
```

5. Open the UI:
```bash
# Open ui/index.html in your browser
# Or serve it with a simple HTTP server:
python -m http.server 8080 --directory ui
```

## Usage

### Testing Algorithms via UI

1. Open `http://localhost:8080` in your browser
2. Select one or more algorithms to compare
3. Enter a search query
4. View results side-by-side

### Testing Algorithms via API

```bash
# Execute a search with an algorithm
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "bluetooth headphones",
    "algorithm_id": "hybrid-rrf"
  }'

# Compare multiple algorithms
curl -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query": "bluetooth headphones",
    "algorithm_ids": ["keyword-only", "vector-only", "hybrid-rrf"]
  }'
```

### Creating Custom Algorithms

Create a new JSON file in `configs/algorithms/`:

```json
{
  "algorithm_id": "my-custom-algorithm",
  "version": "1.0",
  "name": "My Custom Algorithm",
  "components": [
    {
      "type": "keyword_search",
      "config": {
        "fields": ["title^3", "description"],
        "operator": "or"
      }
    },
    {
      "type": "vector_search",
      "config": {
        "field": "embedding_vector",
        "k": 10,
        "num_candidates": 100
      }
    },
    {
      "type": "merge",
      "config": {
        "strategy": "rrf",
        "k": 60,
        "max_results": 10
      }
    }
  ],
  "metadata": {
    "description": "Your algorithm description",
    "status": "draft"
  }
}
```

## Available Building Blocks

### Search Blocks

- **keyword_search**: Traditional BM25 keyword search
  - Supports field boosting, operators, fuzziness
  - Multi-match query under the hood

- **vector_search**: Semantic/vector search
  - kNN search on dense_vector fields
  - Configurable similarity functions

### Processing Blocks

- **merge**: Combine results from multiple searches
  - Strategies: RRF, weighted, concatenate, interleave
  - Deduplication and score normalization

- **rerank**: Re-order results using additional signals
  - Field-based boosting (popularity, recency)
  - Custom scoring functions

## Configuration Reference

See [docs/CONFIGURATION.md](./docs/CONFIGURATION.md) for complete configuration options.

## Development

### Project Structure

```
query-orchestration/
├── orchestrator/          # Main Python package
│   ├── blocks/           # Composable building blocks
│   ├── core/             # Orchestration engine
│   ├── config/           # Configuration schemas
│   └── api/              # FastAPI application
├── configs/              # Algorithm configurations
│   └── algorithms/       # Algorithm JSON files
├── ui/                   # Web interface
├── tests/                # Test suite
└── docs/                 # Documentation
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black orchestrator/
ruff orchestrator/
```

## Roadmap

- [ ] Historical query replay for testing
- [ ] Synthetic query generation with LLMs
- [ ] A/B testing framework
- [ ] Metrics calculation (NDCG, MRR, etc.)
- [ ] Query performance profiling
- [ ] Visual algorithm builder
- [ ] Integration with popular embedding providers

## Contributing

This is an internal tool. For questions or issues, contact the Search team.

## License

Internal use only.
