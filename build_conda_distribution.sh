conda skeleton pypi animapp --version $(head -n1 animapp_pyqt5/animapp/_version.py | cut -d= -f2 | sed 's/"//g')
conda-build animapp
conda convert --platform all /home/srao/miniconda3/envs/packaging/conda-bld/linux-64/animapp-0.1.5.6-py38_0.tar.bz2 -o all_platforms/
# conda convert --platform all <tar.bz2 from conda-bld folder> -o all_platforms/
# mkdir all_platforms/linux-64
# cp <tar.bz2 from conda-bld folder> all_platforms/linux-64/
# anaconda login
# for each in all_platforms/**/*; do echo $each; anaconda upload $each; done
