from setuptools import setup

if __name__ == "__main__":
    setup(
        name="sequence-parser",
        packages=["sequence_parser"],
        install_requires=[
            "numpy",
            "matplotlib",
            "networkx",
        ]
    )
