# Data Civic Platform - Centro de Monitoreo e Incidencia Fiscal

Review online: <http://fiscal.funde.org>

## Installation

Clone the repository:

    $ git clone https://github.com/fundeIT/cmif.git

Create virtual environment and install requirements:

    $ virtualenv cmif
    $ source cmif/bin/activate
    $ cd cmif
    $ pip install -r requirements.txt

Build databases:

    $ make

Run the webserver:

    $ cd site
    $ python index.py -d
