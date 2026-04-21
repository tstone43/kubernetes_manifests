# had issues with Traefik pod starting after deploying Multus and references on filesystem to binaries got messed up
# had to copy binaries from official Git repos for CNI and Flannel into /var/lib/rancher/k3s/data/cni/ on K3S hosts
curl -L -o cni.tgz https://github.com/containernetworking/plugins/releases/download/v1.5.0/cni-plugins-linux-amd64-v1.5.0.tgz
sudo tar -xvf cni.tgz -C /var/lib/rancher/k3s/data/cni/
curl -L -o flannel.tgz https://github.com/flannel-io/cni-plugin/releases/download/v1.9.0-flannel1/cni-plugin-flannel-linux-amd64-v1.9.0.tgz
sudo tar -xvf flannel.tgz -C flannel/
cd flannel
sudo cp flannel-amd64 /var/lib/rancher/k3s/data/cni/flannel
# after copying these files into /var/lib/rancher/k3s/data/cni/ ensure the only symlink that exists is for cni