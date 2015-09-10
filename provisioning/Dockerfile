FROM centos:6
MAINTAINER Pontus Larsson <b97pla@gmail.com>
RUN yum -y update; \
    yum clean all;
RUN yum install -y tar wget bzip2;

# set up a non-root user and run the rest of the commands as that user
RUN adduser tornadouser; \
    mkdir /opt/tornado; \
    chown -R tornadouser /opt/tornado;

USER tornadouser

# deploy miniconda for managing the python environment
RUN cd /tmp; \
    wget https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh; \
    bash miniconda.sh -b -p /opt/tornado/miniconda; \
    export PATH="/opt/tornado/miniconda/bin:$PATH"; \
    hash -r; \
    conda config --set always_yes yes --set changeps1 no; \
    conda update -q conda; \
    conda info -a;

ENV PATH=/opt/tornado/miniconda/bin:$PATH

# set up a new python environment and install the dependencies
RUN conda create -n tornado python=2.7; \
    source activate tornado; \
    conda install -y tornado pandas requests;

# deploy the webapp and get some external libraries
RUN cd /opt/tornado; \
    git clone https://github.com/b97pla/ngi_stats.git; \
    wget https://cdn.rawgit.com/novus/nvd3/v1.8.1/build/nv.d3.min.js -O ngi_stats/javascript/nv.d3.min.js; \
    wget https://cdn.rawgit.com/novus/nvd3/v1.8.1/build/nv.d3.css -O ngi_stats/css/nv.d3.css;

# launch the web service
WORKDIR /opt/tornado/ngi_stats
EXPOSE 8888
ENTRYPOINT ["/opt/tornado/miniconda/envs/tornado/bin/python"]
CMD ["/opt/tornado/ngi_stats/webapp.py"]

