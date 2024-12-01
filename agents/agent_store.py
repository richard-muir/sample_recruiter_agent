class AgentStore:
    def __init__(self):
        self.candidate_agents = {}
        self.recruiter_agents = {}

    def get_candidate_agents(self):
        """Return the dictionary storing candidate agents."""
        return self.candidate_agents

    def get_recruiter_agents(self):
        """Return the dictionary storing recruiter agents."""
        return self.recruiter_agents
