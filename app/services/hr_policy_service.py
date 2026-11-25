import logging
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from dataclasses import dataclass
from app.services.gemini_client import GeminiClient
from sqlalchemy.orm import Session
from app.models.hr_policy_version import HRPolicyVersion
from sqlalchemy import select
from sqlalchemy import func
from app.models.hr_policy import HRPolicy
from sqlalchemy.orm import joinedload
from datetime import date, datetime, timezone, timedelta
from app.models.hr_policy_chunk import HRPolicyChunk

logger = logging.getLogger(__name__)

def extract_policy_text(file_path: str | Path) -> str:
    """
    Extract text from a supported HR policy document.

    Supported formats:
        PDF
        DOCX
    """

    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Policy document was not found.")

    extension = path.suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(str(path))

        extracted_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            if page_text.strip():
                extracted_pages.append(
                    f"[Page {page_number}]\n{page_text.strip()}"
                )

        text = "\n\n".join(extracted_pages)

    elif extension == ".docx":
        document = Document(str(path))

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        text = "\n\n".join(paragraphs)

    else:
        raise ValueError(
            "Unsupported policy document format. "
            "Only PDF and DOCX are supported."
        )

    if not text.strip():
        raise ValueError(
            "No readable text was found in the policy document."
        )

    return text

def clean_policy_text(text: str) -> str:
    """
    Normalize extracted policy text while preserving
    paragraph and page boundaries.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Policy text cannot be empty.")

    cleaned_lines = []

    for line in text.splitlines():
        normalized_line = " ".join(line.split())

        if normalized_line:
            cleaned_lines.append(normalized_line)

    cleaned_text = "\n".join(cleaned_lines)

    if not cleaned_text.strip():
        raise ValueError("No readable policy text remains after cleaning.")

    return cleaned_text

@dataclass(frozen=True)
class PolicyTextChunk:
    chunk_number: int
    chunk_text: str


def chunk_policy_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[PolicyTextChunk]:
    """
    Split policy text into overlapping chunks.

    chunk_size:
        Maximum number of characters per chunk.

    overlap:
        Number of characters shared between consecutive chunks.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Policy text cannot be empty.")

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    chunks = []
    start = 0
    chunk_number = 1

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                PolicyTextChunk(
                    chunk_number=chunk_number,
                    chunk_text=chunk_text,
                )
            )
            chunk_number += 1

        if end >= len(text):
            break

        start = end - overlap

    return chunks

def generate_policy_chunk_embeddings(
    chunks: list[PolicyTextChunk],
    gemini_client: GeminiClient,
) -> list[dict]:
    """
    Generate Gemini embeddings for policy document chunks.

    Uses RETRIEVAL_DOCUMENT because these embeddings
    will be stored and searched as policy content.
    """

    if not chunks:
        raise ValueError("At least one policy chunk is required.")

    embedded_chunks = []

    for chunk in chunks:
        result = gemini_client.generate_embedding(
            text=chunk.chunk_text,
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensions=3072,
        )

        embedded_chunks.append(
            {
                "chunk_number": chunk.chunk_number,
                "chunk_text": chunk.chunk_text,
                "embedding": result.embedding,
                "embedding_model": result.model_name,
                "embedding_dimensions": result.dimensions,
            }
        )

    return embedded_chunks

def generate_policy_query_embedding(
    query: str,
    gemini_client: GeminiClient,
) -> list[float]:
    """
    Generate an embedding for an employee's policy question.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Policy search query cannot be empty.")

    result = gemini_client.generate_embedding(
        text=query.strip(),
        task_type="RETRIEVAL_QUERY",
        output_dimensions=3072,
    )

    return result.embedding

def save_policy_chunks(
    db: Session,
    policy_version_id: int,
    embedded_chunks: list[dict],
) -> int:
    """
    Save policy text chunks and their embeddings to PostgreSQL.
    """

    if not embedded_chunks:
        raise ValueError("No policy chunks were provided.")
    validate_policy_version(db, policy_version_id)
    saved_count = 0

    for item in embedded_chunks:
        chunk = HRPolicyChunk(
            policy_version_id=policy_version_id,
            chunk_number=item["chunk_number"],
            chunk_text=item["chunk_text"],
            embedding_model=item["embedding_model"],
            embedding_dimensions=item["embedding_dimensions"],
            embedding=item["embedding"],
        )

        db.add(chunk)
        saved_count += 1

    db.flush()

    logger.info(
        "Saved %s policy chunks for policy version %s.",
        saved_count,
        policy_version_id,
    )

    return saved_count

def get_policy_chunks_by_version(
    db: Session,
    policy_version_id: int,
) -> list[HRPolicyChunk]:
    """
    Retrieve all chunks belonging to a policy version.
    """

    statement = (
        select(HRPolicyChunk)
        .options(
            joinedload(HRPolicyChunk.policy_version)
            .joinedload(HRPolicyVersion.policy)
        )
        .where(
            HRPolicyChunk.policy_version_id == policy_version_id
        )
        .order_by(HRPolicyChunk.chunk_number.asc())
    )

    return list(db.scalars(statement).all())

def validate_policy_version(
    db: Session,
    policy_version_id: int,
) -> HRPolicyVersion:
    """
    Retrieve a policy version or raise an error if it does not exist.
    """

    policy_version = db.get(HRPolicyVersion, policy_version_id)

    if policy_version is None:
        raise ValueError(
            f"Policy version {policy_version_id} was not found."
        )

    return policy_version

def search_policy_chunks_by_embedding(
    db: Session,
    query_embedding: list[float],
    limit: int = 5,
) -> list[HRPolicyChunk]:
    """
    Retrieve the most semantically similar policy chunks.
    """

    if len(query_embedding) != 3072:
        raise ValueError(
            "Query embedding must contain exactly 3072 dimensions."
        )

    if limit < 1:
        raise ValueError("Search limit must be at least 1.")

    statement = (
        select(HRPolicyChunk)
        .join(
            HRPolicyVersion,
            HRPolicyChunk.policy_version_id
            == HRPolicyVersion.policy_version_id,
        )
        .join(
            HRPolicy,
            HRPolicyVersion.policy_id == HRPolicy.policy_id,
        )
        .where(
            HRPolicyVersion.status == "published",
            HRPolicy.status == "published",
            HRPolicyVersion.effective_from <= date.today(),
            (
                HRPolicyVersion.effective_to.is_(None)
                | (HRPolicyVersion.effective_to >= date.today())
            ),
        )
        .order_by(
            HRPolicyChunk.embedding.cosine_distance(query_embedding)
        )
        .limit(limit)
    )
    return list(db.scalars(statement).all())

def search_policy_chunks_by_text(
    db: Session,
    query: str,
    limit: int = 5,
) -> list[HRPolicyChunk]:
    """
    Retrieve published policy chunks using PostgreSQL full-text search.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Policy search query cannot be empty.")

    if limit < 1:
        raise ValueError("Search limit must be at least 1.")

    search_query = func.plainto_tsquery("english", query.strip())

    statement = (
        select(HRPolicyChunk)
        .join(
            HRPolicyVersion,
            HRPolicyChunk.policy_version_id
            == HRPolicyVersion.policy_version_id,
        )
        .join(
            HRPolicy,
            HRPolicyVersion.policy_id == HRPolicy.policy_id,
        )
        .where(
            HRPolicyVersion.status == "published",
            HRPolicy.status == "published",
            HRPolicyVersion.effective_from <= date.today(),
            (
                HRPolicyVersion.effective_to.is_(None)
                | (HRPolicyVersion.effective_to >= date.today())
            ),
            HRPolicyChunk.search_vector.op("@@")(search_query),
        )
        .order_by(
            func.ts_rank(
                HRPolicyChunk.search_vector,
                search_query,
            ).desc()
        )
        .limit(limit)
    )

    return list(db.scalars(statement).all())

def hybrid_search_policy_chunks(
    db: Session,
    query: str,
    query_embedding: list[float],
    limit: int = 5,
) -> list[HRPolicyChunk]:
    """
    Combine semantic and PostgreSQL full-text search
    using Reciprocal Rank Fusion (RRF).
    """

    if limit < 1:
        raise ValueError("Search limit must be at least 1.")

    semantic_results = search_policy_chunks_by_embedding(
        db=db,
        query_embedding=query_embedding,
        limit=limit,
    )

    text_results = search_policy_chunks_by_text(
        db=db,
        query=query,
        limit=limit,
    )

    rank_constant = 60

    fused_scores = {}
    chunk_lookup = {}

    for results in (semantic_results, text_results):
        for rank, chunk in enumerate(results, start=1):
            chunk_id = chunk.policy_chunk_id

            fused_scores[chunk_id] = (
                fused_scores.get(chunk_id, 0.0)
                + 1.0 / (rank_constant + rank)
            )

            chunk_lookup[chunk_id] = chunk

    ranked_chunk_ids = sorted(
        fused_scores,
        key=lambda chunk_id: fused_scores[chunk_id],
        reverse=True,
    )

    return [
        chunk_lookup[chunk_id]
        for chunk_id in ranked_chunk_ids[:limit]
    ]


def retrieve_relevant_policy_chunks(
    db: Session,
    query: str,
    gemini_client: GeminiClient,
    limit: int = 5,
) -> list[HRPolicyChunk]:
    """
    Generate a query embedding and retrieve relevant policy chunks.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Policy search query cannot be empty.")

    query_embedding = generate_policy_query_embedding(
        query=query,
        gemini_client=gemini_client,
    )

    return hybrid_search_policy_chunks(
        db=db,
        query=query,
        query_embedding=query_embedding,
        limit=limit,
    )

def format_policy_context(
    chunks: list[HRPolicyChunk],
) -> str:
    """
    Format retrieved policy chunks into context for the AI assistant.
    """

    if not chunks:
        return (
            "No relevant published HR policies were found. "
            "Do not invent HR policy rules or assume an answer."
        )

    context_parts = []

    for chunk in chunks:
        policy = chunk.policy_version.policy

        context_parts.append(
            f"[Policy: {policy.policy_title}]\n"
            f"[Policy Code: {policy.policy_code}]\n"
            f"[Policy Version: {chunk.policy_version_id}]\n"
            f"[Chunk: {chunk.chunk_number}]\n"
            f"[Source: {chunk.source_reference or 'Not specified'}]\n"
            f"{chunk.chunk_text}"
        )

    return "\n\n".join(context_parts)

def ingest_policy_document(
    db: Session,
    policy_version_id: int,
    file_path: str | Path,
    gemini_client: GeminiClient,
    source_reference: str | None = None,
) -> int:
    """
    Extract, process, embed, and save an HR policy document.
    """

    policy_version = validate_policy_version(
        db,
        policy_version_id,
    )

    if policy_version.status != "draft":
        raise ValueError(
            "Policy documents can only be ingested into draft versions."
        )

    if source_reference is not None and not source_reference.strip():
        raise ValueError(
            "Source reference cannot be empty when provided."
        )

    existing_chunks = get_policy_chunks_by_version(
        db,
        policy_version_id,
    )

    if existing_chunks:
        raise ValueError(
            "This policy version already contains chunks."
        )
    try:
        extracted_text = extract_policy_text(file_path)
        cleaned_text = clean_policy_text(extracted_text)
        chunks = chunk_policy_text(cleaned_text)

        embedded_chunks = generate_policy_chunk_embeddings(
            chunks=chunks,
            gemini_client=gemini_client,
        )

        policy_version.source_file_name = Path(file_path).name

        if source_reference is not None:
            policy_version.source_reference = source_reference.strip()

        return save_policy_chunks(
            db=db,
            policy_version_id=policy_version_id,
            embedded_chunks=embedded_chunks,
        )
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to ingest policy version %s.",
            policy_version_id,
        )
        raise
def create_policy_with_initial_version(
    db: Session,
    *,
    policy_code: str,
    policy_title: str,
    category: str,
    description: str | None,
    owner_user_id: int,
    created_by_user_id: int,
    version_label: str | None = None,
    change_summary: str | None = None,
) -> tuple[HRPolicy, HRPolicyVersion]:
    """
    Create an HR policy and its initial draft version.

    The caller is responsible for committing the transaction.
    """

    policy = HRPolicy(
        policy_code=policy_code.strip(),
        policy_title=policy_title.strip(),
        category=category.strip(),
        description=description,
        owner_user_id=owner_user_id,
        status="draft",
    )

    db.add(policy)
    db.flush()

    policy_version = HRPolicyVersion(
        policy_id=policy.policy_id,
        version_number=1,
        version_label=version_label,
        status="draft",
        created_by_user_id=created_by_user_id,
        change_summary=change_summary,
    )

    db.add(policy_version)
    db.flush()

    return policy, policy_version


def submit_policy_for_review(
    db: Session,
    policy_version_id: int,
) -> HRPolicyVersion:
    """
    Submit a draft HR policy version for review.

    The caller is responsible for committing the transaction.
    """

    policy_version = validate_policy_version(
        db,
        policy_version_id,
    )

    if policy_version.status != "draft":
        raise ValueError(
            "Only draft policy versions can be submitted for review."
        )

    existing_chunks = get_policy_chunks_by_version(
        db,
        policy_version_id,
    )

    if not existing_chunks:
        raise ValueError(
            "A policy document must be ingested before submission."
        )

    policy_version.status = "pending_review"
    policy_version.submitted_at = datetime.now(timezone.utc)

    db.flush()

    logger.info(
        "Policy version %s submitted for review.",
        policy_version_id,
    )

    return policy_version


def approve_policy_version(
    db: Session,
    policy_version_id: int,
    approved_by_user_id: int,
) -> HRPolicyVersion:
    """
    Approve a policy version submitted for review.

    The caller is responsible for committing the transaction.
    """

    policy_version = validate_policy_version(
        db,
        policy_version_id,
    )

    if policy_version.status != "pending_review":
        raise ValueError(
            "Only policy versions pending review can be approved."
        )

    if approved_by_user_id <= 0:
        raise ValueError("Invalid approving user ID.")

    policy_version.status = "approved"
    policy_version.approved_by_user_id = approved_by_user_id
    policy_version.approved_at = datetime.now(timezone.utc)

    db.flush()

    logger.info(
        "Policy version %s approved by user %s.",
        policy_version_id,
        approved_by_user_id,
    )

    return policy_version



def publish_policy_version(
    db: Session,
    policy_version_id: int,
    effective_from: date,
    effective_to: date | None = None,
) -> HRPolicyVersion:
    """
    Publish an approved HR policy version using chronological
    effective-date versioning.

    Previous published versions remain available for historical
    policy retrieval.

    The caller is responsible for committing the transaction.
    """

    policy_version = validate_policy_version(
        db,
        policy_version_id,
    )

    if policy_version.status != "approved":
        raise ValueError(
            "Only approved policy versions can be published."
        )

    if effective_from is None:
        raise ValueError(
            "An effective start date is required for publication."
        )

    if effective_to is not None and effective_to < effective_from:
        raise ValueError(
            "The effective end date cannot precede the start date."
        )

    policy = db.scalar(
        select(HRPolicy)
        .where(HRPolicy.policy_id == policy_version.policy_id)
        .with_for_update()
    )

    if policy is None:
        raise ValueError(
            "The associated HR policy was not found."
        )

    existing_published_versions = db.scalars(
        select(HRPolicyVersion)
        .where(
            HRPolicyVersion.policy_id == policy.policy_id,
            HRPolicyVersion.status == "published",
            HRPolicyVersion.policy_version_id != policy_version_id,
        )
        .order_by(HRPolicyVersion.effective_from.asc())
        .with_for_update()
    ).all()

    for existing_version in existing_published_versions:

        existing_start = existing_version.effective_from
        existing_end = existing_version.effective_to

        if existing_start is None:
            raise ValueError(
                "An existing published version has no effective start date."
            )

        # New versions must follow every previously published version.
        if effective_from <= existing_start:
            raise ValueError(
                "A new policy version must have an effective start "
                "date later than all previously published versions."
            )

        # Close a previous open-ended version.
        if existing_end is None:
            existing_version.effective_to = (
                effective_from - timedelta(days=1)
            )

        # Reject overlap with an existing finite period.
        elif existing_end >= effective_from:
            raise ValueError(
                "The new policy version overlaps an existing "
                "published version's effective period."
            )

    policy_version.effective_from = effective_from
    policy_version.effective_to = effective_to
    policy_version.status = "published"
    policy_version.published_at = datetime.now(timezone.utc)

    policy.status = "published"

    db.flush()

    logger.info(
        "Policy version %s published.",
        policy_version_id,
    )

    return policy_version
