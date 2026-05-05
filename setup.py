from setuptools import setup, find_packages

setup(
    name="recallclaw",
    version="1.0.0",
    description="Sistema de memoria Positrónica de ultra-alta compresión para IA",
    author="Tu Nombre/Organización",
    packages=find_packages(),
    install_requires=[
        "sentence-transformers>=3.0.0",
        "spacy>=3.0.0"
    ],
    python_requires=">=3.9",
)
