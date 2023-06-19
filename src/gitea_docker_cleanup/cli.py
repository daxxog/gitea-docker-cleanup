import typer


def cli(name: str):
    print(f"Hello {name}")


def main():
    typer.run(cli)


if __name__ == "__main__":
    main()
