import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import { GKECluster } from "./modules/gke/gkeCluster";

const config = new pulumi.Config();
const project = config.require("gcpProject");
const location = config.require("gcpLocation");

const myCluster = new GKECluster("my-cluster", {
    name: "my-cluster",
    project,
    location,
    numNodes: 3,
    nodeMachineType: "n1-standard-2",
    maintenanceWindow: {
        dayOfWeek: "Monday",
        time: "03:00",
    },
    privateEndpoint: true,
    enableAutoscaling: true,
    minNodes: 2,
    maxNodes: 5,
    additionalNodePools: [
        {
            name: "pool2",
            machineType: "n1-standard-4",
            numNodes: 2,
        },
    ],
});
