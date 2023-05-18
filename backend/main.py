import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.crawler.crawler import crawl_thread
from backend.crawler.utils import normalize_url

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
connection = psycopg2.connect(
        database="voz_db",
        user="postgres",
        password="minhnd1234",
        host="localhost",
        port="5432",
    )


def get_repplies(comment_id: str, added_comments: set, db_connection) -> list:
    cursor = db_connection.cursor()

    cursor.execute("""
        SELECT 
            fk__reply__comment_child, c.content_json as content, fk__reply__comment_parent as parent, 
            vu.name as user_name, c.post_time
        FROM quote q
        JOIN comment c on q.fk__reply__comment_child = c.id
        JOIN voz_user vu on c.fk__comment__user = vu.id
        WHERE fk__reply__comment_parent = %s;
    """, (comment_id,))

    replies = []
    for comment_id, content, parent, user_name, post_time in cursor.fetchall():
        if comment_id in added_comments:
            return []
        added_comments.add(comment_id)
        replies.append({
            "id": comment_id,
            "content": content,
            "parent": parent,
            "user_name": user_name,
            "replies": get_repplies(comment_id, added_comments, db_connection),
            "post_time": post_time
        })
    return replies


def recently_updated(thread_url: str) -> bool:
    thread_url = normalize_url(thread_url)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id FROM thread
        WHERE
            last_crawl_time  > current_timestamp - interval '30 minutes' AND
            url = %s
        LIMIT 1
    """, (thread_url,))
    return bool(cursor.fetchone())


@app.get("/thread/")
def get(url: str):
    if not recently_updated(url):
        crawl_thread(connection, url)
    cursor = connection.cursor()

    normalized_url = normalize_url(url)
    cursor.execute("""
        SELECT title, last_crawl_time
        FROM thread WHERE url LIKE %s
    """, (normalized_url,))
    thread_data = cursor.fetchone()
    if thread_data:
        title, last_crawl_time = thread_data
    else:
        title, last_crawl_time = None, None

    cursor.execute("""
        SELECT comment.id, content_json as content, vu.name, comment.post_time
        FROM comment
        JOIN thread t ON comment.fk__comment_thread = t.id
        JOIN voz_user vu on comment.fk__comment__user = vu.id
        WHERE t.url LIKE %s
        ORDER BY index
    """, (normalized_url,))

    added_comments = set()
    posts = []
    for comment in cursor.fetchall():
        if comment[0] in added_comments:
            continue
        added_comments.add(comment[0])
        posts.append({
            "id": comment[0],
            "content": comment[1],
            "parent": None,
            "user_name": comment[2],
            "replies": get_repplies(comment[0], added_comments, connection),
            "post_time": comment[3]
        })
    return {
        "title": title,
        "last_crawl_time": last_crawl_time,
        "posts": posts
    }
