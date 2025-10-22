# Configuration Guide

This document provides detailed configuration options for all building blocks.

## Algorithm Configuration Schema

```json
{
  "algorithm_id": "string",      // Unique identifier
  "version": "string",           // Version number
  "name": "string",              // Human-readable name
  "components": [],              // Array of block configurations
  "metadata": {}                 // Metadata object
}
```

## Block Types

### 1. Keyword Search Block

Performs traditional BM25 keyword search using ElasticSearch multi_match query.

```json
{
  "type": "keyword_search",
  "name": "optional_name",
  "enabled": true,
  "config": {
    "fields": [                   // Required: Fields to search
      "title^3",                  // With optional boost (^3 = 3x weight)
      "description",
      "tags^2"
    ],
    "operator": "or",             // Optional: "or" or "and" (default: "or")
    "minimum_should_match": "75%", // Optional: Min match threshold
    "fuzziness": "AUTO",          // Optional: Fuzzy matching
    "boost": 1.0,                 // Optional: Overall query boost
    "size": 10                    // Optional: Number of results
  }
}
```

**Parameters:**

- `fields` (required): Array of field names with optional boost syntax
  - Format: `"field_name"` or `"field_name^boost"`
  - Example: `"title^3"` means title field with 3x weight

- `operator` (optional): Boolean operator for terms
  - `"or"`: Any term can match (default)
  - `"and"`: All terms must match

- `minimum_should_match` (optional): Minimum number/percentage of terms that must match
  - Percentage: `"75%"`
  - Absolute: `"2"` (at least 2 terms)

- `fuzziness` (optional): Allow fuzzy matching
  - `"AUTO"`: Automatically determines fuzziness based on term length
  - `0`, `1`, `2`: Explicit edit distance

- `boost` (optional): Multiplier for all scores from this search (default: 1.0)

- `size` (optional): Maximum results to return (default: 10)

### 2. Vector Search Block

Performs semantic search using kNN on dense vector fields.

```json
{
  "type": "vector_search",
  "name": "optional_name",
  "enabled": true,
  "config": {
    "field": "embedding_vector",  // Required: Name of dense_vector field
    "k": 10,                      // Required: Number of nearest neighbors
    "num_candidates": 100,        // Required: Candidates for approximate kNN
    "similarity": "cosine",       // Optional: Similarity function
    "boost": 1.0                  // Optional: Overall query boost
  }
}
```

**Parameters:**

- `field` (required): Name of the dense_vector field in your ES index

- `k` (required): Number of nearest neighbors to return

- `num_candidates` (required): Number of candidates for approximate kNN
  - Higher = more accurate but slower
  - Typically 10-20x the value of `k`
  - Minimum: `k`

- `similarity` (optional): Similarity function to use
  - `"cosine"`: Cosine similarity (default for most embeddings)
  - `"dot_product"`: Dot product
  - `"l2_norm"`: Euclidean distance
  - Must match the similarity configured in your index mapping

- `boost` (optional): Multiplier for all scores (default: 1.0)

**Note:** Vector search requires `query_vector` to be provided in the search request.

### 3. Merge Block

Combines results from multiple search blocks.

```json
{
  "type": "merge",
  "name": "optional_name",
  "enabled": true,
  "config": {
    "strategy": "rrf",            // Required: Merge strategy
    "k": 60,                      // For RRF: Constant (default: 60)
    "weights": {                  // For weighted: Weights per source
      "0": 0.4,
      "1": 0.6
    },
    "max_results": 10             // Optional: Max results to return
  }
}
```

**Strategies:**

#### RRF (Reciprocal Rank Fusion)

Combines results using rank-based scoring. Works well when you don't know relative score magnitudes.

```
RRF_score = sum(1 / (k + rank)) for each occurrence
```

**Parameters:**
- `k` (default: 60): Constant to prevent division by zero and reduce impact of top ranks
  - Lower k = more weight on top results
  - Higher k = more uniform weighting

**Example:**
```json
{
  "strategy": "rrf",
  "k": 60,
  "max_results": 10
}
```

#### Weighted

Combines results using weighted score addition. Good when you want explicit control over source importance.

**Parameters:**
- `weights`: Object mapping source index to weight
  - Keys are string indices: "0", "1", "2", etc.
  - Values are weight multipliers
  - If not specified for a source, defaults to 1.0

**Example:**
```json
{
  "strategy": "weighted",
  "weights": {
    "0": 0.3,    // First search block: 30% weight
    "1": 0.7     // Second search block: 70% weight
  },
  "max_results": 10
}
```

#### Concatenate

Simple concatenation of results in order.

**Example:**
```json
{
  "strategy": "concatenate",
  "max_results": 20
}
```

#### Interleave

Round-robin interleaving of results from different sources.

**Example:**
```json
{
  "strategy": "interleave",
  "max_results": 10
}
```

### 4. Rerank Block

Re-orders results using additional signals.

```json
{
  "type": "rerank",
  "name": "optional_name",
  "enabled": true,
  "config": {
    "boost_by_field": "popularity_score",  // Field to use for boosting
    "weight": 0.3                          // Boost weight
  }
}
```

**Parameters:**

- `boost_by_field` (optional): Field name containing numeric boost value
  - Field must exist in document source
  - Must be numeric (int or float)
  - Larger values = higher boost

- `weight` (optional): How much to weight the field value (default: 1.0)
  - Formula: `new_score = original_score * (1 + weight * field_value)`

**Example:**
```json
{
  "boost_by_field": "popularity_score",
  "weight": 0.3
}
```

If a document has `popularity_score: 10` and `original_score: 1.0`:
```
new_score = 1.0 * (1 + 0.3 * 10) = 1.0 * 4.0 = 4.0
```

## Complete Examples

### Example 1: Simple Keyword Search

```json
{
  "algorithm_id": "keyword-basic",
  "version": "1.0",
  "name": "Basic Keyword Search",
  "components": [
    {
      "type": "keyword_search",
      "config": {
        "fields": ["title^2", "description"],
        "operator": "or",
        "size": 10
      }
    }
  ]
}
```

### Example 2: Hybrid Search with RRF

```json
{
  "algorithm_id": "hybrid-rrf",
  "version": "1.0",
  "name": "Hybrid Search (RRF)",
  "components": [
    {
      "type": "keyword_search",
      "config": {
        "fields": ["title^3", "description", "tags^2"],
        "operator": "or",
        "minimum_should_match": "75%",
        "size": 20
      }
    },
    {
      "type": "vector_search",
      "config": {
        "field": "embedding_vector",
        "k": 20,
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
  ]
}
```

### Example 3: Weighted Hybrid with Personalization

```json
{
  "algorithm_id": "hybrid-personalized",
  "version": "1.0",
  "name": "Personalized Hybrid Search",
  "components": [
    {
      "type": "keyword_search",
      "config": {
        "fields": ["title^3", "description"],
        "size": 20
      }
    },
    {
      "type": "vector_search",
      "config": {
        "field": "embedding_vector",
        "k": 20,
        "num_candidates": 150
      }
    },
    {
      "type": "merge",
      "config": {
        "strategy": "weighted",
        "weights": {
          "0": 0.3,
          "1": 0.7
        },
        "max_results": 20
      }
    },
    {
      "type": "rerank",
      "config": {
        "boost_by_field": "user_affinity_score",
        "weight": 0.5
      }
    }
  ]
}
```

## Algorithm Metadata

```json
{
  "metadata": {
    "created_by": "user@example.com",
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z",
    "status": "production",          // draft, testing, production
    "ab_test_id": "experiment-123",
    "description": "Algorithm description",
    "tags": ["hybrid", "personalized"]
  }
}
```

## Environment Configuration

Set these in your `.env` file:

```bash
# ElasticSearch
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=changeme
ELASTICSEARCH_INDEX_PREFIX=search_

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Algorithm Storage
ALGORITHM_CONFIG_PATH=./configs/algorithms
ALGORITHM_STORAGE_TYPE=filesystem

# Testing
TEST_QUERY_INDEX=test_queries
ENABLE_QUERY_LOGGING=true
```
