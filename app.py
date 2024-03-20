from dotenv import load_dotenv
import requests
import os
from flask import Flask, request, jsonify
from deepface import DeepFace
import pymongo
# from flask_cors import CORS
from waitress import serve

load_dotenv()
app = Flask(__name__)
# CORS(app)

db_URL = os.getenv('DB_URL')
# by default 5000
PORT = os.getenv('PORT', '5000')

# MongoDB Initialization
client = pymongo.MongoClient(db_URL)
database = client["deepface"]
collection = database["facial_database"]


@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    img_url = data.get('img_url')
    user = data.get('user')

    existing_image = collection.find_one({"img_url": img_url, "user": user})

    if (existing_image):
        return jsonify("Img already exist in the DB"), 400
    try:
        collection.insert_one({"img_url": img_url, "user": user})
        return jsonify("Img added Successfully"), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def retrieve_images_from_mongodb():
    image_collection = database["facial_database"]
    images = image_collection.find()
    images_list = list(images)
    return images_list


def save_image_to_local_storage(image_document):
    local_dir = 'DataImages'
    # Ensure the directory exists
    os.makedirs(local_dir, exist_ok=True)
    response = requests.get(image_document["img_url"])
    if response.status_code == 200:
        local_path = os.path.join(
            local_dir, f"{image_document['user']}_{image_document['_id']}.jpg")
        # Write the image data to a file
        with open(local_path, 'wb') as f:
            f.write(response.content)
    return


@app.route('/find', methods=['POST'])
def find():
    data = request.json
    img_url = data.get('img_url')

    try:
        images = retrieve_images_from_mongodb()
        # Save each image to the local directory
        for image in images:
            save_image_to_local_storage(image)
        # Use DeepFace to find the face in the images
        result = DeepFace.find(img_path=img_url, db_path='DataImages')
        final_res = []
        if (not result):
            return jsonify("No any matches found!")
        for res in result[0].identity:
            # extract userName from file name and append it to the array
            final_res.append(res[res.index('/')+1:res.index('_')])
        # Return the JSON response
        return jsonify(final_res)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=int(PORT))
    # app.run(debug=True)
