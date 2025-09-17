from setuptools import find_packages, setup

setup(
    name="async-worker",
    version="0.1.0",
    description="Async Worker package for RabbitMQ task processing",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "aio-pika>=9.0.0",
        "loguru>=0.7.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
