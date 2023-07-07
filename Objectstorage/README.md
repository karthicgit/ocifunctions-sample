Function to decompress gzip files in OCI object storage

You can pass **prefix** in the function configuration to decompress objects starting with that prefix
If prefix is not passed it will try to list all the gzip files and decompress. 

You can use Events to trigger the function when an object is created .Make sure the timeout and memory is set to maximum limit for large files so that it won't timeout.
If there are many files and it will take time to decompress and put the data back into objet storage you can use container instance to do this activity or locally with few modification.
