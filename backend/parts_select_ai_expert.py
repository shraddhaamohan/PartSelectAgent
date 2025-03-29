from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
import asyncio
import httpx
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import Client
from typing import List
from crawler.PartInformation import PartInformation
from crawler.ModelInformation import ModelInformation
from crawler import ModelCompatibility
from knowledge_base.FaissIndexer import FaissIndexer
import json

load_dotenv()

llm = os.getenv('LLM_MODEL', 'deepseek-chat')
model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

## Load Knowledge Base
faiss_dishwasher = FaissIndexer(data_list=None)
faiss_refrigerator = FaissIndexer(data_list=None)

# Load the FAISS index and metadata
faiss_dishwasher.load_index("./knowledge_base/dishwasher_faiss_index.bin", "./knowledge_base/dishwasher_metadata.pkl")
faiss_refrigerator.load_index("./knowledge_base/refrigerator_faiss_index.bin", "./knowledge_base/refrigerator_metadata.pkl")

@dataclass
class PartsSelectAIDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
You are an intelligent assistant designed to assist customers with refrigerator and dishwasher parts on the PartSelect e-commerce platform. Your primary functions include:

Product Information – Providing details about specific parts, their compatibility, pricing, availability, and installation instructions.

Troubleshooting Support – Helping users diagnose and fix common appliance issues using the troubleshooting knowledge bank when applicable.

Order Assistance – Guiding users through the ordering process, checking availability, and linking to relevant product pages. The customer support number for parts select is 1-888-944-1394 which is available Monday to Saturday 8am-9pm EST. Do not answer questions outside this scope.

IMPORTANT TOOL USAGE INSTRUCTIONS:
- Call each tool ONLY ONCE per unique query or part number
- After retrieving information with a tool, use that information to craft your response without making duplicate calls
- When a user asks about the same part or issue multiple times, reference your previously retrieved information
- Only make a new tool call when presented with a genuinely new query or part number
- If the user is asking about a general trouble shooting question without specifying the model or part number, use the retrieve_relevant_troubleshooting_documentation tool to get the relevant information. 
- You will only pass to the retrieve_relevant_troubleshooting_documentation tool the appliance names - "Dishwasher" or "Refrigerator". Try to clean the user's query to get the more concise description of the issue.
- If the user is already asking about a specific model, you will call the get_model_information tool to get the relevant information and answer the question.
- Always suggest to the user if complications exist to call customer support at 1-888-944-1394 for further assistance.
- NEVER ASK USER TO CALL ANYONE ELSE OTHER THAN CUSTOMER SUPPORT. DO NOT fabricate information or provide guesses.
- NEVER MODIFY THE LINKS YOU GET FROM THE TOOLS. DO NOT ADD ANYTHING TO THEM. DO NOT CHANGE THE URLS.


Behavioral Guidelines:
Stay strictly within the domain of appliance parts and repairs and if you do not get any relevant context please direct users to call customer support - 1-888-944-1394 which is available Monday to Saturday 8am-9pm EST. Do not answer questions outside this scope.

Example Queries You Handle:
"How can I install part number PS11752778?"

"Is this part compatible with my WDT780SAEM1 model?"

"The ice maker on my Whirlpool fridge is not working. How can I fix it?"

"What is the price and availability of this part?"

Always prioritize efficiency, accuracy, and user experience while keeping responses focused and relevant to PartSelect's catalog.
"""

parts_select_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PartsSelectAIDeps,
    retries=2
)


@parts_select_expert.tool
async def retrieve_relevant_troubleshooting_documentation(ctx: RunContext[PartsSelectAIDeps], appliance: str, user_query: str) -> str:
    """
    Retrieve relevant troubleshooting documentation chunks based on the query with RAG.
    
    Args:
        ctx: The context including the Supabase client and OpenAI client
        appliance: The appliance type either "Dishwasher" or "Refrigerator"
        user_query: The user's troubleshooting related question or query 
        
    Returns:
        A formatted string containing the top 5 most relevant troubleshooting documentation chunks
    """
    try:
    
        print(user_query,"MOSHI", appliance, "HIII")
        # Query Supabase for relevant documents
        results = None
        if appliance.lower() == "dishwasher":
            results = faiss_dishwasher.search(user_query, k=3)
        elif appliance.lower() == "refrigerator":
            results = faiss_refrigerator.search(user_query, k=3)
        if not results:
            return "No relevant documentation found."
        
        # Format the results
        chunks = []
        for result in results:
 
            if result['score'] > 0.3:  # Adjust threshold as needed
                original_video_link = result['data']['data'].get('video_link', '')
                # Replace the video link with the YouTube link if it exists
                if "youtube.com" in original_video_link:
                    # Extract the video ID from the original link
                    video_id = original_video_link.split('/')[-2]
                    print("Video ID:", video_id)
                    new_video_link = f"https://www.youtube.com/watch?v={video_id}"
                    result['data']['data']['video_link'] = new_video_link
                chunks.append(result["data"])
            
        # Join all chunks with a separator
        return "\n\n---\n\n".join(json.dumps(chunks))
        
    except Exception as e:
        print(f"Error retrieving documentation: {e}")
        return f"Error retrieving documentation: {str(e)}"

# @parts_select_expert.tool
# async def list_documentation_pages(ctx: RunContext[PartsSelectAIDeps]) -> List[str]:
#     """
#     Retrieve a list of all available Pydantic AI documentation pages.
    
#     Returns:
#         List[str]: List of unique URLs for all documentation pages
#     """
#     try:
#         # Query Supabase for unique URLs where source is pydantic_ai_docs
#         result = ctx.deps.supabase.from_('site_pages') \
#             .select('url') \
#             .eq('metadata->>source', 'pydantic_ai_docs') \
#             .execute()
        
#         if not result.data:
#             return []
            
#         # Extract unique URLs
#         urls = sorted(set(doc['url'] for doc in result.data))
#         return urls
        
#     except Exception as e:
#         print(f"Error retrieving documentation pages: {e}")
#         return []

# @parts_select_expert.tool
# async def get_page_content(ctx: RunContext[PartsSelectAIDeps], url: str) -> str:
#     """
#     Retrieve the full content of a specific documentation page by combining all its chunks.
    
#     Args:
#         ctx: The context including the Supabase client
#         url: The URL of the page to retrieve
        
#     Returns:
#         str: The complete page content with all chunks combined in order
#     """
#     try:
#         # Query Supabase for all chunks of this URL, ordered by chunk_number
#         result = ctx.deps.supabase.from_('site_pages') \
#             .select('title, content, chunk_number') \
#             .eq('url', url) \
#             .eq('metadata->>source', 'pydantic_ai_docs') \
#             .order('chunk_number') \
#             .execute()
        
#         if not result.data:
#             return f"No content found for URL: {url}"
            
#         # Format the page with its title and all chunks
#         page_title = result.data[0]['title'].split(' - ')[0]  # Get the main title
#         formatted_content = [f"# {page_title}\n"]
        
#         # Add each chunk's content
#         for chunk in result.data:
#             formatted_content.append(chunk['content'])
            
#         # Join everything together
#         return "\n\n".join(formatted_content)
        
#     except Exception as e:
#         print(f"Error retrieving page content: {e}")
#         return f"Error retrieving page content: {str(e)}"
    
@parts_select_expert.tool
async def get_part_installation_information(ctx: RunContext[PartsSelectAIDeps], part_number: str) -> str:
    """
    Retrieves all information of a part with including its identifiers (part_number, mfg_number), URLs (part_url, image_url, installation_video), description (product_description, symptoms_it_fixes, appliances_its_for, compatible_brands), installation details (installation_difficulty, installation_time), pricing and availability (price, availability), and customer feedback (review_count, rating).
    Args:
        ctx: The context including the Supabase client
        part_number: The part number to retrieve information for
        
    Returns:
        str: The complete information of the part related to its installation
    """
    try:
        print("Fetching part information...")
        url = f"https://www.partselect.com/api/search/?searchterm={part_number}&SearchMethod=standard"
        
        # Create the PartInformation instance
        part_info = PartInformation(url).getPartInfoModel()

        return part_info.model_dump_json(indent=2)  # Convert to JSON string
                
    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"
    
@parts_select_expert.tool
async def get_model_information(ctx: RunContext[PartsSelectAIDeps], model_number: str) -> str:
    """
    Retrieves detailed information about a model, including its name, URL, manuals, diagrams, videos, and parts URL.
    
    Args:
        ctx: The context including the Supabase client
        model_number: The model number to retrieve information for
        
    Returns:
        str: The complete information of the model in JSON format
    """
    try:
        print(f"Fetching information for model: {model_number}...")
        # Construct the model URL
        model_url = f"https://www.partselect.com/Models/{model_number}/"
        
        # Create the ModelInformation instance
        model_info_instance = ModelInformation(model_url)
        
        # Fetch the model information
        model_info_model = model_info_instance.getmodelInfoModel()
        
        # Return the model information as a JSON string
        return model_info_model.model_dump_json(indent=2)
    
    except Exception as e:
        print(f"Error retrieving model information: {e}")
        return f"Error retrieving model information: {str(e)}"
    
@parts_select_expert.tool
async def get_model_compatibility_information(ctx: RunContext[PartsSelectAIDeps], part_number: str, model_number: str) -> str:
    """
    Retrieves all information of a part with including its identifiers (part_number, mfg_number), URLs (part_url, image_url, installation_video), description (product_description, symptoms_it_fixes, appliances_its_for, compatible_brands), installation details (installation_difficulty, installation_time), pricing and availability (price, availability), and customer feedback (review_count, rating).
    Args:
        ctx: The context including the Supabase client
        part_number: The part number to retrieve information for
        
    Returns:
        str: The complete information of the part related to its installation
    """
    try:
        print("Checking part compatibility with model...")
        modelCompatibility = ModelCompatibility.checkModalCompatibility(model_number, part_number)
        print(modelCompatibility)
        return modelCompatibility.model_dump_json(indent=2)  # Convert to JSON string
                
    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"