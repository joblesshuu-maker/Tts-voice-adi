import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tortoise-tts",
    packages=setuptools.find_packages(),
    version="3.0.0",
    author="James Betker",
    author_email="james@adamant.ai",
    description="A high quality multi-voice text-to-speech library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/neonbjb/tortoise-tts",
    project_urls={
        "Documentation": "https://github.com/neonbjb/tortoise-tts/wiki",
        "Source": "https://github.com/neonbjb/tortoise-tts",
        "Bug Tracker": "https://github.com/neonbjb/tortoise-tts/issues",
    },
    scripts=[
        'scripts/tortoise_tts.py',
    ],
    include_package_data=True,
    install_requires=[
        'tqdm',
        'rotary_embedding_torch',
        'inflect',
        'progressbar',
        'einops',
        'unidecode',
        'scipy',
        'librosa',
        'transformers==4.31.0',
        'tokenizers==0.14.0',
        'scipy==1.13.1',  # Added missing comma here
        # Uncomment to enable DeepSpeed support:
        # 'deepspeed==0.8.3',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.6",
)
