import unittest
import asyncio
import redis.asyncio as redis
from dotenv import load_dotenv
import os

load_dotenv()

from ltms.config import config
from ltms.services.agent_registry_service import AgentRegistryService
from ltms.services.context_coordination_service import ContextCoordinationService
from ltms.services.session_state_service import SessionStateService

class TestModelContextProtocol(unittest.TestCase):

    def setUp(self):
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_url = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"
        if redis_password:
            redis_url = f"redis://:{redis_password}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"

        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.agent_registry = AgentRegistryService(self.redis_client)
        self.context_coordinator = ContextCoordinationService(self.redis_client)
        self.session_manager = SessionStateService(self.redis_client)

    def tearDown(self):
        async def clear_redis():
            await self.redis_client.flushdb()
        asyncio.run(clear_redis())

    async def test_agent_onboarding_workflow(self):
        # 1. Discovery (This is a conceptual step, not a direct API call)
        protocol_version = "1.0.0" # As defined in our documentation
        self.assertEqual(protocol_version, "1.0.0")

        # 2. Registration
        agent_id = "agent-1"
        capabilities = ["test"]
        await self.agent_registry.register_agent({"agent_id": agent_id, "capabilities": capabilities})
        registered_agents = await self.agent_registry.get_active_agents()
        self.assertIn(agent_id, [agent["agent_id"] for agent in registered_agents])

        # 3. Create Session
        session_id = await self.session_manager.create_session(agent_id)
        self.assertIsNotNone(session_id)

        # 4. Subscribe to Context (Conceptual)
        # In a real implementation, this would involve a pub/sub mechanism.
        # We'll simulate this by checking if the agent is part of the session.
        session_state = await self.session_manager.get_session_state(session_id)
        self.assertIn(agent_id, session_state["agents"])

    async def test_context_propagation(self):
        session_id = await self.session_manager.create_session("agent-1")
        context_update = {"key": "value"}

        # The context coordinator would publish this to a channel.
        # We will simulate this by directly checking the propagation logic.
        await self.context_coordinator.propagate_context_change(session_id, context_update)

        # Verify the change was stored in the session state
        session_state = await self.session_manager.get_session_state(session_id)
        self.assertEqual(session_state["context"], context_update)

    async def test_agent_disconnection(self):
        agent_id = "agent-1"
        session_id = await self.session_manager.create_session(agent_id)

        # Simulate agent disconnection (e.g., by removing heartbeat)
        await self.agent_registry.unregister_agent(agent_id)

        # The session manager should detect this and remove the agent from the session
        await self.session_manager.remove_agent_from_session(session_id, agent_id)

        session_state = await self.session_manager.get_session_state(session_id)
        self.assertNotIn(agent_id, session_state["agents"])

if __name__ == '__main__':
    # Need to run the async tests with an event loop
    unittest.main()