from datetime import datetime

from backend.crawler.models import QuoteData
from backend.crawler.utils import normalize_url


def insert_comment(
    db_connection,
    comment_id: str,
    user_id: str = None,
    index: int = None,
    post_time: str = None,
    content: str = None,
    thread_id: int = None,
    quotes: list[QuoteData] = None,
    json_content: str = None,
):
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM comment WHERE id = %s LIMIT 1", (comment_id,))
    existed_comment = cursor.fetchone()
    if not existed_comment:
        cursor.execute(
            """
            INSERT INTO comment (id, fk__comment__user , index, post_time, content, fk__comment_thread, content_json) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (comment_id, user_id, index, post_time, content, thread_id, json_content),
        )

    if quotes:
        for quote in quotes:
            insert_quote(
                db_connection, comment_id, quote.parent_comment_id, quote.content
            )
    db_connection.commit()


def insert_quote(
    db_connection,
    child_comment_id: str,
    parent_comment_id: str,
    content: str,
):
    cursor = db_connection.cursor()
    cursor.execute(
        """
        SELECT id 
        FROM quote WHERE fk__reply__comment_child = %s AND fk__reply__comment_parent = %s AND content = %s LIMIT 1
        """,
        (child_comment_id, parent_comment_id, content),
    )
    existed_quote = cursor.fetchone()
    if not existed_quote:
        cursor.execute(
            """
            INSERT INTO quote (fk__reply__comment_child, fk__reply__comment_parent, content)
            VALUES (%s, %s, %s)
            """,
            (child_comment_id, parent_comment_id, content),
        )
        db_connection.commit()


def insert_user(db_connection, user_id: str, user_name: str, user_url: str):
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM voz_user WHERE id = %s LIMIT 1", (user_id,))
    existed_user = cursor.fetchone()
    if not existed_user:
        user_url = normalize_url(user_url)
        cursor.execute(
            "INSERT INTO voz_user (id, name, url) VALUES (%s, %s, %s)",
            (user_id, user_name, user_url),
        )
        db_connection.commit()


def insert_forum(db_connection, title="", url=""):
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM forum WHERE url = %s LIMIT 1", (url,))
    existed_forum = cursor.fetchone()
    if existed_forum:
        return existed_forum[0]
    else:
        url = normalize_url(url)
        cursor.execute(
            "INSERT INTO forum (title, url) VALUES (%s, %s)",
            (title, url),
        )
        db_connection.commit()
    cursor.execute("SELECT id FROM forum WHERE url = %s LIMIT 1", (url,))
    return cursor.fetchone()[0]


def insert_thread(db_connection, title="", url="", forum_id=None):
    url = normalize_url(url)

    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM thread WHERE url = %s LIMIT 1", (url,))
    existed_thread = cursor.fetchone()
    if existed_thread:
        thread_id = existed_thread[0]
        cursor.execute(
            "UPDATE thread SET title = %s, last_crawl_time = %s WHERE id = %s",
            (title, datetime.now(), thread_id),
        )
        db_connection.commit()
        return existed_thread[0]
    else:
        cursor.execute(
            "INSERT INTO thread (title, url, fk__thread_forum, last_crawl_time) VALUES (%s, %s, %s, %s)",
            (title, url, forum_id, datetime.now()),
        )
        db_connection.commit()
    cursor.execute("SELECT id FROM thread WHERE url = %s LIMIT 1", (url,))
    return cursor.fetchone()[0]
