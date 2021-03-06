"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import eks
import networking


config = pulumi.Config();
environment = config.require('environment');
instance_size = config.require('instance-size');
eks_service_role = config.require('eks-service-role');
node_instance_role = config.require('node-instance-role');
node_pool_desired_size = config.require('pool-desired-size');
node_pool_min_size = config.require('pool-min-size');
node_pool_max_size = config.require('pool-max-size');
node_ssh_key = config.require('node-ssh-key')
eks_node_disk_size = config.require('eks-node-disk-size')
eks_version = config.require('eks-version')

#Create EKS required Roles

eks_cluster = eks.Cluster(
    f'{environment}',
    role_arn=eks_service_role,
    version=eks_version,
    tags={
        'Name': f'{environment}',
    },
    vpc_config=eks.ClusterVpcConfigArgs(
        public_access_cidrs=['0.0.0.0/0'],
        security_group_ids=[networking.eks_security_group.id],
        subnet_ids=networking.subnet_ids,
    ),
)

eks_node_group = eks.NodeGroup(
    f'{environment}-wng1',
    cluster_name=eks_cluster.name, 
    node_group_name=f'{environment}-wng1',
    node_role_arn=node_instance_role,
    subnet_ids=networking.subnet_ids,
    disk_size=int(eks_node_disk_size),
    instance_types=[instance_size],
    remote_access=eks.NodeGroupRemoteAccessArgs(
        ec2_ssh_key=node_ssh_key,
    ),
    tags={
        'Name': f'{environment}-wng1',
    },
    scaling_config=eks.NodeGroupScalingConfigArgs(
        desired_size=int(node_pool_desired_size),
        max_size=int(node_pool_max_size),
        min_size=int(node_pool_min_size),
    ),
)