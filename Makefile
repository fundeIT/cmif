all:
	cp prep/accrued/build_from_alac/accrued.db site/data
	cp prep/budget/budget.db site/data

clean:
	$(MAKE) clean -C prep
