from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import os

app = Flask(__name__)

elastic_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
es = Elasticsearch([{"host": elastic_host, "port": 9200}])

@app.route("/add", methods=["POST"])
def add_status():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        es.index(index="service_status", body=data)
        return jsonify({"message": "Status added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    try:
        response = es.search(index="service_status", body={"query": {"match_all": {}}})
        services = {}
        overall_status = "UP"

        if "hits" in response and "hits" in response["hits"]:
            for hit in response["hits"]["hits"]:
                service = hit["_source"]
                                
                nome_servico = service.get("service_name")
                status_servico = service.get("status")

                if nome_servico and status_servico:
                    services[nome_servico] = status_servico
                    if status_servico == "DOWN":
                        overall_status = "DOWN"
                else:
                    print(f"Invalid service: {service}")

        return jsonify({"application_status": overall_status, "services": services})
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch from Elasticsearch: {str(e)}"}), 500

@app.route("/healthcheck/<service>", methods=["GET"])
def healthcheck_service(service):
    try:
        query = {
            "query": {
                "match": {"service_name": service}
            },
            "size": 1
        }

        response = es.search(index="service_status", body=query)

        if response["hits"]["hits"]:
            service_data = response["hits"]["hits"][0]["_source"]
            return jsonify({"service": service_data["service_name"], "status": service_data["status"]})
        else:
            return jsonify({"error": "Service not found"}), 404

    except Exception as e:
        return jsonify({"error": f"Failed to fetch service from Elasticsearch: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
