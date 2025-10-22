#!/usr/bin/env python3
"""
Test script to verify ElasticSearch connection and basic functionality.

Usage:
    python scripts/test_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.config import get_settings
from orchestrator.core import ElasticsearchClient


async def test_connection():
    """Test ElasticSearch connection."""
    print("=" * 60)
    print("Query Orchestrator - Connection Test")
    print("=" * 60)
    print()

    # Load settings
    print("Loading settings...")
    settings = get_settings()
    print(f"  Hosts: {settings.elasticsearch_hosts}")
    print(f"  Username: {settings.elasticsearch_username}")
    print()

    # Test connection
    print("Connecting to ElasticSearch...")
    client = ElasticsearchClient(settings)

    try:
        es = await client.connect()
        print("  ✓ Connected successfully!")
        print()

        # Get cluster info
        print("Cluster Information:")
        info = await es.info()
        print(f"  Name: {info['name']}")
        print(f"  Version: {info['version']['number']}")
        print(f"  Cluster: {info['cluster_name']}")
        print()

        # Check health
        print("Health Check:")
        is_healthy = await client.health_check()
        health = await es.cluster.health()
        print(f"  Status: {health['status']}")
        print(f"  Nodes: {health['number_of_nodes']}")
        print(f"  Healthy: {'✓' if is_healthy else '✗'}")
        print()

        # List indices
        print("Available Indices:")
        indices = await es.cat.indices(format="json")
        if indices:
            for idx in indices[:10]:  # Show first 10
                print(f"  - {idx['index']} ({idx['docs.count']} docs)")
        else:
            print("  No indices found")
        print()

        print("=" * 60)
        print("Connection test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Verify ElasticSearch is running")
        print("  2. Check .env file configuration")
        print("  3. Verify credentials")
        print("  4. Check firewall settings")
        sys.exit(1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_connection())
