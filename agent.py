from langchain.agents import create_agent 
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
load_dotenv()
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search,scrap_url
 
# llm_model = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0  # Gemini 3.0+ defaults to 1.0
#     # max_tokens=None,
#     # timeout=None,
#     # max_retries=2
# )


llm_model = ChatMistralAI(
    model="ministral-3b-2512",
    temperature=0
    # max_tokens=None,
    # timeout=None,
    # max_retries=2
)


# 1st agent 

def build_search_agent ():
    return create_agent(
        model=llm_model,
        tools = [web_search]
    )

# 2nd tool

def build_reader_agent():
    return create_agent(
        model = llm_model,
        tools = [scrap_url]
    )

# write chain 
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm_model | StrOutputParser()

# CRITIC CHAIN


critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),])

critic_chain= critic_prompt | llm_model | StrOutputParser()