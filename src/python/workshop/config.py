import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for the AWS Cost Advisor Agent."""

    AGENT_NAME = "AWS Cost Advisor Agent"
    TENTS_DATA_SHEET_FILE = "datasheet/contoso-tents-datasheet.pdf"
    INSTANCE_DATA_SHEET_FILE = "datasheet/AzureResourceGraphResults-Query.txt"
    FONTS_ZIP = "fonts/fonts.zip"
    API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
    PROJECT_ENDPOINT = os.environ["PROJECT_ENDPOINT"]
    MAX_COMPLETION_TOKENS = 10240
    MAX_PROMPT_TOKENS = 20480
    # The LLM is used to generate the SQL queries.
    # Set the temperature and top_p low to get more deterministic results.
    TEMPERATURE = 0.1
    TOP_P = 0.1
