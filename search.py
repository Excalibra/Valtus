import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from config import USER_AGENTS

def get_requests_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

SESSION = get_requests_session()

def scrape_page(url, proxies=None):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = SESSION.get(url, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
            meta = soup.find("meta", attrs={"name": "description"})
            desc = meta.get("content", "").strip() if meta else ""
            return title, desc
    except Exception as e:
        raise e
    return "No Title", ""

def perform_google_dork_search_live(dork, num_results=3, pause=30, proxies=None):
    from googlesearch import search

    param_sets = [
        {'num_results': num_results, 'sleep_interval': pause},
        {'num_results': num_results, 'pause': pause},
        {'stop': num_results, 'pause': pause},
        {'num_results': num_results},
    ]

    for params in param_sets:
        try:
            for url in search(dork, **params):
                title, desc = scrape_page(url, proxies)
                yield {"url": url, "title": title, "description": desc}
            return
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                continue
            else:
                raise e
        except Exception as e:
            raise e
    raise Exception("No compatible parameter set found for googlesearch.search()")
