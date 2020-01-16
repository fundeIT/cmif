# Repositorio del Centro de Monitoreo e Incidencia Fiscal

Clone the repository:

    $ git clone https://github.com/fundeIT/cmif.git

Create virtual environment and install requirements:

    $ virtualenv cmif
    $ source cmif/bin/activate
    $ cd cmif
    $ pip install -r requirements.txt

Build the budget database:

    $ make

Run the webserver:

    $ cd site
    $ python index.py -d
