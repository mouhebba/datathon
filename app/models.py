# app/models.py
from datetime import datetime
from typing import Optional, List
from .db import get_connection

def now_iso() -> str:
    return datetime.utcnow().isoformat()

def get_document_by_hash(authority: str, content_hash: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE authority=? AND content_hash=?",
        (authority, content_hash),
    )
    row = cur.fetchone()
    conn.close()
    return row

def insert_document(authority: str, title: str, url: str, file_path: str, content_hash: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents (
            authority, title, url, file_path, content_hash,
            created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?)
        """,
        (authority, title, url, file_path, content_hash, now_iso(), now_iso()),
    )
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id

def update_document_translation(doc_id: int, translated_text: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE documents
        SET translated_text=?, updated_at=?
        WHERE id=?
        """,
        (translated_text, now_iso(), doc_id),
    )
    conn.commit()
    conn.close()

def update_document_analysis(doc_id: int, summary: str, matched_keywords: List[str]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE documents
        SET analysis_summary=?, matched_keywords=?, updated_at=?
        WHERE id=?
        """,
        (summary, ",".join(matched_keywords), now_iso(), doc_id),
    )
    conn.commit()
    conn.close()

def mark_document_notified(doc_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE documents
        SET last_notified_at=?, updated_at=?
        WHERE id=?
        """,
        (now_iso(), now_iso(), doc_id),
    )
    conn.commit()
    conn.close()

def get_untranslated_documents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE translated_text IS NULL"
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_unanalysed_documents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE translated_text IS NOT NULL AND analysis_summary IS NULL"
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_unnotified_documents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE analysis_summary IS NOT NULL AND last_notified_at IS NULL"
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_recent_documents(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
