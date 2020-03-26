all:
	cp prep/accrued/build_from_alac/accrued.db site/data
	cp prep/budget/budget.db site/data
	cp prep/master.db site/data
	cp -r prep/shp site/shp

clean:
	$(MAKE) clean -C prep
