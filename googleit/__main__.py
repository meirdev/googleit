import dataclasses
import os
import re
import sys
import textwrap
from urllib.parse import urlencode, urlparse, urlunsplit

from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from playwright.sync_api import sync_playwright

DOMAIN = os.environ.get("GOOGLEIT_DOMAIN", "google.com")


@dataclasses.dataclass
class Result:
    title: str
    link: str
    content: str


def get_query() -> str:
    return " ".join(sys.argv[1:])


def get_search_url(query: str) -> str:
    return urlunsplit(("https", DOMAIN, "/search", urlencode({"q": query}), ""))


def get_page_source(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()

        page = browser.new_page()
        page.goto(url)

        content = page.content()

        browser.close()

        return content


def parse_results(content: str) -> list[Result]:
    soup = BeautifulSoup(content, "html.parser")

    results = []

    for div1 in soup.find_all("div", class_="MjjYud"):
        item = None

        if div2 := div1.find("div", class_="yuRUbf"):
            if link := div2.find("a"):
                if title := link.find("h3", class_="LC20lb MBeuO DKV0Md"):
                    item = Result(title.text, link.attrs["href"], "")

        if item:
            if text := div1.find(
                "div", class_="VwiC3b yXK7lf MUxGbd yDYNvb lyLwlc lEBKkf"
            ):
                item.content = text.text

                results.append(item)

    return results


def get_host(url: str) -> str:
    return urlparse(url).netloc


def get_content(content: str, query: str) -> str:
    keywords = re.sub(r"[^\w\s]+", "", query).split()

    content = "\n".join(textwrap.wrap(content))

    for keyword in keywords:
        content = re.sub(
            rf"({keyword})",
            Style.BRIGHT + "\\1" + Style.NORMAL,
            content,
            flags=re.IGNORECASE,
        )

    return content


def get_link(href: str, title: str) -> str:
    # https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    return "\x1b]8;;" + href + "\x1b\\" + title + "\x1b]8;;\x1b\\"


def main() -> None:
    init()

    query = get_query()
    if not query:
        print(Fore.RED, "Missing query")
        sys.exit(1)

    url = get_search_url(query)
    content = get_page_source(url)
    results = parse_results(content)

    for result in results:
        print(Fore.BLACK + get_host(result.link), Style.RESET_ALL)
        print(Fore.BLUE + get_link(result.link, result.title), Style.RESET_ALL)
        print(Fore.WHITE + get_content(result.content, query), Style.RESET_ALL)
        print()


if __name__ == "__main__":
    main()
