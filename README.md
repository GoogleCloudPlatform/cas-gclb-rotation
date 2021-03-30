# GCLB rotation tool for Certificate Authority Service

This is a sample solution that periodically checks the status of Google Cloud internal or external HTTP(S) load balancers and rotates their certificates (using a configured CA on [Certificate Authority Service](https://cloud.google.com/certificate-authority-service/docs)) when they reach a given percentage of their lifetime.

**Note: This solution is not an official product and is not supported by Google, but is a sample provided for your reference. Direct use of this code in production is discouraged, but you may fork, modify and run this code as needed (subject to the license).**

## Quickstart (for a local run)
### Prerequisites:
1. [Docker](https://docs.docker.com/engine/install/): used to package and run the code locally.
1. [gcloud](https://cloud.google.com/sdk/docs/install): used to bootstrap identity when running locally.
1. Unix-like shell: needed to run the included scripts. Tested with bash on macOS, but should also work on Linux and WSL.

### Steps
1. Update `app/config.yaml` with your rotation profiles (see [Config file](#config-file) for details).
1. Run `gcloud auth application-default login`.

     Make sure the account you use has the appropriate [permissions](#iam-roles).

1. Run `./run-local.sh` in one terminal to start the rotator server.
1. Run `./call-local.sh` in another terminal to actually initiate the rotation logic.

## Deploying to the Cloud
In addition to running locally, you can deploy this tool to the Cloud and run it on a schedule (e.g. every 6 hours) to keep your certificates up-to-date.

The simplest way to do this is to use the `publish.sh` script to deploy the rotation service to [Google Cloud Run](https://cloud.google.com/run), and use [Google Cloud Scheduler](https://cloud.google.com/scheduler) to define a recurring schedule for calling the rotation service.

You may also modify, package and deploy this tool to run on other platforms, such as VMs or Kubernetes pods.

## Config file
This tool uses a YAML config file (`app/config.yaml`) to discover the load balancers to manage, the certificate authorities to use, and what certificates should look like. It contains a list of *rotation profiles*, each of which describes a single certificate which must be maintained.

Each rotation profile consists of:
1. A load balancer instance whose certificates will be rotated.
1. A Certificate Authority (CA) that will issue new certificates.
1. The time duration (in days) for which the new certificates should be valid.
1. A threshold of each certificate's lifetime at which it is rotated.
     For example, if a certificate's lifetime is 30 days and its rotation threshold is `0.5`, it will be considered eligible for rotation when 15 days have passed since it was issued.

## IAM roles
The account used by the rotation server must have at least the following IAM role bindings:
- `roles/privateca.certificateRequester` on all configured Certificate Authorities.
- `roles/compute.loadBalancerAdmin` on the project containing the configured Load Balancers.

## Limitations

The following features are currently not supported:

- Multiple certificates for a single load balancer. Currently, this tool only looks at the first certificate and replaces that.
- Publicly-trusted certificates. To automate rotation of publicly-trusted certificates, see [Using Google-managed SSL certificates](https://cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs).

## Community contributions

If you would like to contribute to this project, start by checking the existing [issues](../../issues) and [pull requests](../../pulls) to see if someone else has already suggested a similar edit, idea or question. If you do not see a similar idea already listed, feel free to create one.
