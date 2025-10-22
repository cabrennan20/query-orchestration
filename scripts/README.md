# Utility Scripts

This directory contains utility scripts for setup and testing.

## Available Scripts

### test_connection.py

Tests your ElasticSearch connection and displays cluster information.

```bash
python scripts/test_connection.py
```

**Output:**
- Connection status
- Cluster information
- Available indices
- Health check results

**Use this to:**
- Verify your `.env` configuration
- Confirm ElasticSearch is accessible
- See what indices are available

### create_sample_index.py

Creates a sample index with test product data.

```bash
python scripts/create_sample_index.py
```

**Creates:**
- Index: `sample_products`
- 10 sample product documents
- Proper field mappings for keyword search

**Use this to:**
- Get started quickly without real data
- Test the orchestrator functionality
- Learn how to structure your own data

## Example Workflow

1. **Test connection first:**
```bash
python scripts/test_connection.py
```

2. **Create sample index:**
```bash
python scripts/create_sample_index.py
```

3. **Start the API:**
```bash
python main.py
```

4. **Test via curl:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "headphones",
    "algorithm_id": "keyword-only",
    "index": "sample_products"
  }'
```

## Troubleshooting

If scripts fail:

1. Check `.env` file exists and is configured
2. Verify ElasticSearch is running
3. Ensure Python dependencies are installed
4. Check network connectivity
