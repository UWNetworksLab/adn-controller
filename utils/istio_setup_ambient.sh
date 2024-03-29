
#!/bin/bash

set -ex

curl -k -L https://istio.io/downloadIstio | sh -
pushd istio-*
sudo cp bin/istioctl /usr/local/bin
kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
  { kubectl kustomize "github.com/kubernetes-sigs/gateway-api/config/crd/experimental?ref=v1.0.0" | kubectl apply -f -; }
istioctl install --set profile=ambient --set "components.ingressGateways[0].enabled=true" --set "components.ingressGateways[0].name=istio-ingressgateway" --skip-confirmation
popd

set +ex