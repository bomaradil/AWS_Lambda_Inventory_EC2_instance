#inventory EC2 instance and save the data into DynamoDB Table and a .csv file in s3 bucket
#I will be using the resource methode to call for the AWS services EC2, DynamoDB and S3

import boto3

#the keys of the metadata we want to get from the instances.
#the keys will be used to create the headers for the csv file and the items inthe DynamoDb table
keys= ["instance_id", "vpc_id", "subnet_id", "security_groups", "instance_type", 
           "public_ip_addressd", "image_id", "key_name", "state", "tags"]

def Get_Ec2_Instance_Info(keys=keys):
    '''
    collect the data from all the ec2 instances, 
    the fucntion will return a list of dictionary with the keys and the data collected.
    the EC2 resource method is used to call the services.
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#service-resource
    '''
    table_data = list()
    #call the ec2 resource methode
    ec2 = boto3.resource('ec2')   
    for instance in ec2.instances.all():
        #create a dictionnary for every instance using keys and the metada collected
        data = dict(zip(keys, [instance.id, instance.vpc_id, instance.subnet_id, instance.security_groups,  
               instance.instance_type, instance.public_ip_address, instance.image.id, 
               instance.key_name, instance.state['Name'], instance.tags,] 
               ))
        #append the dictionary to a list wish will be returned
        table_data.append(data) 
    return table_data

def Inventory_Ec2_Instance_RDS(table_name='Inventory_Ec2_Instances', table_data=Get_Ec2_Instance_Info()):
    '''
    Save the data collected with the function Get_Ec2_Instance_Info to a DynamoDB table that I created
    the items in the DynamoDB table need to be the same as the element of keys
    the DynamoDB resource method is used to call the services
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#service-resource
    '''
    #import logging
    #call the DynamoDB resource method 
    dynamodb = boto3.resource('dynamodb')
    #call the inventory table
    table = dynamodb.Table(table_name)
    with table.batch_writer() as writer:
        #write data into our table
        for item in table_data:
            writer.put_item(Item=item)
    print('done')
        
def Inventory_Ec2_Instance_Xls_S3(keys=keys, bucket_name='ec2-inventory-boa', table_data=Get_Ec2_Instance_Info()):
    '''
    Save the data collected with the function Get_Ec2_Instance_Info into a csv file wish will be 
    saved to a s3 bucket
    the s3 resource method is used to call the services
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#service-resource
    '''
    #call the datetime and csv library
    import datetime, csv
    #get the date 
    date = datetime.datetime.now()
    #call teh s3 resouce methode
    s3 = boto3.resource('s3')
    # use the format inventory-year-month-day to name the csv file. 
    filename = ('inventory-{}-{}-{}.csv'.format(date.year, date.month, date.day))
    #open the file with write mode and created it if it's doesnt existe
    with open('/tmp/'+filename, 'w+') as inventory:
        #write into the file using the DicWriter function the headers will be the keys
        writer = csv.DictWriter(inventory, fieldnames=keys)
        #write the headers
        writer.writeheader()
        for data in table_data:
            #write the values of the data
            writer.writerow(data)
    #upload the csv file into the s3 bucket and make it public read 
    s3.Object(bucket_name, filename).upload_file('/tmp/'+filename, ExtraArgs={'ACL':'public-read'})
    print('done')

def lambda_handler(event, context):
    Inventory_Ec2_Instance_RDS()
    Inventory_Ec2_Instance_Xls_S3()
