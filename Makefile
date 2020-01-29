all:
	$(MAKE) -C prep
	cp prep/accrued/accrued.db site/data
	cp prep/budget/budget.db site/data

clean:
	$(MAKE) clean -C prep
