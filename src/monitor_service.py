import json
import time
import socket
import requests
from datetime import datetime

API_URL = "http://localhost:5000/add"

def send_to_api(service_data):
    try:
        response = requests.post(API_URL, json=service_data, headers={"Content-Type": "application/json"})
        if response.status_code == 201:
            print(f"Service {service_data['service_name']} successfully sent")
        else:
            print(f"Error sending {service_data['service_name']} - Code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"API connect fail: {e}")

def check_service(service_name, port):
    try:
        sock = socket.create_connection((service_name, port), timeout=3)
        sock.close()
        return "UP"
    except Exception:
        return "DOWN"

def monitor_services():
    services = {
        "httpd": 80,
        "rabbitmq": 5672,
        "postgres": 5432
    }
    hostname = socket.gethostname()
    results = []
    overall_status = "UP"
    
    for service, port in services.items():
        status = check_service(service, port)
        service_data = {
            "service_name": service,
            "status": status,
            "host_name": hostname
        }
        results.append(service_data)
        
        send_to_api(service_data)
        
        if status == "DOWN":
            overall_status = "DOWN"
    
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"monitoring-status-{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
    
    return overall_status, filename

if __name__ == "__main__":
    while True:
        status, file_created = monitor_services()
        time.sleep(180)
