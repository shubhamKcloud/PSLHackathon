from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .agent import AIAgent

# Load environment variables from .env file
load_dotenv()

class ModelClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4.1",
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv(
            "OPENAI_BASE_URL",
            "https://hub-proxy-service.thankfulfield-16b4d5d6.eastus.azurecontainerapps.io"
        )
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set. Create a .env file with your OpenAI API key.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def summarize(self, prompt: str) -> str:
        """Call GPT-4.1 to generate a summary or analysis."""
        try:
            print(f"[DEBUG] Calling API with model: {self.model}")
            print(f"[DEBUG] Gateway URL: {self.base_url}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI incident analysis assistant. Provide concise, actionable analysis. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
            )
            content = response.choices[0].message.content or "No response"
            print(f"[DEBUG] API response received: {content[:200]}...")
            return content
        except Exception as e:
            print(f"[DEBUG] Error calling API: {str(e)}")
            return f"Error calling API: {str(e)}"


def main() -> None:
    model_client = ModelClient()
    
    # Optional CloudWatch configuration (set via environment variables)
    cloudwatch_config = None
    if os.getenv("CLOUDWATCH_LOG_GROUP"):
        cloudwatch_config = {
            "enabled": True,
            "log_group": os.getenv("CLOUDWATCH_LOG_GROUP"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        }
    
    agent = AIAgent(
        log_sources=["logs"],
        ticketing_config={"provider": "file", "ticket_dir": "tickets"},
        model_client=model_client,
        knowledge_base_dir=Path(__file__).resolve().parents[2] / "knowledgeBase",
        cloudwatch_config=cloudwatch_config,
    )
    print("=" * 60)
    print("🚨 AI Incident Agent Monitor Started")
    print("=" * 60)
    print(f"📁 Watching logs folder: logs/")
    if cloudwatch_config:
        print(f"☁️  CloudWatch log group: {cloudwatch_config.get('log_group')}")
    print(f"🎫 Tickets saved to: tickets/")
    print(f"🤖 Using model: {model_client.model}")
    print(f"🌐 Gateway: {model_client.base_url}")
    print("=" * 60)
    agent.run_forever(interval=5.0)


if __name__ == "__main__":
    main()
