#Paria Sarzaeim 100863215

#import necassary libraries
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response
from datetime import datetime
from PIL import Image, ImageFilter
import io
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials


#make an instance of flask
app = Flask(__name__)

#sendgrid api to enable email notification service
SENDGRID_API_KEY = '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'


#set up the client for computer vision API
endpoint = "https://imageprocess-computervision.cognitiveservices.azure.com/"
subscription_key = "1cce0bb061464795a872b1c3a4ff75e6"

#Blob Storage Configuration
CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=coviddiag;AccountKey=7KQqN6FW0gMWg9rL8XPk6v0t6OgrPtq3ijeqou2k6OAU9fabGOHIBHKoZV3dkkR4Fr3QpwPgzYDk+AStyCfFkA==;EndpointSuffix=core.windows.net'
CONTAINER_NAME = 'imageprocess'
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

#first page of the web app
@app.route('/', methods=['GET', 'POST'])
def index():
   if request.method == 'POST':
      name = request.form['name']
      email = request.form.get('email')
      password = request.form.get('password')
      
      #retrieve the password for the entered email from Blob Storage
      blob_name = f"{email}.txt"
      blob_client = container_client.get_blob_client(blob_name)
      blob_data = blob_client.download_blob().content_as_text()

      if blob_data == password:
        #email and password are correct so go to the next page
         return render_template('hello.html', name=name)
      else:
         #passwords don't match, redirect to index page
         print('Incorrect email or password -- redirecting')
         return redirect(url_for('index'))
   
   #render the index page with the login form
   return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/hello', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        #get the uploaded file
        image = request.files['image']
        option = request.form['filter']
        
        if option == '1':
          #for blurring the image
            img = Image.open(image)
            blurred_img = img.filter(ImageFilter.BLUR)
            #convert the blurred image to bytes and store in memory
            img_bytes = io.BytesIO()
            blurred_img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            if image:
                #create a response with the blurred image
                response = make_response(img_bytes.getvalue())
                response.headers.set('Content-Type', 'image/png')
                response.headers.set('Content-Disposition', 'inline', filename='blurred_image.png')
                return response

        if option == '2':
          #for finding the edges in the image
            img = Image.open(image)
            blurred_img = img.filter(ImageFilter.FIND_EDGES)
            # Convert the blurred image to bytes and store in memory
            img_bytes = io.BytesIO()
            blurred_img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            if image:
                #create a response
                response = make_response(img_bytes.getvalue())
                response.headers.set('Content-Type', 'image/png')
                response.headers.set('Content-Disposition', 'inline', filename='blurred_image.png')
                return response         
        if option == '3':
          #text extraction
            headers = {
                'Content-Type': 'application/octet-stream',
                'Ocp-Apim-Subscription-Key': subscription_key,
            }
            response = requests.post(endpoint, headers=headers, data=image.read())
            response.raise_for_status()
            #extract the text from the response
            result = response.json()
            lines = []
            for region in result['analyzeResult']['readResults'][0]['lines']:
                lines.append(region['text'])
            #redirect to the endpoint with the extracted text as a parameter
            return render_template('hello.html', text='\n'.join(lines))
    #render the page with the image upload form
    return render_template('hello.html')

#sign up page
@app.route('/signup', methods=['POST','GET'])
def signup():
   if request.method == 'POST':
      #get the user's information from the form
      name = request.form.get('name')
      email = request.form.get('email')
      password = request.form.get('password')

      #check if the email already exists
      blob_name = f"{email}.txt"
      blob_client = container_client.get_blob_client(blob_name)
      if blob_client.exists():
         return render_template('signup.html', error="Email already exists.")
        
      #create a new record in blob storage with the user's password
      container_client.upload_blob(name=blob_name, data=password)
      
      #create a new mail object that will be sent to the registered user
      message = Mail(
      from_email='paria.sarzaeim@ontariotechu.net',
      to_emails=email,
      subject='Welcome to My Web App!',
      html_content='Thank you for signing up!')
      
      #use the sendgrid client to send the email
      try:
         sg = sendgrid.SendGridAPIClient(app.config[SENDGRID_API_KEY])
         response = sg.send(message)
         print(f'Successfully sent email to {email}')
      except Exception as e:
         print(f'Error sending email to {email}: {str(e)}')


      #redirect to the first page to login
      return redirect(url_for('index'))

   #render the signup page
   return render_template('sign-up.html')

 return redirect(url_for('index'))  


if __name__ == '__main__':
   app.run()
