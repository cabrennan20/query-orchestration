#!/usr/bin/env python3
"""
Create a sample ElasticSearch index with test data for trying out the orchestrator.

Usage:
    python scripts/create_sample_index.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.config import get_settings
from orchestrator.core import ElasticsearchClient


SAMPLE_INDEX = "sample_products"

SAMPLE_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "title": {"type": "text"},
            "description": {"type": "text"},
            "category": {"type": "keyword"},
            "tags": {"type": "text"},
            "price": {"type": "float"},
            "popularity_score": {"type": "float"},
        }
    }
}

SAMPLE_PRODUCTS = [
    {
        "id": "1",
        "title": "Wireless Bluetooth Headphones",
        "description": "Premium over-ear headphones with active noise cancellation and 30-hour battery life",
        "category": "Electronics",
        "tags": "wireless bluetooth audio headphones noise-cancelling",
        "price": 199.99,
        "popularity_score": 9.2,
    },
    {
        "id": "2",
        "title": "Ergonomic Office Chair",
        "description": "Adjustable lumbar support office chair with breathable mesh back",
        "category": "Furniture",
        "tags": "office chair ergonomic furniture",
        "price": 349.99,
        "popularity_score": 8.5,
    },
    {
        "id": "3",
        "title": "Stainless Steel Water Bottle",
        "description": "Insulated 32oz water bottle keeps drinks cold for 24 hours",
        "category": "Kitchen",
        "tags": "water bottle insulated stainless steel",
        "price": 29.99,
        "popularity_score": 7.8,
    },
    {
        "id": "4",
        "title": "Mechanical Keyboard RGB",
        "description": "Gaming mechanical keyboard with customizable RGB lighting and Cherry MX switches",
        "category": "Electronics",
        "tags": "keyboard gaming mechanical rgb",
        "price": 129.99,
        "popularity_score": 8.9,
    },
    {
        "id": "5",
        "title": "Yoga Mat Premium",
        "description": "Non-slip yoga mat with extra cushioning, 6mm thick",
        "category": "Fitness",
        "tags": "yoga mat fitness exercise",
        "price": 39.99,
        "popularity_score": 8.1,
    },
    {
        "id": "6",
        "title": "LED Desk Lamp",
        "description": "Adjustable LED desk lamp with touch controls and USB charging port",
        "category": "Lighting",
        "tags": "lamp led desk lighting usb",
        "price": 45.99,
        "popularity_score": 7.5,
    },
    {
        "id": "7",
        "title": "Running Shoes",
        "description": "Lightweight running shoes with responsive cushioning for long distance",
        "category": "Footwear",
        "tags": "shoes running athletic footwear",
        "price": 119.99,
        "popularity_score": 8.7,
    },
    {
        "id": "8",
        "title": "Backpack Laptop",
        "description": "Waterproof laptop backpack with USB charging port, fits up to 17 inch",
        "category": "Bags",
        "tags": "backpack laptop bag waterproof",
        "price": 59.99,
        "popularity_score": 8.3,
    },
    {
        "id": "9",
        "title": "Coffee Maker Programmable",
        "description": "12-cup programmable coffee maker with thermal carafe",
        "category": "Kitchen",
        "tags": "coffee maker kitchen appliance",
        "price": 89.99,
        "popularity_score": 7.9,
    },
    {
        "id": "10",
        "title": "Wireless Mouse",
        "description": "Ergonomic wireless mouse with precision tracking and long battery life",
        "category": "Electronics",
        "tags": "mouse wireless computer ergonomic",
        "price": 34.99,
        "popularity_score": 8.0,
    },
]


async def create_sample_index():
    """Create sample index with test data."""
    print("=" * 60)
    print("Creating Sample Index")
    print("=" * 60)
    print()

    settings = get_settings()
    client = ElasticsearchClient(settings)

    try:
        es = await client.connect()
        print(f"Creating index: {SAMPLE_INDEX}")

        # Delete index if it exists
        if await es.indices.exists(index=SAMPLE_INDEX):
            print(f"  Index already exists, deleting...")
            await es.indices.delete(index=SAMPLE_INDEX)

        # Create index with mapping
        await es.indices.create(index=SAMPLE_INDEX, body=SAMPLE_MAPPING)
        print(f"  ✓ Index created")
        print()

        # Index sample documents
        print("Indexing sample products...")
        for product in SAMPLE_PRODUCTS:
            await es.index(index=SAMPLE_INDEX, id=product["id"], body=product)
            print(f"  ✓ Indexed: {product['title']}")

        # Refresh index
        await es.indices.refresh(index=SAMPLE_INDEX)
        print()

        # Verify
        count = await es.count(index=SAMPLE_INDEX)
        print(f"Total documents: {count['count']}")
        print()

        print("=" * 60)
        print("Sample index created successfully!")
        print("=" * 60)
        print()
        print("Try these queries:")
        print("  - 'headphones'")
        print("  - 'something to write with' (needs vector search)")
        print("  - 'office furniture'")
        print("  - 'fitness equipment'")
        print()
        print(f"Index name: {SAMPLE_INDEX}")
        print()

    except Exception as e:
        print(f"  ✗ Failed to create index: {e}")
        sys.exit(1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(create_sample_index())
