import boto3

# reads the complete contents of an  object from an s3 bucket and returns it as a UTF-8 string
def read_file_from_s3(bucket_name, file_key):
    result = None
    s3 = boto3.client('s3')
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        result = response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error reading file: {e}")

    return result
