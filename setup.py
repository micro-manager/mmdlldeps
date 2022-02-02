from setuptools import setup, find_packages

setup(
    name="mmdlldeps",
    python_requires=">=3.9",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["*.bat"]},
    entry_points={
        "console_scripts": [
            "mmdlldeps = mmdlldeps.__main__:main",
        ]
    },
)
