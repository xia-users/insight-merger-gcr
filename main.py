import os
import json
from flask import Flask, request, Response, render_template
import google.cloud.logging
import google.auth
from xialib.service import service_factory

# Global Setting
app = Flask(__name__)
project_id = google.auth.default()[1]

# Configuration Load
with open(os.path.join('.', 'config', 'global_conn_config.json')) as fp:
    global_conn_config = json.load(fp)
with open(os.path.join('.', 'config', 'object_config.json')) as fp:
    object_config = json.load(fp)

# Global Object Factory
global_connectors = service_factory(global_conn_config)

# Log configuration
client = google.cloud.logging.Client()
client.get_default_handler()
client.setup_logging()


@app.route('/', methods=['GET', 'POST'])
def insight_merger():
    merger = service_factory(object_config, global_connectors)
    if request.method == 'GET':
        return render_template("index.html"), 200
    envelope = request.get_json()
    if not envelope:
        return "no Pub/Sub message received", 204
    if not isinstance(envelope, dict) or 'message' not in envelope:
        return "invalid Pub/Sub message format", 204
    data_header = envelope['message']['attributes']

    if merger.merge_all_data(data_header['topic_id'], data_header['table_id']):
        return "merge message received", 200 # pragma: no cover
    else:  # pragma: no cover
        return "merge message to be resent", 400  # pragma: no cover

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))  # pragma: no cover