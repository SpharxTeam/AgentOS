# Community Agents

This directory is intended for community-contributed agents.  
Each agent should be placed in its own subdirectory and include:

- `agent.py` - implementation (subclassing `BaseAgent`)
- `contract.json` - valid agent contract
- `prompts/` - system prompts (optional)

Please ensure your agent passes contract validation (`validate_contract.py`) before submitting.