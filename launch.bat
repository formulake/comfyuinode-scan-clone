@echo off
echo Activating virtual environment...
call venv\Scripts\activate

echo Launching the Gradio app...
python app.py

pause
