from typing import Any, Dict, List, Optional, Awaitable, Callable, Tuple, Type, Union


from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.utilities import BingSearchAPIWrapper
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain.schema import OutputParserException
from langchain.prompts import PromptTemplate

from prompts import BING_PROMPT_PREFIX

def run_agent(question:str, agent_chain: AgentExecutor) -> str:
    """Function to run the brain agent and deal with potential parsing errors"""
    
    try:
        return agent_chain.run(input=question)
    
    except OutputParserException as e:
        # If the agent has a parsing error, we use OpenAI model again to reformat the error and give a good answer
        chatgpt_chain = LLMChain(
                llm=agent_chain.agent.llm_chain.llm, 
                    prompt=PromptTemplate(input_variables=["error"],template='Remove any json formating from the below text, also remove any portion that says someting similar this "Could not parse LLM output: ". Reformat your response in beautiful Markdown. Just give me the reformated text, nothing else.\n Text: {error}'), 
                verbose=False
            )

        response = chatgpt_chain.run(str(e))
        return response


class BingSearchResults(BaseTool):
    """Tool for a Bing Search Wrapper"""

    name = "@bing"
    description = "useful when the questions includes the term: @bing.\n"

    k: int = 5

    def _run(self, query: str) -> str:
        bing = BingSearchAPIWrapper(k=self.k)
        try:
            return bing.results(query,num_results=self.k)
        except:
            return "No Results Found"
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BingSearchResults does not support async")
            
            
class BingSearchTool(BaseTool):
    """Tool for a Bing Search Wrapper"""
    
    name = "@bing"
    description = "useful when the questions includes the term: @bing.\n"
    
    llm: AzureChatOpenAI
    k: int = 5
    
    def _run(self, tool_input: Union[str, Dict],) -> str:
        try:
            tools = [BingSearchResults(k=self.k)]
            parsed_input = self._parse_input(tool_input)

            agent_executor = initialize_agent(tools=tools, 
                                              llm=self.llm, 
                                              agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
                                              agent_kwargs={'prefix':BING_PROMPT_PREFIX},
                                              callback_manager=self.callbacks,
                                              verbose=self.verbose)
            
            for i in range(2):
                try:
                    response = run_agent(parsed_input, agent_executor)
                    break
                except Exception as e:
                    response = str(e)
                    continue

            return response
        
        except Exception as e:
            print(e)
    
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BingSearchTool does not support async")