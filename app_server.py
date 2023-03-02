import boto3
import time
from subprocess import run
import os

def getSession():
    session = boto3.Session(
        region_name='us-east-1'
    )
    return session

session = getSession()
s3 = session.client('s3')
sqs = session.resource('sqs')
req_queue = sqs.get_queue_by_name(QueueName='samkit-request-queue')
res_queue = sqs.get_queue_by_name(QueueName='samkit-response-queue')  

while(1):
    try:
        messages = req_queue.receive_messages(
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )
        if len(messages)==0: 
            time.sleep(1)
            continue
        token = messages[0].body.split(",")
        message_str, image_name = token[0], token[1]
        arr_bytes = bytes.fromhex(message_str)
        os.chdir('/home/ubuntu')
        with open(image_name,"wb") as f:
            f.write(arr_bytes)
        cmd = "python3 image_classification.py {}".format(image_name)
        data = run(cmd, capture_output=True, shell=True)
        output_binary = data.stdout.splitlines()
        errors = data.stderr.splitlines()
        output_text = output_binary[0].decode('utf-8')
        s3.upload_file(image_name,'samkit-input-bucket',image_name)
        s3.put_object(Body=output_text,Bucket='samkit-output-bucket',Key=image_name.split('.')[0])
        res_queue.send_message(MessageBody=output_text)
        status = "Image has been succesfully sent to S3."
        messages[0].delete()
        os.remove(image_name)
    except Exception as e:
        status = "Error! = " + str(e)
    print(status)
