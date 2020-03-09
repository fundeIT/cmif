accrued.db:
	python download.py
	python excel2csv.py
	python builddb.py
	rm -rf *csv
	rm -rf *xlsx
	
	# January 2020
	python 202001.py

clean:
	rm -f accrued.db
