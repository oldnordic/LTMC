# Compatibility config module for LTMC binary
# This redirects to the proper LTMC settings module

from ltmc_mcp_server.config.settings import LTMCSettings

# Export settings for compatibility
settings = LTMCSettings()