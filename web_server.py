from flask import Flask,request
import boto3
import time

#Initializing Hash Map which saves the responses from the response queue
hash_map = dict()
#Initializing sqs resource using boto3 library
sqs = boto3.resource('sqs', region_name="us-east-1")
req_queue = sqs.get_queue_by_name(QueueName='samkit-request-queue')
res_queue = sqs.get_queue_by_name(QueueName='samkit-response-queue')  

# This function fetches all the messages present in the response queue and adds it to the dictionary
# and deletes them from the response queue
def fetch_message():
    messages = res_queue.receive_messages(
        MessageAttributeNames=['All'],
        MaxNumberOfMessages=10,
        VisibilityTimeout=0,
        WaitTimeSeconds=10
    )
    for m in messages:
        hash_map[m.body.split(",")[0]]=m.body.split(",")[1]
        m.delete()

app = Flask(__name__)
@app.route("/", methods=['POST'])
def process_image():
    file = request.files["myfile"]
    status=None
    try:
        #reads the file contents in bytes
        file_bytes=file.read()
        #converts the bytes into hexadecimal string
        file_hex_str = file_bytes.hex()
        #sending file_hex_str along with the filename into the SQS
        req_queue.send_message(MessageBody=file_hex_str+","+file.filename)
        
        #We are defining the while loop which runs 30 times each loop having a sleep of 1 second
        #We are running the loop until we get the desired response in the hashmap 
        i=1
        while i<600:
            fetch_message()
            if file.filename in hash_map:
                status = hash_map[file.filename]
                del hash_map[file.filename]
                return status
            i+=1
            time.sleep(1)
    except Exception as e:
        status = "Error! = " + str(e)
    return status

if __name__ == "__main__":
    app.run(port=8000)
