import typer

from .client.gitea import GiteaAPIClient
from .config import GiteaConfig

app = typer.Typer()


@app.command()
def cleanup(
    gitea_url: str = typer.Option(
        ...,
        "--endpoint",
        "-e",
        help="The Gitea to connect to ( e.g. https://try.gitea.io ).",
    ),
    owner: str = typer.Option(
        ...,
        "--owner",
        "-o",
        help="Owner of the packages.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Don't actually delete anything (dry run).",
    ),
):
    config = GiteaConfig(endpoint=gitea_url)
    client = GiteaAPIClient(config)
    tags = client.container_tags(owner)

    # YAML
    print("---")
    if dry_run:
        print("run: dry")
    else:
        print("run: delete")
    print("gitea:")
    print(f"  endpoint: {gitea_url}")
    print(f"owner: {owner}")

    print("tags:")

    for name in tags:
        for tag in list(tags[name]):
            if "sha256:" not in tag:
                manifest = client.manifest(owner, name, tag)
                tags[name].remove(tag)
                if "layers" in manifest:
                    raise Exception("manifest had layers: {owner}/{name}:{tag}")
                if "manifests" in manifest:
                    for digest in map(lambda m: m["digest"], manifest["manifests"]):
                        tags[name].remove(digest)

        l_tags = list(tags[name])
        if len(l_tags) == 0:
            print(f"  {name}: []")
        else:
            print(f"  {name}:")
        for tag in l_tags:
            print(f'   - "{tag}"')
            if not dry_run:
                client.delete_container(owner, name, tag)


main = app
if __name__ == "__main__":
    main()
