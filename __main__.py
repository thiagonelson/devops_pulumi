# aws configure
# pulumi config set aws:region us-west-2
# ssh -i cocus_keys ec2-user@54.245.183.214


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 09:34:46 2022

@author: thiago
"""
import pulumi
from pulumi import export
import pulumi_aws as aws


tipo_instancia = "t3.micro"

vpc = aws.ec2.Vpc(
 	"ec2-vpc",
 	cidr_block="172.16.0.0/23"
)

public_subnet = aws.ec2.Subnet(
 	"ec2-public-subnet",
 	cidr_block="172.16.0.0/24",
 	tags={
		"Name": "ec2-public"
 	},
 	vpc_id=vpc.id
)


private_subnet = aws.ec2.Subnet(
 	"ec2-private-subnet",
 	cidr_block="172.16.1.0/24",
 	tags={
		"Name": "ec2-private"
 	},
 	vpc_id=vpc.id
)


igw = aws.ec2.InternetGateway(
	"ec2-igw",
	vpc_id=vpc.id,
)

route_table = aws.ec2.RouteTable(
	"ec2-route-table",
	vpc_id=vpc.id,
	routes=[
		{
			"cidr_block": "0.0.0.0/0",
			"gateway_id": igw.id
		}
	]
)

rt_assoc = aws.ec2.RouteTableAssociation(
	"ec2-rta",
	route_table_id=route_table.id,
	subnet_id=public_subnet.id
)


eip = aws.ec2.Eip("eip-name",
    vpc=True)

natgateway = aws.ec2.NatGateway("ec2-igw-private",
    allocation_id=eip.id,
    subnet_id=public_subnet.id,
    opts=pulumi.ResourceOptions(depends_on=[igw])
    )


route_table_private = aws.ec2.RouteTable(
	"ec2-route-table-private",
	vpc_id=vpc.id,
	routes=[
		{
			"cidr_block": "0.0.0.0/0",
			"gateway_id": natgateway.id
		}
	]
)


rt_assoc_private = aws.ec2.RouteTableAssociation(
	"ec2-rta-private",
	route_table_id=route_table.id,
	subnet_id=private_subnet.id
)

sg_public = aws.ec2.SecurityGroup(
	"ec2-public-sg",
	description="Allow traffic to EC2 instance",
	ingress=[{
		"protocol": "tcp",
		"from_port": 80,
		"to_port": 80,
		"cidr_blocks": ["0.0.0.0/0"],
	},
        {
    		"protocol": "icmp",
    		"from_port": -1,
    		"to_port": -1,
    		"cidr_blocks": ["0.0.0.0/0"],
    	},
        {
    		"protocol": "tcp",
    		"from_port": 22,
    		"to_port": 22,
    		"cidr_blocks": ["0.0.0.0/0"],
    	}
        ],
    vpc_id=vpc.id,
)


sg_private = aws.ec2.SecurityGroup(
	"ec2-private-sg",
	description="Allow private traffic to EC2 instance",
	ingress=[{
		"protocol": "tcp",
		"from_port": 3110,
		"to_port": 3110,
		# "cidr_blocks": ["172.16.0.0/24"],
        "cidr_blocks": ["0.0.0.0/0"],
	},
        {
    		"protocol": "icmp",
    		"from_port": -1,
    		"to_port": -1,
    		"cidr_blocks": ["0.0.0.0/0"],
    	},
        {
    		"protocol": "tcp",
    		"from_port": 22,
    		"to_port": 22,
    		#"cidr_blocks": ["172.16.0.0/24"],
            "cidr_blocks": ["0.0.0.0/0"],
    	}
        ],
    vpc_id=vpc.id,
)



ami = aws.ec2.get_ami(
	most_recent="true",
	owners=["amazon"],
	filters=[{"name": "name", "values": ["amzn-ami-hvm-*"]}]
)



keypair = aws.ec2.KeyPair("cocus", public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCfH1V1EBPy8sipkTdmDTX3YbWb/x7z3uiUvRLLnEyQOhlx8OVxdAw95h0ZP+gXWWJEjFBsPazyS7yE2PkaxyxWOgr6HIBdzSLG8ToSptxKByKI+veZyARyX9qXO4olOjORoEilVFtU4Og+D70cllX8jjcBN2UCexwXGrO8ZmaVhukmAjSbbi97UbTTdO9Km9iUGrFP687ikSWD8PoXPEHox0Xf6fGircKaOQSvnOcLT0os6HVDKdZTdNNJwsUS9ZnD7hz+yI9Q/bKRu/aimeDlEtGvwFpVvhgxyxZx3Xp+9CRmDHK2XFcKB3FvtdPhcX7LUeq420YY+bi9qr4crxU/kDx33rVc2qSa+1MDUzYeotx8ursolz1LkYWssjlV6DtJBl3FSjdTR8646VJdvP3xIjehFy6VjNSO5C7j+J/dKw0zqyFliCcWgzl3SE6Ke6CYLpZlWb5i6BDalDK+uixrtvw/5/DwbmgybyCnwOPJ87XLf5DrldwCUiwP8yIXSH8= root@cloudsim")

user_data = """
#!/bin/bash
echo "Hello, world!" > index.html
nohup python -m SimpleHTTPServer 80 &
"""



ec2_webserver = aws.ec2.Instance(
	"webserver",
	instance_type=tipo_instancia,
#	vpc_security_group_ids=[sg_public.id, sg_private.id],
	vpc_security_group_ids=[sg_public.id],
	ami=ami.id,
	user_data=user_data,
    subnet_id=public_subnet.id,
    associate_public_ip_address=True,
    key_name=keypair.key_name,
)


ec2_database = aws.ec2.Instance(
	"database",
	instance_type=tipo_instancia,
	vpc_security_group_ids=[sg_private.id],
	ami=ami.id,
	user_data="",
    subnet_id=private_subnet.id,
    associate_public_ip_address=False,
    key_name=keypair.key_name,
)



export("ec2-public-ip", ec2_webserver.public_ip)
