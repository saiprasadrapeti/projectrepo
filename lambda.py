import boto3
import json
import base64
import time
AMI = 'ami-0629230e074c580f2'
INSTANCE_TYPE = 't2.micro'
REGION = 'us-east-2' 
#user_Data = 
#user_Data_bytes = user_Data.encode("ascii")
#base64_bytes = base64.b64encode(user_Data_bytes)
#base64_string = base64_bytes.decode("ascii") 

lb = boto3.client('elbv2', region_name=REGION)
asg = boto3.client('autoscaling', region_name=REGION) 
ec2 = boto3.client('ec2', region_name=REGION)
rds = boto3.client('rds', region_name=REGION)
def lambda_handler(event, context):
     
     key_pair = ec2.create_key_pair(
          KeyName= 'saiprasad',
          KeyType='rsa')
     print ("key pair created.")
     
     security_group = ec2.create_security_group(
          Description= 'allow all trafics',
          GroupName= 'launch-wizard-2',
          VpcId= 'vpc-01bd5d3657235916f')
     print ("security group created.")
     inbound_rule = ec2.authorize_security_group_ingress(
          GroupId= security_group['GroupId'],
          CidrIp='0.0.0.0/0',
          IpProtocol='all', 
          FromPort=1, 
          ToPort=255)
     print ("inbound_rule added.")    
     
     db_instance = rds.create_db_instance(
          DBName= 'carrental',
          DBInstanceIdentifier='myrds',
          AllocatedStorage=10,
          DBInstanceClass='db.t2.micro',
          Engine='mysql',
          MasterUsername='admin',
          MasterUserPassword='saiprasadrapeti',
          VpcSecurityGroupIds= [security_group['GroupId']],
          EngineVersion= '5.7',
          PubliclyAccessible=True)
     print ("RDS created.") 
     print ("wait for 3 minutes")
     time.sleep(400)
     db_instance_disc = rds.describe_db_instances( DBInstanceIdentifier='myrds')
     print ("db_instance discribed.")
     print (db_instance_disc['DBInstances'][0]['Endpoint']['Address'])
     end_point = db_instance_disc['DBInstances'][0]['Endpoint']['Address']
       
     load_balancer = lb.create_load_balancer(
          Name='sai-nlb',
          Subnets=['subnet-08ac816e92386a609','subnet-0b4ab3622bacde8fe'],
          Type='network',
          IpAddressType='ipv4')
     LoadBalancer_Arn = load_balancer['LoadBalancers'][0]['LoadBalancerArn']
     print (LoadBalancer_Arn)
     print ("load balancer created")
     
     target_group = lb.create_target_group(
          Name='sainbl',
          Protocol='TCP',
          Port=80,
          VpcId='vpc-01bd5d3657235916f',
          TargetType='instance')
     print ("Target group created.")
     
     listener = lb.create_listener(
          LoadBalancerArn= load_balancer['LoadBalancers'][0]['LoadBalancerArn'],
          Protocol='TCP',
          Port=80,
          DefaultActions=[{'Type': 'forward', 'TargetGroupArn': target_group['TargetGroups'][0]['TargetGroupArn']}])
     print ("Listeners created")
     user_Data = f'''#!/bin/bash
sudo apt-get update -y
sudo apt-get upgrade -y
sudo wget https://www.apachefriends.org/xampp-files/8.1.2/xampp-linux-x64-8.1.2-0-installer.run
sudo chmod 755 xampp-linux-x64-8.1.2-0-installer.run
sudo ./xampp-linux-x64-8.1.2-0-installer.run
Y
Y
ENTER
Y
sudo apt install net-tools
sudo /opt/lampp/lampp start
sudo rm -rf /opt/lampp/htdocs/*
sudo chmod 777 /opt/lampp/htdocs
sudo git clone https://github.com/saiprasadrapeti/projectrepo.git
sudo cp -r final_project/sourcecode/zms/* /opt/lampp/htdocs
sudo chmod 777 /opt/lampp/htdocs/includes/dbconnection.php
sudo sed -i.bak 's/localhost/{end_point}/g' /opt/lampp/htdocs/includes/dbconnection.php
sudo sed -i.bak 's/localhost/{end_point}/g' /opt/lampp/htdocs/admin/includes/dbconnection.php
sudo chmod 777 /opt/lampp/etc/extra/httpd-xampp.conf
sudo sed -i.bak 's/local/all granted/g' /opt/lampp/etc/extra/httpd-xampp.conf
sudo chmod 755 /opt/lampp/etc/extra/httpd-xampp.conf
sudo /opt/lampp/lampp restart
sudo chmod 777 /opt/lampp/phpmyadmin/config.inc.php
sudo echo '$cfg["Servers"][$i]["verbose"] = "Amazon RDS";' >> /opt/lampp/phpmyadmin/config.inc.php
sudo echo '$cfg["Servers"][$i]["host"] = "{end_point}";' >> /opt/lampp/phpmyadmin/config.inc.php
sudo echo '$cfg["Servers"][$i]["user"] = "admin";' >> /opt/lampp/phpmyadmin/config.inc.php
sudo echo '$cfg["Servers"][$i]["password"] = "saiprasadrapeti";' >> /opt/lampp/phpmyadmin/config.inc.php
sudo echo '$cfg["Servers"][$i]["port"] = "3306";' >> /opt/lampp/phpmyadmin/config.inc.php
sudo echo '$cfg["Servers"][$i]["auth_type"] = "config";' >> /opt/lampp/phpmyadmin/config.inc.php
sudo echo '$cfg["Servers"][$i]["AllowNoPassword"] = true;' >> /opt/lampp/phpmyadmin/config.inc.php
sudo chmod 400 /opt/lampp/phpmyadmin/config.inc.php
sudo /opt/lampp/lampp restart
sudo apt install mysql-client-core-8.0
sudo mysql -h {end_point} -u admin --password=saiprasadrapeti carrental < /final_project/sourcecode/SQL\ File/carrental.sql
'''
     user_Data_bytes = user_Data.encode("ascii")
     base64_bytes = base64.b64encode(user_Data_bytes)
     base64_string = base64_bytes.decode("ascii")
     launch_template = ec2.create_launch_template(
          LaunchTemplateName='my-lt',
          LaunchTemplateData={
               'ImageId': AMI,
               'InstanceType': INSTANCE_TYPE,
               'KeyName': key_pair['KeyName'],
               'UserData': base64_string,
               'SecurityGroupIds': [security_group['GroupId']],
               'IamInstanceProfile': {'Name': 'demo-Role'}})
     print (launch_template)
     print ("Launch template created.")

     autoscaling_group = asg.create_auto_scaling_group(
          AutoScalingGroupName='my-asg1',
          LaunchTemplate={'LaunchTemplateName': 'my-lt'},
          MinSize=1,
          MaxSize=2,
          DesiredCapacity=1,
          AvailabilityZones=['us-east-2c'],
          TargetGroupARNs=[target_group['TargetGroups'][0]['TargetGroupArn']])
     print ("First asg Created.")
     
     autoscaling_group = asg.create_auto_scaling_group(
          AutoScalingGroupName='my-asg2',
          LaunchTemplate={'LaunchTemplateName': 'my-lt'},
          MinSize=1,
          MaxSize=2,
          DesiredCapacity=1,
          AvailabilityZones=['us-east-2b'],
          TargetGroupARNs=[target_group['TargetGroups'][0]['TargetGroupArn']])
     print ("Second asg Created.")

     scaling_policy = asg.put_scaling_policy(
          AutoScalingGroupName= 'my-asg1',
          PolicyName= 'target-tracking-scaling-policy',
          PolicyType='TargetTrackingScaling',
           TargetTrackingConfiguration={
               'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'ASGAverageCPUUtilization'
                    },
               'TargetValue': 10.0,
          },
     )
     print ("Scaling policy attached to first ASG.")
     scaling_policy = asg.put_scaling_policy(
          AutoScalingGroupName= 'my-asg2',
          PolicyName= 'target-tracking-scaling-policy',
          PolicyType='TargetTrackingScaling',
           TargetTrackingConfiguration={
               'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'ASGAverageCPUUtilization'
                    },
               'TargetValue': 10.0,
           },
     )
     print ("Scaling policy attached to Second ASG.")

     return (db_instance_disc['DBInstances'][0]['Endpoint']['Address'])
