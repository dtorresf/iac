"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import eks
import networking


config = pulumi.Config();
environment = config.require('environment');
instance_size = config.require('instance-size');

eks_cluster = eks.Cluster(
    f'tenon-{environment}',
    role_arn='arn:aws:iam::870743714739:role/eksServiceRole',
    tags={
        'Name': f'tenon-{environment}',
    },
    vpc_config=eks.ClusterVpcConfigArgs(
        public_access_cidrs=['0.0.0.0/0'],
        security_group_ids=[networking.eks_security_group.id],
        subnet_ids=networking.subnet_ids,
    ),
)

eks_node_group = eks.NodeGroup(
    f'tenon-{environment}-wng1',
    cluster_name=eks_cluster.name, 
    node_group_name=f'tenon-{environment}-wng1',
    node_role_arn='arn:aws:iam::870743714739:role/NodeInstanceRole',
    subnet_ids=networking.subnet_ids,
    instance_types=[instance_size],
    remote_access=eks.NodeGroupRemoteAccessArgs(
        ec2_ssh_key='tenon-ecs-key',
    ),
    tags={
        'Name': f'tenon-{environment}-wng1',
    },
    scaling_config=eks.NodeGroupScalingConfigArgs(
        desired_size=3,
        max_size=6,
        min_size=2,
    ),
)