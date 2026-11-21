
import logging
import time
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from app.config import settings
from app.observability import trace


log = logging.getLogger(__name__)


def _get_status_code(exc):
    """Support Pinecone SDK exception status attributes."""
    return (
        getattr(exc, "status_code", None)
        or getattr(exc, "status", None)
    )


@lru_cache(maxsize=1)
def index():
    """Return an initialized Pinecone index."""

    s = settings()

    if not s.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is missing from .env")

    if not s.pinecone_index_name:
        raise RuntimeError("PINECONE_INDEX_NAME is missing from .env")

    pc = Pinecone(api_key=s.pinecone_api_key)
    name = s.pinecone_index_name

    # Check whether the index already exists.
    try:
        info = pc.describe_index(name)

    except Exception as exc:
        # Create an index only when it genuinely does not exist.
        if _get_status_code(exc) != 404:
            raise

        log.info(
            "Creating Pinecone index %s (dimension=%d, metric=cosine)",
            name,
            s.embed_dim,
        )

        try:
            pc.create_index(
                name=name,
                dimension=s.embed_dim,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=s.pinecone_cloud,
                    region=s.pinecone_region,
                ),
            )

        except Exception as create_exc:
            # Another process may have created the index simultaneously.
            if _get_status_code(create_exc) != 409:
                raise

        info = pc.describe_index(name)

    # Validate embedding dimensions.
    if int(info.dimension) != s.embed_dim:
        raise ValueError(
            f"Pinecone index {name} has dimension={info.dimension}, "
            f"but expected {s.embed_dim}. "
            "Use a different index name or matching EMBED_DIM."
        )

    # Validate similarity metric.
    if str(info.metric).lower() != "cosine":
        raise ValueError(
            f"Pinecone index {name} must use cosine metric, "
            f"but got {info.metric}."
        )

    # Wait until Pinecone index is ready.
    deadline = time.monotonic() + s.pinecone_ready_timeout

    while True:
        status = pc.describe_index(name).status

        if status.get("ready"):
            break

        remaining = deadline - time.monotonic()

        if remaining <= 0:
            raise TimeoutError(
                f"Pinecone index {name} was not ready within "
                f"{s.pinecone_ready_timeout} seconds."
            )

        time.sleep(min(3, remaining))

    log.info("Pinecone index %s is ready", name)

    return pc.Index(name)


def namespace(tenant):
    """Return an isolated namespace for each tenant."""

    if tenant is None or not str(tenant).strip():
        raise ValueError("Tenant ID cannot be empty.")

    return "tenant-" + str(tenant)


@trace("upsert")
def upsert(tenant, records):
    """Insert or update vectors in a tenant-specific namespace."""

    if not records:
        raise ValueError("No vector records provided for upsert.")

    return index().upsert(
        vectors=records,
        namespace=namespace(tenant),
    )


@trace("search")
def search(tenant, vector, groups, owner, limit=5):
    """Search relevant vectors with tenant and access-control filters."""

    if not vector:
        raise ValueError("Query vector cannot be empty.")

    if limit < 1:
        raise ValueError("Search limit must be at least 1.")

    # Build access-control conditions.
    conditions = []

    if groups:
        conditions.append(
            {"allowed_groups": {"$in": list(groups)}}
        )

    if owner:
        conditions.append(
            {"owner_sub": {"$eq": owner}}
        )

    if not conditions:
        raise ValueError(
            "At least one authorized group or owner is required."
        )

    acl = conditions[0] if len(conditions) == 1 else {"$or": conditions}

    result = index().query(
        vector=vector,
        top_k=limit,
        include_metadata=True,
        namespace=namespace(tenant),
        filter=acl,
    )

    return [
        {
            "id": match.id,
            "score": match.score,
            "metadata": match.metadata or {},
        }
        for match in result.matches
    ]


def delete_document(tenant, ids):
    """Delete document vectors from a tenant namespace."""

    if ids:
        return index().delete(
            ids=ids,
            namespace=namespace(tenant),
        )
