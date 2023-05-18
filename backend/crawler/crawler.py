import json
from datetime import datetime

import cloudscraper
import psycopg2
from bs4 import BeautifulSoup, Tag
from selenium.webdriver import ChromeOptions
from undetected_chromedriver import Chrome

from backend.crawler.db import insert_comment, insert_user, insert_forum, insert_thread
from backend.crawler.models import CommentData, QuoteData


def get_db():
    connection = psycopg2.connect(
        database="voz_db",
        user="postgres",
        password="minhnd1234",
        host="localhost",
        port="5432",
    )
    return connection


def list_crawled_posts(db_connection) -> set:
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM comment")
    return {comment_data[0] for comment_data in cursor.fetchall()}


def list_crawled_pages(db_connection, thread_url) -> list:
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT crawled_page FROM thread WHERE url = %s",
        thread_url
    )
    return cursor.fetchone() or []


def get_driver() -> Chrome:
    options = ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    return Chrome(options=options)


def insert_thread_data(db_connection, page_html):
    thread_title = page_html.select_one("meta[property='og:title']")["content"]
    thread_url = page_html.select_one("meta[property='og:url']")["content"]
    forum_url = page_html.select_one("li~ li+ li a[itemprop]")["href"]
    forum_title = page_html.select_one("li~ li+ li span").getText()
    forum_id = insert_forum(db_connection, forum_title, forum_url)
    thread_id = insert_thread(db_connection, thread_title, thread_url, forum_id)
    return thread_id


def crawl_thread(db_connection, thread_url: str):
    crawled_pages = list_crawled_pages(db_connection)
    crawled_comments = list_crawled_posts(db_connection)
    max_pages = 1
    i = 0
    scraper = cloudscraper.create_scraper()
    thread_id = None
    while i < max_pages:
        if i == 0:
            url = thread_url
        else:
            url = f"{thread_url}page-{i + 1}"
        if i + 1 in crawled_pages and i != 0:
            i += 1
            continue
        page_content = scraper.get(url).text

        soup = BeautifulSoup(page_content, "html.parser")
        if max_pages == 1:
            max_pages = get_max_thread_pages(soup)
            thread_id = insert_thread_data(db_connection, soup)
        crawled_comments = insert_page_data(
            db_connection, extract_page_comments(soup), thread_id, crawled_comments
        )

        print("Crawling page: ", i + 1, "of", max_pages, "pages")
        i += 1


def insert_page_data(
    db_connection,
    extracted_comments: list[CommentData],
    thread_id: int,
    crawled_comments: set,
) -> set:
    """
    Insert comment, user, quote data into database
    """
    for comment in extracted_comments:
        if comment.id not in crawled_comments:
            insert_user(
                db_connection,
                comment.user_id,
                comment.user_name,
                comment.user_url,
            )
            insert_comment(
                db_connection,
                comment.id,
                comment.user_id,
                comment.idx,
                comment.post_time,
                comment.content,
                thread_id,
                comment.quotes,
                comment.json_content,
            )
            crawled_comments.add(comment.id)
    return crawled_comments


def extract_page_comments(page_html: BeautifulSoup) -> list[CommentData]:
    comments = page_html.select(
        "article.message.message--post.js-post.js-inlineModContainer"
    )
    return [extract_comment(comment) for comment in comments]


def extract_comment(comment_soup: Tag) -> CommentData:
    comment_headers = comment_soup.select(
        ".message-attribution-opposite.message-attribution-opposite--list li"
    )
    if comment_headers:
        idx = int(
            comment_headers[-1].getText().strip().replace("#", "").replace(",", "")
        )
    else:
        idx = None

    content_html = comment_soup.select_one("article div.bbWrapper")
    json_content = []
    for element in content_html.contents:
        element_type = element.name
        if element_type == "blockquote":
            pass
            # quote_content = element.select_one("div.js-expandContent")
            # if quote_content:
            #     element = quote_content
        elif element_type == "br":
            continue
        json_content.append({"type": element_type, "content": str(element)})
    result = CommentData(
        id=comment_soup["data-content"].replace("post-", ""),
        idx=idx,
        user_url=comment_soup.select_one("a.username")["href"],
        user_id=comment_soup.select_one("a.username")["data-user-id"],
        user_name=comment_soup.select_one("a.username").getText(),
        content=str(content_html),
        json_content=json.dumps(json_content),
    )
    post_time = (comment_soup.select("time")[0]["data-time"],)
    if post_time:
        result.post_time = datetime.fromtimestamp(int(post_time[0]))

    quotes = comment_soup.select("blockquote")
    result_quotes = []
    for quote in quotes:
        quote_parent_id = quote["data-source"].replace("post: ", "")
        result_quotes.append(
            QuoteData(parent_comment_id=quote_parent_id, content=str(quote))
        )
    result.quotes = result_quotes
    return result


def get_max_thread_pages(page_html: BeautifulSoup) -> int:
    page_navs = page_html.select(".pageNav-page a")
    if page_navs:
        last_page_element = page_navs[-1].getText()
        return int(last_page_element)
    return 1


def crawl_thread_links(db_connection, forum_url: str):
    """
    Crawl thread links from a forum page
    """
    scraper = cloudscraper.create_scraper()
    page_content = scraper.get(forum_url).text
    soup = BeautifulSoup(page_content, "html.parser")
    threads = soup.select(".structItem-title a[data-preview-url]")

    forum_id = insert_forum(db_connection, url=forum_url)
    for thread in threads:
        thread_title = thread.getText()
        thread_url = thread["href"]
        insert_thread(db_connection, thread_title, thread_url, forum_id)


if __name__ == "__main__":
    conn = get_db()
    crawl_thread(
        conn,
        "https://voz.vn/t/tac-dong-cua-ai-den-cong-viec-cua-lap-trinh-vien.771942/page-2#post-25249402",
    )
    # print(crawl_thread_links(conn, "https://voz.vn/f/chuyen-tro-linh-tinh.17/"))

    conn.close()
