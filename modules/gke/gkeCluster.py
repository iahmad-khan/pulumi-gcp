import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import * as k8s from "@pulumi/kubernetes";

interface GKEClusterArgs {
    name: string;
    project: string;
    location: string;
    nodeVersion?: string;
    numNodes?: number;
    nodeMachineType?: string;
    maintenanceWindow?: {
        dayOfWeek: string;
        time: string;
    };
    privateEndpoint?: boolean;
    enableAutoscaling?: boolean;
    minNodes?: number;
    maxNodes?: number;
    additionalNodePools?: {
        name: string;
        machineType: string;
        numNodes: number;
    }[];
}

export class GKECluster extends pulumi.ComponentResource {
    constructor(name: string, args: GKEClusterArgs, opts?: pulumi.ComponentResourceOptions) {
        super("custom:gcp:GKECluster", name, {}, opts);

        // Create GKE cluster
        const cluster = new gcp.container.Cluster(name, {
            name: args.name,
            location: args.location,
            initialNodeCount: args.numNodes || 1,
            nodeVersion: args.nodeVersion || "latest",
            nodeConfig: {
                machineType: args.nodeMachineType || "n1-standard-1",
                oauthScopes: [
                    "https://www.googleapis.com/auth/compute",
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring",
                ],
                enableAutorepair: true,
                enableAutoupgrade: true,
                minCpuPlatform: "Automatic",
            },
            removeDefaultNodePool: true, // We'll add node pools separately
        }, { parent: this });

        // Optional: Configure maintenance window
        if (args.maintenanceWindow) {
            const maintenancePolicy = new gcp.container.ClusterMaintenancePolicy(name, {
                location: cluster.location,
                cluster: cluster.name,
                dailyMaintenanceWindow: {
                    startTime: args.maintenanceWindow.time,
                },
            }, { parent: this });
        }

        // Optional: Enable private endpoint
        if (args.privateEndpoint) {
            const privateEndpoint = new gcp.container.ClusterPrivateClusterConfig(name, {
                enablePrivateEndpoint: true,
                masterIpv4CidrBlock: "172.16.0.0/28",
            }, { parent: this });
        }

        // Optional: Configure autoscaling
        if (args.enableAutoscaling) {
            const autoscaling = new gcp.container.ClusterAutoscaling(name, {
                cluster: cluster.name,
                autoscalingPolicy: {
                    maxNodeCount: args.maxNodes || 5,
                    minNodeCount: args.minNodes || 1,
                },
            }, { parent: this });
        }

        // Optional: Add additional node pools
        if (args.additionalNodePools) {
            for (const npArgs of args.additionalNodePools) {
                const nodePool = new gcp.container.NodePool(name + "-" + npArgs.name, {
                    cluster: cluster.name,
                    initialNodeCount: npArgs.numNodes,
                    nodeConfig: {
                        machineType: npArgs.machineType,
                    },
                }, { parent: this });
            }
        }

        // Export cluster details
        this.clusterName = cluster.name;
        this.kubeconfig = cluster.kubeconfig;
    }

    public readonly clusterName: pulumi.Output<string>;
    public readonly kubeconfig: pulumi.Output<any>;
}
