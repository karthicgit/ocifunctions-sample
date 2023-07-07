import oci
import gzip
import re
import json
import io

#import logging

def decompress(bucket_name,namespace,object_storage_client,**kwargs):
    bucket_name = bucket_name
    namespace = namespace
    prefix = kwargs.get("prefix")
    #list objects in object storage
    try:
        list_objects = object_storage_client.list_objects(namespace, bucket_name,prefix=prefix).data.objects
    except oci.exceptions.ServiceError as oci_exception:
        print(oci_exception)
    #loop through objects which ends with .gz and decompress them
    for i in list_objects:
        gzip_file = i.name
        if gzip_file.endswith(".gz"):
            try:
                gzip_object = object_storage_client.get_object(namespace,bucket_name,gzip_file).data.content
                data = gzip.decompress(gzip_object)
                object_storage_client.put_object(
                    namespace_name=namespace,
                    bucket_name=bucket_name,
                    object_name=re.sub(r'\.gz$', '', gzip_file),
                    put_object_body=data)
            except oci.exceptions.ServiceError as oci_exception:
                print(oci_exception)
            except Exception as e:
                print(e)
        else:
            continue


# def delete_object(bucket_name, object_name,namespace,object_storage_client):
#     try:
#         object_storage_client.delete_object(
#         namespace_name=namespace,
#         bucket_name=bucket_name,
#         object_name=object_name)
#     except Exception as e:
#         print(e)

def handler(ctx, data: io.BytesIO=None):

    try:
        cfg = ctx.Config()
        object_prefix = None
        if cfg.get('prefix') is not None:
            object_prefix = cfg['prefix']
          
        signer = oci.auth.signers.get_resource_principals_signer()
        object_storage_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

        body = json.loads(data.getvalue())

        bucket_name = body['data']['additionalDetails']['bucketName']
        namespace = body['data']['additionalDetails']['namespace']
        decompress(bucket_name, namespace,object_storage_client,prefix=object_prefix)

    except ValueError:
        print("Invalid JSON")
    except oci.exceptions.ServiceError as oci_exception:
        print(oci_exception)
    except Exception as e:
        print(e)
