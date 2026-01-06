import paramiko
import time

host = '192.168.119.128'
user = 'bino'
password = '0000'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=10)

# Check last 10 lines of rhythm log to see if it's thinking
stdin, stdout, stderr = client.exec_command('tail -10 /home/bino/agi/logs/rhythm_think.log')
print("Linux Log:\n", stdout.read().decode())

# Check timestamp of the json file on Linux
stdin, stdout, stderr = client.exec_command('ls -l /home/bino/agi/outputs/thought_stream_latest.json')
print("Linux JSON:\n", stdout.read().decode())

client.close()
