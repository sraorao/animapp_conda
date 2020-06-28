import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("animapp/_version.py", "r") as fh:
    """
    Get version number from animapp/_version.py and parse the string
    """
    __version__ = fh.readlines()[0].split("=")[1].strip().strip('"')

setuptools.setup(
    name="animapp",
    version=__version__,
    author="Srinivasa Rao",
    author_email="srinivasarao.rao@gmail.com",
    description="A package to track the movement of an object (a small animal) in a video",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sraorao/animapp_conda",
    packages=setuptools.find_packages(),
    entry_points={'console_scripts': ['threshold=animapp.set_thresholds:main', 'animapp=animapp.animapp:main'],},
    package_dir={'animapp':'animapp'},
    package_data={
        'animapp': ['data_files/*.*'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
