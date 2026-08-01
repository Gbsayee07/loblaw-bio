.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt || pip install -r requirements.txt --break-system-packages

pipeline:
	python pipeline.py

dashboard:
	streamlit run dashboard/app.py
