all:
	ln -s prep/budget.db site/data
	ln -s prep/master.db site/data

clean:
	$(MAKE) clean -C prep
