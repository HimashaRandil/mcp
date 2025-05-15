import json
import time
import boto3
from botocore.config import Config
from typing import Dict, Any, Optional
from src.utils.logger.logging import logger as logging


class DirectClaudeClient:
    """
    Direct client for Claude 3.7 Sonnet that bypasses LangChain.
    This class is designed to work with extended thinking mode.
    Uses AWS CLI credentials and a YAML configuration file.
    """

    def __init__(
        self,
        config,
        agent_name: str = "DirectClaudeAgent",
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize the Direct Claude Client using a configuration file.

        Args:
            config: Configuration object with AWS and Claude settings
            agent_name: Name of the agent for tracking purposes
            system_prompt: Optional system prompt to override configuration
        """
        # Load configuration from YAML file
        self.config = config
        self.agent_name = agent_name

        aws_config = getattr(self.config, "aws_config", {})
        claude_config = getattr(self.config, "claude_config", {})

        # Claude settings with defaults
        self.model_id = getattr(
            claude_config, "model_id", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        )
        self.max_tokens = getattr(claude_config, "max_tokens", 2000)
        self.temperature = getattr(claude_config, "temperature", 0.7)
        self.region = getattr(claude_config, "region", "us-east-1")
        self.thinking_budget_tokens = getattr(
            claude_config, "thinking_budget_tokens", 8000
        )

        # System prompt can be passed directly rather than loaded from config
        self.system_prompt = system_prompt

        # AWS settings with defaults
        self.max_retries = getattr(aws_config, "max_retries", 3)
        self.backoff_factor = getattr(aws_config, "backoff_factor", 1.5)
        self.profile_name = getattr(aws_config, "profile_name", None)
        connect_timeout = getattr(aws_config, "connect_timeout", 120)
        read_timeout = getattr(aws_config, "read_timeout", 1800)

        # Create Bedrock client using AWS CLI credentials
        aws_config_obj = Config(
            region_name=self.region,
            connect_timeout=connect_timeout,  # 2 minutes
            read_timeout=read_timeout,  # 30 minutes
            max_pool_connections=50,
        )

        # Use AWS CLI profile if specified, otherwise use default credentials
        session_kwargs = {}
        if self.profile_name:
            session_kwargs["profile_name"] = self.profile_name

        # Create session and client
        session = boto3.Session(**session_kwargs)
        self.bedrock_runtime = session.client(
            "bedrock-runtime",
            config=aws_config_obj,
        )

        logging.info(
            f"Initialized {self.__class__.__name__} with model {self.model_id}"
        )

    def call_claude(
        self,
        user_message_content: Any,
        use_extended_thinking: bool = False,
    ) -> Dict[str, Any]:
        """
        Call Claude with configurable extended thinking mode.

        Args:
            user_message_content: User message (string or list of content objects)
            use_extended_thinking: Whether to enable extended thinking mode

        Returns:
            Dict containing the response and optionally thinking process
        """
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                # Format the message content based on type
                if isinstance(user_message_content, str):
                    messages = [
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": user_message_content}],
                        }
                    ]
                elif isinstance(user_message_content, list):
                    messages = [{"role": "user", "content": user_message_content}]
                else:
                    raise ValueError(
                        f"Unsupported message content type: {type(user_message_content)}"
                    )

                # Prepare request body
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": messages,
                }

                # Add system prompt if configured
                if self.system_prompt:
                    body["system"] = self.system_prompt

                # Add extended thinking if requested
                if use_extended_thinking:
                    body["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": self.thinking_budget_tokens,
                    }
                    # For extended thinking, AWS requires temperature 1.0
                    body["temperature"] = 1.0

                    # Ensure max_tokens is greater than thinking_budget_tokens
                    if body["max_tokens"] <= self.thinking_budget_tokens:
                        body["max_tokens"] = self.thinking_budget_tokens + 2000
                        logging.info(
                            f"Adjusted max_tokens to {body['max_tokens']} for extended thinking"
                        )

                logging.debug(f"Request body: {json.dumps(body, indent=2)}")

                # Measure time
                start_time = time.time()

                # Make API call
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body),
                )

                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                logging.info(f"API call completed in {elapsed_time:.2f} seconds")

                # Parse response
                response_body = json.loads(response["body"].read())

                # Extract text and thinking content
                result = {}
                text_content = None
                thinking_content = None

                for content_block in response_body.get("content", []):
                    if content_block.get("type") == "thinking":
                        thinking_content = content_block.get("thinking")
                        result["thinking"] = thinking_content
                        logging.info("Extended thinking content received")
                    elif content_block.get("type") == "text":
                        text_content = content_block.get("text")
                        result["response"] = text_content

                # Try to parse JSON from text response if it exists
                if text_content:
                    try:
                        json_start = text_content.find("{")
                        if json_start != -1:
                            json_end = text_content.rfind("}") + 1
                            json_str = text_content[json_start:json_end]
                            parsed_json = json.loads(json_str)
                            # Only update result if we found valid JSON
                            for key, value in parsed_json.items():
                                if key != "thinking":  # Don't overwrite thinking
                                    result[key] = value
                    except json.JSONDecodeError:
                        logging.debug("No valid JSON found in response text")

                return result

            except Exception as e:
                last_error = str(e)
                logging.error(
                    f"Error calling Claude API on attempt {attempt + 1}: {last_error}"
                )

                attempt += 1
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor**attempt
                    logging.info(f"Retrying in {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)

        raise Exception(
            f"Failed to get valid response after {self.max_retries} attempts. Last error: {last_error}"
        )

    def get_model_info(self) -> Dict[str, Any]:
        """
        Return information about this client instance.
        """
        return {
            "model_id": self.model_id,
            "agent_name": self.agent_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "region": self.region,
            "thinking_budget_tokens": self.thinking_budget_tokens,
            "profile_name": self.profile_name,
        }
