
import asyncio
import json
import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from backend.agents.core.orchestrator import PipelineOrchestrator
from backend.utils.logger import get_logger

logger = get_logger("debug_analysis")

async def test():
    orchestrator = PipelineOrchestrator()
    query = "analyze Barranquilla vs Real Santander"
    
    print(f"Starting analysis for: {query}")
    
    async for event in orchestrator.run_pipeline(query):
        try:
            data = json.loads(event)
            event_type = data.get("event")
            
            if event_type == "agent_start":
                print(f"▶ Agent started: {data.get('agent')}")
            elif event_type == "agent_complete":
                print(f"✓ Agent completed: {data.get('agent')} in {data.get('execution_time_ms')}ms")
            elif event_type == "agent_error":
                print(f"✗ Agent failed: {data.get('agent')} Error: {data.get('error')}")
            elif event_type == "agent_timeout":
                print(f"⌛ Agent timeout: {data.get('agent')}")
            elif event_type == "pipeline_complete":
                print(f"🏁 Pipeline complete!")
                # print(json.dumps(data.get('data'), indent=2))
        except Exception as e:
            print(f"Error parsing event: {e}")

if __name__ == "__main__":
    asyncio.run(test())
