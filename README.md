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

Run a debug webserver:

    $ cd site
    $ python index.py -d
    
Run a production server:

    $ cd site
    $ python index.py -s
