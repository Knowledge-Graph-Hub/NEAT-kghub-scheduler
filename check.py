# check.py

"""Utility for checking KG-Hub projects for 
updated NEAT config YAMLs.
If one is found, it is retrieved
and assigned a unique identifier based
on its bucket LastModified.
If:
* the config is in a build directory
* and there is not yet a graph_ml directory in that build dir
then the run continues.
"""

import os
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
    if len(new_neats) > 0:
        retrieve(bucket, new_neats)
    else:
        print("Found no new NEAT configs. Nothing to do.")

def check_bucket(bucket: str):
    """
    Checks bucket for all NEAT configs.
    Also checks if they match the following criteria:
        * the config is in a build directory
        * there is not yet a graph_ml directory in that build dir
    :param bucket: name of the bucket
    :return: list of dicts of 
                "Key":string key for NEAT config,
                "LastModified":LastModified string,
                "To_Run":bool
    """

    all_keys = []
    all_builds_with_graph_ml = []
    all_neats = []

    client = boto3.client('s3')

    pager = client.get_paginator("list_objects_v2")

    print(f"Searching {bucket}...")
    for page in pager.paginate(Bucket=bucket):
        remote_contents = page['Contents']
        for key in remote_contents:
            all_keys.append(key['Key'])
            try:
                if "/graph_ml" in key['Key']:
                    buildname = (key['Key'].split("/"))[-3]
                    all_builds_with_graph_ml.append(buildname)
            except IndexError:
                pass
            if (((key['Key']).split("/"))[-1]).lower() in ['neat.yaml', 'neat.yml']: 
                last_modified_string = (key['LastModified']).strftime("%m-%d-%Y-%H-%M-%S")
                all_neats.append({"Key":key['Key'],
                                    "LastModified":last_modified_string,
                                    "To_Run":False})

    # Check if there's a corresponding graph_ml directory already
    # where the directory is a build (i.e., named in our expected format)
    for key in all_neats:
        keyname = key["Key"]
        buildname = (keyname.split("/"))[-2]
        if not buildname.isnumeric() or len(buildname) > 8:
            print(f"Config found in {keyname}, but this does not look like a build directory.")
            continue
        if buildname in all_builds_with_graph_ml:
            print(f"Config found in {keyname} already has graph_ml present.")
            continue
        else:
            print(f"Config for {keyname} has no results - will try to run.")
            key["To_Run"] = True

    print(f"Found {len(all_neats)} NEAT configs.")
    for key in all_neats:
        keyname = key["Key"]
        if key["To_Run"]:
            print(f"{keyname} will be run.")
        else:
            print(f"{keyname} will NOT be run.")

    return all_neats

def retrieve(bucket: str, neats: dict) -> None:
    """
    Downloads specific files from the remote bucket.
    :param bucket: name of the bucket
    :param neats: dict produced by check_bucket
    """

    client = boto3.client('s3')

    for neat in neats:
        if neat["To_Run"]:
            keyname = neat["Key"]
            outfilename = ((keyname.split("/"))[-1]).replace(".yaml", "-" + neat["LastModified"] + ".yaml")
            outfilepath = os.path.join("../",outfilename)
            print(f"Downloading {keyname} to {outfilepath}")
            client.download_file(bucket, keyname, outfilepath)

if __name__ == '__main__':
  run()