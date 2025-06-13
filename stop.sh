ps aux | grep 'python3 app.py --host=0.0.0.0' | grep -v grep | awk '{print $2}' | xargs -r kill
