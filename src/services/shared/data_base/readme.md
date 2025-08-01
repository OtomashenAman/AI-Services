
# 🔧 Qdrant Payload Index Creation Script

This script resolves common errors related to missing payload indexes in your Qdrant vector database—specifically for filtering by fields such as `user_type`.

---

## ❗ Problem

If you're encountering an error like the following when querying Qdrant:

```bash
qdrant_client.http.exceptions.UnexpectedResponse: Unexpected Response: 400 (Bad Request)
Raw response content:
b'{"status":{"error":"Bad request: Index required but not found for \"user_type\" of one of the following types: [keyword]. Help: Create an index for this key or use a different filter."}
```

It means your collection is missing a **payload index** for the `user_type` field. This index is necessary for filtering queries using this field.

---

## ✅ Solution

Run the following Python script to **create the required payload index** on the `user_type` field.

### 📜 Script: `create_qdrant_index.py`

```python
from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Qdrant configuration
qdrant_url = "https://68ed54cc-e0e7-4320-82e3-5aed41fb5f13.us-west-1-0.aws.cloud.qdrant.io"
qdrant_api_key = os.getenv("QDRANT_API_KEY")

# Initialize client
client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key
)

# Create payload index for 'user_type'
client.create_payload_index(
    collection_name="Question_vector_collection",
    field_name="user_type",
    field_schema=PayloadSchemaType.KEYWORD
)

print("✅ Payload index on 'user_type' created successfully!")
```

---

## 📦 Requirements

- Python 3.8+
- Install dependencies:

```bash
pip install qdrant-client python-dotenv
```

---

## ⚙️ Environment Configuration

Create a `.env` file in your project root with the following content:

```env
QDRANT_API_KEY=your_qdrant_api_key_here
```

---

## 🏗️ Collection Creation (if not exists)

Make sure the collection exists **before** creating the payload index. If not, you can create it with:

```python
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

client.create_collection(
    collection_name="Question_vector_collection",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)
```

Adjust the `size` parameter to match your embedding model dimensions.

---

## 🛡️ Idempotency

This script is **idempotent** — if you run it again and the index already exists, Qdrant will raise an error. You can optionally handle that with a try-except block to ignore existing index errors.
