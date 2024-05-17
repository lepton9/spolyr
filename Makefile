
run:
	python spolyr.py

build:
	python -m PyInstaller --onefile spolyr.py

clean:
	rm -rf build dist *.spec __pycache__

