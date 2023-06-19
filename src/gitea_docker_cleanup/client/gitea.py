from base64 import b64encode
from typing import Iterable

import httpx

from gitea_docker_cleanup.config import GiteaConfig
from gitea_docker_cleanup.models.gitea import Package


class GiteaAPIClient:
    def __init__(self, config: GiteaConfig):
        self.config = config
        self.docker_auth = b64encode(
            f"_:{self.config.access_token}".encode("utf-8")
        ).decode("utf-8")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "Authorization": f"token {self.config.access_token}",
        }

    @property
    def docker_registry_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Basic {self.docker_auth}",
        }

    def containers(self, owner: str) -> Iterable[Package]:
        url = f"{self.config.endpoint}/api/v1/packages/{owner}?type=container"
        page = 0
        results = [None]
        while len(results) > 0:
            page += 1
            r = httpx.get(f"{url}&page={page}", headers=self.headers)
            if r.status_code == 200:
                results = r.json()
                for result in results:
                    yield Package(**result)
            else:
                raise Exception(f"Invalid status code from API: {r.status_code}")

    def container_tags(self, owner: str) -> dict[str, set[str]]:
        d = dict()
        for container in self.containers(owner):
            if container.name not in d:
                d[container.name] = set()
            d[container.name].add(container.version)

        return d

    def manifest(self, owner: str, container_name: str, container_tag: str) -> dict:
        url = (
            f"{self.config.endpoint}/v2/{owner}/"
            + f"{container_name}/manifests/{container_tag}"
        )
        r = httpx.get(url, headers=self.docker_registry_headers)
        if r.status_code == 200:
            return r.json()
        else:
            raise Exception(f"Invalid status code from Docker API: {r.status_code}")

    def delete_container(self, owner: str, container_name: str, container_tag: str):
        url = (
            f"{self.config.endpoint}/api/v1/packages/{owner}/"
            + f"container/{container_name}/{container_tag}"
        )
        r = httpx.delete(url, headers=self.headers)
        if r.status_code == 204:
            pass
        else:
            raise Exception(f"Invalid status code from API: {r.status_code}")
