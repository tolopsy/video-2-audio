import pika, sys
from pika.adapters.blocking_connection import BlockingChannel
from pymongo import MongoClient
import gridfs
from conversion import to_audio
from utils import VIDEO_QUEUE

def main():
    client = MongoClient("host.minikube.internal", 27017)
    video_db = client.video
    audio_db = client.audio

    fs_video = gridfs.GridFS(video_db)
    fs_audio = gridfs.GridFS(audio_db)

    def callback(ch: BlockingChannel, method, properties, body):
        err = to_audio.start(body, fs_video, fs_audio, ch)
        if err:
            print(f"There has been an error: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq", heartbeat=0))
    channel = connection.channel()

    channel.basic_consume(queue=VIDEO_QUEUE, on_message_callback=callback)

    print("Waiting for messages. To exit, press CTRL+C")

    channel.start_consuming()


"""TODO: 
1. Printed errors to be properly logged
2. Handle exceptions around channel.start_consuming
"""


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            # cleanup, if any
            pass
