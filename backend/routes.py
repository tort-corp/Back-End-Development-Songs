from . import app
import os
import json
import pymongo
from pymongo.server_api import ServerApi
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")

# env variables in .bashrc
mongodb_service = os.environ.get("MONGODB_SERVICE")
mongodb_username = os.environ.get("MONGODB_USERNAME")
mongodb_password = os.environ.get("MONGODB_PASSWORD")
# mongodb_port = os.environ.get('MONGODB_PORT')


print(f"The value of MONGODB_SERVICE is: {mongodb_service}")

if mongodb_service == None:
    app.logger.error("Missing MongoDB server in the MONGODB_SERVICE variable")
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = uri = f"mongodb+srv://{mongodb_username}:{mongodb_password}@{mongodb_service}"

else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)


def parse_json(data):
    return json.loads(json_util.dumps(data))


######################################################################
# INSERT CODE HERE
######################################################################

######################################################################
# RETURN HEALTH OF THE APP
######################################################################


@app.route("/health")
def health():
    """
    Returns:
        200: if status OK
    """
    return jsonify(dict(status="OK")), 200


######################################################################
# COUNT THE NUMBER OF SONGS
######################################################################


@app.route("/count")
def count():
    """
    Return:
        length of data and status 200

    """
    count = db.songs.count_documents({})

    return {"count": f"{count}"}, 200


######################################################################
# GET ALL SONGS
######################################################################
@app.route("/song")
def song():
    """
    Return
      list of all songs and status 200
      404: No data exists
    """
    results = db.songs.find({})
    results_list = list(results)
    if not results or len(results_list) < 1:
        return json_util.dumps(results_list), 404

    return json_util.dumps(results_list), 200


######################################################################
# GET A SONG
######################################################################
@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """
    Gets specific song json based on song id key.
    Returns:
        json: song json based on id received in request
        404: No song of that id found
    """
    results = db.songs.find_one({"id": id})
    if not results:
        return {"message": f"song with id {id} not found"}, 404

    return parse_json(results), 200


######################################################################
# CREATE A SONG
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    # get data from the json body
    song_in = request.json

    print(song_in["id"])

    # if the id is already there, return 303 with the URL for the resource
    song = db.songs.find_one({"id": song_in["id"]})
    if song:
        return {"Message": f"song with id {song_in['id']} already present"}, 302

    # what is this syntax again?
    insert_id: InsertOneResult = db.songs.insert_one(song_in)

    return {"inserted id": parse_json(insert_id.inserted_id)}, 201


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):

    # get data from the json body
    song_in = request.json

    song = db.songs.find_one({"id": id})

    if song == None:
        return {"message": "song not found"}, 404

    updated_data = {"$set": song_in}

    result = db.songs.update_one({"id": id}, updated_data)

    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return parse_json(db.songs.find_one({"id": id})), 201



@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):

    result = db.songs.delete_one({"id": id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "", 204