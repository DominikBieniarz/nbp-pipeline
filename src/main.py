import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

def main() -> None:
    print("nbp-pipeline: setup OK")

if __name__ == "__main__":
    main()