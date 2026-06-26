from pyngrok import ngrok
import subprocess, threading, time, os

def start_flask():
    os.chdir(os.path.dirname(__file__))
    subprocess.run(['python', 'app.py'])

t = threading.Thread(target=start_flask, daemon=True)
t.start()
time.sleep(3)

public_url = ngrok.connect(5000, bind_tls=True)
print(f'\n{"="*50}')
print(f'  PUBLIC URL: {public_url}')
print(f'{"="*50}')
print('  قفله: اضغط Ctrl + C')
print(f'{"="*50}\n')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ngrok.kill()
