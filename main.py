import os
import json
import base64
import gzip
import hashlib
from flask import Flask, request, Response, render_template
import google.auth
from google.cloud import pubsub_v1
from google.cloud import firestore
import google.cloud.logging
from xialib_pubsub import PubsubPublisher
from xialib_firestore import FirestoreDepositor
from pyinsight import Insight, Merger
from xialib.service import service_factory

# Global Setting
app = Flask(__name__)
project_id = google.auth.default()[1]

# Configuration Load
with open(os.path.join('.', 'config', 'insight_config.json')) as fp:
    insight_config = json.load(fp)
with open(os.path.join('.', 'config', 'global_conn_config.json')) as fp:
    global_conn_config = json.load(fp)
with open(os.path.join('.', 'config', 'object_config.json')) as fp:
    object_config = json.load(fp)

# Global Object Factory
global_connectors = service_factory(global_conn_config)
insight_messager = service_factory(insight_config['messager'], global_connectors)
Insight.set_internal_channel(messager=insight_messager,
                             channel=insight_config.get('control_channel', project_id),
                             topic_cockpit=insight_config['control_topics']['cockpit'],
                             topic_cleaner=insight_config['control_topics']['cleaner'],
                             topic_merger=insight_config['control_topics']['merger'],
                             topic_packager=insight_config['control_topics']['packager'],
                             topic_loader=insight_config['control_topics']['loader'],
                             topic_backlog=insight_config['control_topics']['backlog']
)

# Log configuration
client = google.cloud.logging.Client()
client.get_default_handler()
client.setup_logging()


@app.route('/', methods=['GET', 'POST'])
def insight_receiver():
    if request.method == 'GET':
        merger = service_factory(object_config, global_connectors)
        return render_template("index.html"), 200
    merger = service_factory(object_config, global_connectors)
    envelope = request.get_json()
    if not envelope:
        return "no Pub/Sub message received", 204
    if not isinstance(envelope, dict) or 'message' not in envelope:
        return "invalid Pub/Sub message format", 204
    data_header = envelope['message']['attributes']

    if merger.merge_data(data_header['topic_id'],
                         data_header['table_id'],
                         data_header['merge_key'],
                         int(data_header['merge_level']),
                         int(data_header['target_merge_level'])):
        return "merge message received", 200 # pragma: no cover
    else:  # pragma: no cover
        return "merge message to be resent", 400  # pragma: no cover

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))  # pragma: no cover