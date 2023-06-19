from pydantic import BaseSettings


class GiteaConfig(BaseSettings):
    access_token: str
    endpoint: str

    class Config:
        env_prefix = "GITEA_"
