# agent_wrapper_mock

Demonstrates a mock agent wrapper. The mock agent proposes actions; the wrapper
rejects direct protected actions and only lets seed/host-mediated local actions
continue.

```bash
uv run python examples/agent_wrapper_mock/mock_agent.py
```
