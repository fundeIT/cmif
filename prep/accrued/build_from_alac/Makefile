accrued.db:
	python download.py
	python excel2csv.py
	python builddb.py
	rm -rf *csv
	rm -rf *xlsx

clean:
	rm -f accrued.db
