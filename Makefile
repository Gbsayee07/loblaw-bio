.PHONY: setup pipeline dashboard

setup:
	pip3 install -r requirements.txt || pip3 install -r requirements.txt --break-system-packages

pipeline:
	python3 pipeline.py

dashboard:
	streamlit run dashboard/app.py
