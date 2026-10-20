from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient 
import os
from dotenv import load_dotenv
load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search (query:str)->str:
    """search the web for recent and reliable information  on a topic .return titles ,url and snippets."""
    results= tavily.search(query=query, max_results=5)
    
    # return result
    out =[]
    for r in results ['results']:
        out.append (
            f"Title:{r['title']}\n URL:{r['url']}\n Snippet:{r['content'][:300]}\n"
        )
    return "\n______\n ".join(out)
    
# print (web_search.invoke("what are the rexcent news"))

@tool 
def scrap_url(url:str )->str:
    """scrap and return clean text content from a given URL for depper reading  """
    try:
        resp=requests.get(url,timeout =8,headers={"user-agent":"Mozila/0.5"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(['script','style','nav','footer']):
            tag.decompose()
        return soup.get_text(separator="",strip=True)[:3000]
    except Exception as e:
        return f"could not scrape url:{str(e)}"
# print (scrap_url.invoke("https://www.cbsnews.com/news/iphone-duo-pre-order-sales-apple-foldable/"))


    