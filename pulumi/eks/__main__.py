"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import eks
import networking


config = pulumi.Config();
environment = config.require('environment');
instance_size = config.require('instance-size');
eks_service_role = config.require('eks-service-role');
node_instance_role = config.require('node-instance-role');

#Create EKS required Roles

eks_cluster = eks.Cluster(
    f'{environment}',
    role_arn=eks_service_role,
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
    instance_types=[instance_size],
    remote_access=eks.NodeGroupRemoteAccessArgs(
        ec2_ssh_key='ecs-key',
    ),
    tags={
        'Name': f'{environment}-wng1',
    },
    scaling_config=eks.NodeGroupScalingConfigArgs(
        desired_size=3,
        max_size=6,
        min_size=2,
    ),
)