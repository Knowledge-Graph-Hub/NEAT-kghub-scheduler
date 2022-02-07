# check.py

"""Utility for checking KG-Hub projects for 
updated NEAT config YAMLs.
If one is found, it is retrieved
and assigned a unique identifier based
on its bucket LastModified, 
so it won't be retrieved
again unless it is modified.
"""

import boto3
import click
from datetime import datetime

@click.command()
@click.option("--bucket",
               required=True,
               nargs=1,
               help="""The name of an AWS S3 bucket.""")
def run(bucket: str):
    new_neats = check_bucket(bucket)

def check_bucket(bucket: str):
    """
    Checks bucket for all NEAT configs.
    :param bucket: name of the bucket
    :return: list of tuples of 
                (string key for NEAT config,
                LastModified string)

    """

    all_neat_keys = []

    client = boto3.client('s3')

    pager = client.get_paginator("list_objects_v2")

    print(f"Searching {bucket}...")
    for page in pager.paginate(Bucket=bucket):
        remote_contents = page['Contents']
        for key in remote_contents:
            if (((key['Key']).split("/"))[-1]).lower() in ['neat.yaml', 'neat.yml']: 
                last_modified_string = (key['LastModified']).strftime("%m-%d-%Y-%H-%M-%S")
                all_neat_keys.append((key['Key'],last_modified_string))

    print(f"Found {len(all_neat_keys)} NEAT configs.")
    for key in all_neat_keys:
        print(key)

    return all_neat_keys

if __name__ == '__main__':
  run()