# Getting Started Guide

This guide will walk you through setting up and using the Query Orchestrator for the first time.

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.9 or higher** installed
2. **ElasticSearch 8.x cluster** running and accessible
3. **An index with data** to search against
4. (Optional) **Vector embeddings** in your index for semantic search

## Step 1: Installation

### Clone the Repository

```bash
git clone <repository-url>
cd query-orchestration
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

For development:

```bash
pip install -r requirements-dev.txt
```

## Step 2: Configure ElasticSearch Connection

### Create Environment File

```bash
cp .env.example .env
```

### Edit Configuration

Open `.env` and update with your ElasticSearch details:

```bash
# Your ElasticSearch cluster
ELASTICSEARCH_HOSTS=http://localhost:9200

# Your credentials
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your_password_here

# Index prefix for your search indices
ELASTICSEARCH_INDEX_PREFIX=products_
```

### Test Connection

Start Python and test the connection:

```python
from orchestrator.config import get_settings
from orchestrator.core import ElasticsearchClient
import asyncio

async def test_connection():
    settings = get_settings()
    client = ElasticsearchClient(settings)
    await client.connect()
    health = await client.health_check()
    print(f"ES Health: {health}")
    await client.disconnect()

asyncio.run(test_connection())
```

## Step 3: Prepare Your Index

### Required Fields

For **keyword search** to work, your index needs text fields:

```json
{
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "description": { "type": "text" },
      "tags": { "type": "text" }
    }
  }
}
```

For **vector search** to work, you need a dense_vector field:

```json
{
  "mappings": {
    "properties": {
      "embedding_vector": {
        "type": "dense_vector",
        "dims": 384,
        "similarity": "cosine"
      }
    }
  }
}
```

### Example: Create a Test Index

```bash
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "description": { "type": "text" },
      "price": { "type": "float" },
      "popularity_score": { "type": "float" }
    }
  }
}'
```

### Add Sample Data

```bash
curl -X POST "localhost:9200/products/_doc" -H 'Content-Type: application/json' -d'
{
  "title": "Wireless Bluetooth Headphones",
  "description": "Premium over-ear headphones with active noise cancellation",
  "price": 199.99,
  "popularity_score": 8.5
}'
```

## Step 4: Start the API Server

```bash
python main.py
```

You should see output like:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
Starting Query Orchestrator API...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Verify API is Running

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "elasticsearch_connected": true,
  "version": "0.1.0"
}
```

## Step 5: Test Your First Search

### Using the API

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "headphones",
    "algorithm_id": "keyword-only",
    "index": "products"
  }'
```

### Using the Web UI

1. Open a new terminal
2. Start a simple HTTP server:

```bash
python -m http.server 8080 --directory ui
```

3. Open your browser to: `http://localhost:8080`
4. Select an algorithm (e.g., "Keyword Search Only")
5. Enter a search query
6. Click "Search"

## Step 6: Create Your First Custom Algorithm

### Create Algorithm File

Create a new file: `configs/algorithms/my-first-algorithm.json`

```json
{
  "algorithm_id": "my-first-algorithm",
  "version": "1.0",
  "name": "My First Algorithm",
  "components": [
    {
      "type": "keyword_search",
      "config": {
        "fields": ["title^3", "description"],
        "operator": "or",
        "size": 10
      }
    }
  ],
  "metadata": {
    "created_by": "you@example.com",
    "status": "draft",
    "description": "My first custom search algorithm"
  }
}
```

### Test It

Refresh the UI and your new algorithm should appear in the list.

## Step 7: Compare Multiple Algorithms

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query": "headphones",
    "algorithm_ids": ["keyword-only", "my-first-algorithm"],
    "index": "products"
  }'
```

### Via UI

1. Select multiple algorithms (click on multiple cards)
2. Enter your query
3. Click "Search"
4. View results side-by-side

## Common Issues

### Issue: "ElasticSearch connection failed"

**Solution:**
- Verify ElasticSearch is running: `curl http://localhost:9200`
- Check credentials in `.env` file
- Ensure firewall allows connection

### Issue: "No algorithms found"

**Solution:**
- Check that `configs/algorithms/` directory exists
- Verify JSON files are valid
- Check file permissions

### Issue: "Index not found"

**Solution:**
- Verify index exists: `curl http://localhost:9200/_cat/indices`
- Update `ELASTICSEARCH_INDEX_PREFIX` in `.env`
- Specify index explicitly in search request

### Issue: "Vector search requires query_vector"

**Solution:**
- Vector search needs embeddings
- Either:
  - Provide `query_vector` in request
  - Use keyword-only algorithms
  - Integrate an embedding service

## Next Steps

1. **Read the Configuration Guide**: Learn about all available building blocks
   - [docs/CONFIGURATION.md](./CONFIGURATION.md)

2. **Try Hybrid Search**: Combine keyword and vector search
   - Use the `hybrid-rrf.json` example
   - Requires vector embeddings in your index

3. **Set Up Testing**: Implement historical query replay
   - Coming soon in future releases

4. **Deploy to Production**: Set up A/B testing
   - Coming soon in future releases

## Need Help?

- Check the main [README](../README.md)
- Review [CONFIGURATION.md](./CONFIGURATION.md)
- Contact the Search team

## Example Workflow

Here's a typical workflow for testing a new search improvement:

1. **Identify Problem**
   - Notice poor results for certain queries
   - E.g., "something to write with" returns no results

2. **Create Hypothesis**
   - Semantic search might help with conversational queries
   - Create hybrid algorithm combining keyword + vector

3. **Build Algorithm**
   - Copy `hybrid-rrf.json`
   - Adjust parameters (k, weights, etc.)
   - Save as new file

4. **Test with Sample Queries**
   - Use UI to compare new vs. old algorithm
   - Try various query types
   - Check that nothing breaks

5. **Run at Scale**
   - (Future) Run against historical queries
   - (Future) Calculate metrics (NDCG, etc.)
   - (Future) A/B test in production

6. **Iterate**
   - Adjust parameters based on results
   - Try different merge strategies
   - Add re-ranking if needed

7. **Deploy**
   - Mark algorithm as "production"
   - (Future) Roll out gradually
   - Monitor metrics
