# Repositorio del Centro de Monitoreo e Incidencia Fiscal

Clone the repository:

    $ git clone https://github.com/fundeIT/cmif.git

Create virtual environment and install requirements:

    $ virtualenv cmif
    $ source cmif/bin/activate
    $ cd cmif
    $ pip install -r requirements.txt

Build the budget database:

    $ cd prep/budget
    $ python prepare.py

Setup the webserver:

    $ cd ../../site/
    $ mkdir data
    $ ln ../prep/budget/budget.db data/
    
Run the webserver:

    $ python index.py -d
