all:
	$(MAKE) -C prep
	ln -f prep/accrued/accrued.db site/data
	ln -f prep/budget/budget.db site/data

clean:
	$(MAKE) clean -C prep
