import requests
import os
from flask import Flask, request, jsonify
from deepface import DeepFace
import pymongo
# from flask_cors import CORS
from waitress import serve

app = Flask(__name__)
# CORS(app)

db_URL = os.getenv('DB_URL')
PORT = os.getenv('PORT', '5000')  # by default 5000

# MongoDB Initialization
client = pymongo.MongoClient(db_URL)
database = client["deepface"]
collection = database["facial_database"]


@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    img_path = data.get('img1_path')
    img_user = data.get('img1_user')
    try:
        collection.insert_one({"img_url": img_path, "user": img_user})
        return jsonify("Img added Successfully")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def retrieve_images_from_mongodb():
    image_collection = database["facial_database"]
    images = image_collection.find()
    images_list = list(images)

    return images_list


# IDs of local stored imgs
# stored_imgs = []
def save_image_to_local_storage(image_document):
    local_dir = 'DataImages'
    # found = False
    # print(image_document['_id'])
    # if (image_document['_id'] in stored_imgs):
    #     return

    # for res in :
    #     stored_imgs.append(res[res.index('/')+1:res.index('_')])
    #     # extract userName from file name and append it to the array
    # for filename in os.listdir(local_dir):
    #     # Check if the file is an image (you might want to adjust this condition based on your file naming convention)
    #     if filename.endswith(".jpg"):
    #         # Extract userName from file name and append it to the array
    #         # Assuming the file name format is 'userName_imageName.jpg'
    #         userName = filename.split('_')[0]
    #         stored_imgs.append(userName)
    # for x in stored_imgs:
    #     if image_document['_id'] == x:
    #         found = True  # Set the flag to True if the ID is found
    #         break  # Exit the loop as soon as the ID is found
    # if found:
    #     return
    # if not found:  # Only append the ID if it was not found in the list
    #     stored_imgs.append(image_document['_id'])

    # Ensure the directory exists
    os.makedirs(local_dir, exist_ok=True)
    response = requests.get(image_document["img_url"])
    # image = Image.open(io.BytesIO(response.content))
    if response.status_code == 200:
        image_filename = f"{image_document['user']}_.jpg"
        filename, file_extension = os.path.splitext(image_filename)
        local_path = os.path.join(
            local_dir, f"{filename}{image_document['_id']}{file_extension}")
        # Write the image data to a file
        with open(local_path, 'wb') as f:
            f.write(response.content)
    return


@app.route('/find', methods=['POST'])
def find():
    data = request.json
    img_path = data.get('img_path')

    try:
        images = retrieve_images_from_mongodb()
        # Save each image to the local directory
        for image in images:
            save_image_to_local_storage(image)
        # Use DeepFace to find the face in the images
        result = DeepFace.find(img_path=img_path, db_path='DataImages')
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
    # logging.basicConfig(level=logging.DEBUG)  # Enable debug logging
    # app.run(debug=True)
    serve(app, host='0.0.0.0', port=int(PORT))
