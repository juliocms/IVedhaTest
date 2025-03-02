from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import datetime
import os

app = Flask(__name__)

elastic_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
es = Elasticsearch([{"host": elastic_host, "port": 9200}])

def create_index():
    """Cria o índice 'service_status' no Elasticsearch se não existir."""
    index_name = "service_status"
    
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "service_name": {"type": "keyword"},
                    "service_status": {"type": "keyword"},
                    "host_name": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        })
        print(f"✅ Índice '{index_name}' criado com sucesso.")
    else:
        print(f"🔹 Índice '{index_name}' já existe.")

@app.route("/add", methods=["POST"])
def add_status():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        data["created_at"] = datetime.datetime.now().isoformat()
        print(data)
        
        es.index(index="service_status", body=data)
        return jsonify({"message": "Status added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route("/healthcheck", methods=["GET"])
# def healthcheck():
#     try:
#         response = es.search(index="service_status", body={"query": {"match_all": {}}})
#         services = {}
#         overall_status = "UP"

#         if "hits" in response and "hits" in response["hits"]:
#             for hit in response["hits"]["hits"]:
#                 service = hit["_source"]
                                
#                 service_name = service.get("service_name")
#                 status_service = service.get("status")

#                 if service_name and status_service:
#                     services[service_name] = status_service
#                     if status_service == "DOWN":
#                         overall_status = "DOWN"
#                 else:
#                     print(f"Invalid service: {service}")

#         return jsonify({"application_status": overall_status, "services": services})
    
    # except Exception as e:
    #     return jsonify({"error": f"Failed to fetch from Elasticsearch: {str(e)}"}), 500
    
@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    try:
        query = {
            "query": {"match_all": {}},
            "size": 1000,
            "sort": [{"created_at": "desc"}]
        }

        response = es.search(index="service_status", body=query)
        services = {}
        overall_status = "UP"

        if "hits" in response and "hits" in response["hits"]:
            for hit in response["hits"]["hits"]:
                service = hit["_source"]
                                
                service_name = service.get("service_name")
                status_service = service.get("status")

                if service_name and status_service:
                    if service_name not in services:
                        services[service_name] = status_service
                        if status_service == "DOWN":
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
            "size": 1,
            "sort": [{"created_at": "desc"}]
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
    create_index()
    app.run(host="0.0.0.0", port=5000, debug=True)
