import pulumi
from pulumi_aws import ec2, get_availability_zones, rds, elasticache

config = pulumi.Config();
environment = config.require('environment');
cidrblock = config.require('cidrblock');
availability_zones = (config.require_object('availability_zones')).get("id");
private_subnet = config.require_object('private-subnet');
public_subnet = config.require_object('public-subnet');
private_subnet_cidr = private_subnet.get("cidr")
public_subnet_cidr = public_subnet.get("cidr")

vpc = ec2.Vpc(
    f'{environment}',
    cidr_block=cidrblock,
    instance_tenancy='default',
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        'Name': f'{environment}',
    },
)

igw = ec2.InternetGateway(
    f'{environment}',
    vpc_id=vpc.id,
    tags={
        'Name': f'{environment}',
    },
)

public_route_table = ec2.RouteTable(
    f'{environment}-route-public',
    vpc_id=vpc.id,
    routes=[ec2.RouteTableRouteArgs(
        cidr_block='0.0.0.0/0',
        gateway_id=igw.id,
    )],
    tags={
        'Name': f'{environment}-public',
    },
)

#Creating subnets

subnet_ids = []
i=1

#Public Subnets

for cidr in public_subnet_cidr:
    vpc_public_subnet = ec2.Subnet(
        f'{environment}-public-{i}',
        assign_ipv6_address_on_creation=False,
        vpc_id=vpc.id,
        map_public_ip_on_launch=True,
        cidr_block=public_subnet_cidr[i-1],
        availability_zone=availability_zones[i-1],
        tags={
            'Name': f'{environment}-pub{i}',
            'kubernetes.io/role/elb': '1',
        },
    )
    ec2.RouteTableAssociation(
        f'{environment}-pub{i}',
        route_table_id=public_route_table.id,
        subnet_id=vpc_public_subnet.id,
    )
    subnet_ids.append(vpc_public_subnet.id)
    i=i+1

#Private Subnet 

nat_eip = ec2.Eip(f'{environment}',
    vpc=True,
    tags={
        'Name':f'{environment}',
    },
    )

ngw = ec2.NatGateway(f'{environment}',
    allocation_id=nat_eip.id,
    subnet_id=subnet_ids[0],
    tags={
        'Name': f'{environment}',
    },
    )

private_route_table = ec2.RouteTable(
    f'{environment}-route-private',
    vpc_id=vpc.id,
    routes=[ec2.RouteTableRouteArgs(
        cidr_block='0.0.0.0/0',
        gateway_id=ngw.id,
    )],
    tags={
        'Name': f'{environment}-private',
    },
)

#Subnet identifiers

i=1

for cidr in private_subnet_cidr:
    vpc_private_subnet = ec2.Subnet(
        f'{environment}-private-{i}',
        assign_ipv6_address_on_creation=False,
        vpc_id=vpc.id,
        cidr_block=private_subnet_cidr[i-1],
        availability_zone=availability_zones[i-1],
        tags={
            'Name': f'{environment}-priv{i}',
            'kubernetes.io/role/internal-elb': '1'
        },
    )
    ec2.RouteTableAssociation(
        f'{environment}-priv{i}',
        route_table_id=private_route_table.id,
        subnet_id=vpc_private_subnet.id,
    )
    subnet_ids.append(vpc_private_subnet.id)
    i=i+1

## Security Group

eks_security_group = ec2.SecurityGroup(
    f'{environment}-eks-sg',
    vpc_id=vpc.id,
    description='Allow all HTTP(s) traffic to EKS Cluster',
    tags={
        'Name': f'{environment}-eks-sg',
    },
    ingress=[
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=['0.0.0.0/0'],
            from_port=443,
            to_port=443,
            protocol='tcp',
            description='Allow pods to communicate with the cluster API Server.'
        ),
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=['0.0.0.0/0'],
            from_port=80,
            to_port=80,
            protocol='tcp',
            description='Allow internet access to pods'
        ),
    ],
)

node_security_group = ec2.SecurityGroup(
    f'{environment}-wng1-sg',
    vpc_id=vpc.id,
    description='Allow SSH access to the worker nodes',
    tags={
        'Name': f'{environment}-wng1-sg',
    }
)

