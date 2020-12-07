all:
	ln prep/budget.db site/data
	ln prep/master.db site/data

clean:
	$(MAKE) clean -C prep
