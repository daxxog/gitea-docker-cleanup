import typer

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}")


main = app
if __name__ == "__main__":
    main()
