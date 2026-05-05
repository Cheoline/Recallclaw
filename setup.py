from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="recallclaw",
    version="1.0.0",
    description="Sistema de memoria semántica a largo plazo para agentes de inteligencia artificial",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cheoline",
    author_email="cheoline@hotmail.com",
    url="https://github.com/Cheoline/Recallclaw",
    packages=find_packages(),
    install_requires=[
        "sentence-transformers>=3.0.0",
        "spacy>=3.0.0",
        "torch>=2.0.0",
        "numpy>=1.24.0",
        "requests>=2.28.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="ai memory rag vector semantic compression nlp",
)
