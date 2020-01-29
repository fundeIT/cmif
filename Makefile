all:
	$(MAKE) -C prep
	ln -sf prep/accrued/accrued.db site/data
	ln -sf prep/budget/budget.db site/data

clean:
	$(MAKE) clean -C prep
